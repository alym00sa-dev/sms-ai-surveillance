import json

import pytest
import requests

from src.adapters.base import AdapterRequest
from src.adapters.google import GoogleAdapter
from src.adapters.openai import OpenAIAdapter
from src.adapters.registry import ADAPTERS, build_adapter
from src.adapters.together import TogetherAdapter
from src.config import load_models
from src.schemas.model_output import MODEL_OUTPUT_JSON_SCHEMA

KEY = "SECRET-TEST-KEY-123"
MSGS = [{"role": "user", "content": "envelope"}, {"role": "assistant", "content": "bad"}, {"role": "user", "content": "fix it"}]
REQ = AdapterRequest("SYSTEM TEXT", MSGS, MODEL_OUTPUT_JSON_SCHEMA)


class Resp:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._b, self.headers = status, body if body is not None else {}, headers or {}
        self.text = json.dumps(self._b)

    def json(self):
        if self._b is None:
            raise ValueError("no json")
        return self._b


class NotJson(Resp):
    def json(self):
        raise ValueError("not json")


class Session:
    def __init__(self, *resps):
        self.resps, self.calls = list(resps), []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        r = self.resps.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def cfg(provider, **over):
    base = {"model": f"{provider}-model", "adapter": provider, "params": {"temperature": None, "max_tokens": 777}, "structured_output": "native_json_schema", "pricing": None}
    base.update(over)
    return base


# ------------------------------------------------------------------ OpenAI
OPENAI_OK = {"id": "resp_1", "model": "gpt-x", "status": "completed",
             "output": [{"type": "reasoning", "summary": []}, {"type": "message", "content": [{"type": "output_text", "text": '{"a": 1}'}]}],
             "usage": {"input_tokens": 1000, "output_tokens": 300, "input_tokens_details": {"cached_tokens": 400}, "output_tokens_details": {"reasoning_tokens": 200}}}


def test_openai_request_and_parse():
    s = Session(Resp(200, OPENAI_OK, {"x-request-id": "r1"}))
    ad = OpenAIAdapter("o", cfg("openai", params={"temperature": None, "max_tokens": 777, "reasoning_effort": "low"},
                                pricing={"input_per_mtok": 1.0, "output_per_mtok": 2.0, "cache_read_per_mtok": 0.5}), api_key=KEY, session=s)
    r = ad.complete(REQ)
    c = s.calls[0]
    assert c["url"] == "https://api.openai.com/v1/responses" and c["headers"]["Authorization"] == f"Bearer {KEY}"
    b = c["json"]
    assert b["instructions"] == "SYSTEM TEXT" and b["input"] == MSGS and b["max_output_tokens"] == 777 and b["store"] is False
    assert b["text"]["format"] == {"type": "json_schema", "name": "surveillance_turn", "strict": True, "schema": MODEL_OUTPUT_JSON_SCHEMA}
    assert "temperature" not in b and b["reasoning"] == {"effort": "low"}
    assert r.text == '{"a": 1}' and r.stop_reason == "end_turn" and r.request_id == "resp_1"
    assert r.usage == {"input_tokens": 600, "output_tokens": 300, "cache_read_input_tokens": 400, "cache_creation_input_tokens": 0, "reasoning_tokens": 200}
    assert r.cost_usd == pytest.approx(600 / 1e6 + 300 * 2 / 1e6 + 400 * 0.5 / 1e6)
    assert KEY not in json.dumps(r.request_params) and r.request_params["text"]["format"]["schema"] == "<MODEL_OUTPUT_JSON_SCHEMA>"
    assert r.structured_output_mode == "native_json_schema"


def test_openai_refusal_truncation_and_prompt_only():
    refusal = {**OPENAI_OK, "output": [{"type": "message", "content": [{"type": "refusal", "refusal": "no"}]}]}
    r = OpenAIAdapter("o", cfg("openai"), api_key=KEY, session=Session(Resp(200, refusal))).complete(REQ)
    assert r.text is None and r.stop_reason == "refusal"
    trunc = {**OPENAI_OK, "status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"}}
    assert OpenAIAdapter("o", cfg("openai"), api_key=KEY, session=Session(Resp(200, trunc))).complete(REQ).stop_reason == "max_tokens"
    s = Session(Resp(200, OPENAI_OK))
    ad = OpenAIAdapter("o", cfg("openai"), api_key=KEY, session=s, native_schema=False)
    r = ad.complete(REQ)
    assert "text" not in s.calls[0]["json"] and r.structured_output_mode == "prompt_only"


# ------------------------------------------------------------------ Together
TOGETHER_OK = {"id": "t1", "model": "m", "choices": [{"finish_reason": "stop", "message": {"content": '<think>hmm</think>{"a": 1}', "reasoning": "long"}}],
               "usage": {"prompt_tokens": 500, "completion_tokens": 100, "completion_tokens_details": {"reasoning_tokens": 60}}}


def test_together_request_parse_and_think_strip():
    s = Session(Resp(200, TOGETHER_OK))
    ad = TogetherAdapter("t", cfg("together", params={"temperature": 0.0, "max_tokens": 900}), api_key=KEY, session=s)
    r = ad.complete(REQ)
    c = s.calls[0]
    assert c["url"] == "https://api.together.ai/v1/chat/completions" and c["headers"]["Authorization"] == f"Bearer {KEY}"
    b = c["json"]
    assert b["messages"][0] == {"role": "system", "content": "SYSTEM TEXT"} and b["messages"][1:] == MSGS
    assert b["max_tokens"] == 900 and b["temperature"] == 0.0
    assert b["response_format"] == {"type": "json_schema", "json_schema": {"name": "surveillance_turn", "schema": MODEL_OUTPUT_JSON_SCHEMA}}
    assert r.text == '{"a": 1}' and r.usage["output_tokens"] == 100 and r.usage["reasoning_tokens"] == 60 and r.cost_usd is None
    s2 = Session(Resp(200, TOGETHER_OK))
    r2 = TogetherAdapter("t", cfg("together", structured_output="json_object"), api_key=KEY, session=s2).complete(REQ)
    assert s2.calls[0]["json"]["response_format"] == {"type": "json_object"} and r2.structured_output_mode == "json_object"
    trunc = {**TOGETHER_OK, "choices": [{"finish_reason": "length", "message": {"content": "{"}}]}
    assert TogetherAdapter("t", cfg("together"), api_key=KEY, session=Session(Resp(200, trunc))).complete(REQ).stop_reason == "max_tokens"


# ------------------------------------------------------------------ Google
GOOGLE_OK = {"responseId": "g1", "modelVersion": "gemini-x", "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "thinking", "thought": True}, {"text": '{"a": 1}'}]}}],
             "usageMetadata": {"promptTokenCount": 800, "candidatesTokenCount": 120, "thoughtsTokenCount": 80, "cachedContentTokenCount": 300}}


def test_google_request_and_parse():
    s = Session(Resp(200, GOOGLE_OK))
    ad = GoogleAdapter("g", cfg("google", model="gemini-test", params={"temperature": None, "max_tokens": 555, "thinking_config": {"thinkingLevel": "low"}}), api_key=KEY, session=s)
    r = ad.complete(REQ)
    c = s.calls[0]
    assert c["url"] == "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent"
    assert c["headers"]["x-goog-api-key"] == KEY and KEY not in c["url"]
    b = c["json"]
    assert b["systemInstruction"] == {"parts": [{"text": "SYSTEM TEXT"}]}
    assert [x["role"] for x in b["contents"]] == ["user", "model", "user"]
    g = b["generationConfig"]
    assert g["responseMimeType"] == "application/json" and g["responseJsonSchema"] == MODEL_OUTPUT_JSON_SCHEMA
    assert g["maxOutputTokens"] == 555 and "temperature" not in g and g["thinkingConfig"] == {"thinkingLevel": "low"}
    assert r.text == '{"a": 1}' and r.stop_reason == "end_turn"  # thought parts excluded
    assert r.usage == {"input_tokens": 500, "output_tokens": 200, "cache_read_input_tokens": 300, "cache_creation_input_tokens": 0, "reasoning_tokens": 80}
    assert KEY not in json.dumps(r.request_params)


def test_google_blocked_and_truncated():
    blocked = {"promptFeedback": {"blockReason": "SAFETY"}, "usageMetadata": {}}
    r = GoogleAdapter("g", cfg("google"), api_key=KEY, session=Session(Resp(200, blocked))).complete(REQ)
    assert r.text is None and r.stop_reason == "refusal"
    trunc = {**GOOGLE_OK, "candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "{"}]}}]}
    assert GoogleAdapter("g", cfg("google"), api_key=KEY, session=Session(Resp(200, trunc))).complete(REQ).stop_reason == "max_tokens"


# ------------------------------------------------------------------ shared error handling
ADAPTER_CLASSES = [(OpenAIAdapter, "openai", OPENAI_OK), (TogetherAdapter, "together", TOGETHER_OK), (GoogleAdapter, "google", GOOGLE_OK)]


@pytest.mark.parametrize("cls,prov,ok", ADAPTER_CLASSES)
def test_retry_then_success_and_error_classes(cls, prov, ok):
    sleeps = []
    s = Session(Resp(429, {}, {"retry-after": "3"}), Resp(503), Resp(200, ok))
    r = cls("m", cfg(prov), api_key=KEY, session=s, sleep=sleeps.append).complete(REQ)
    assert r.error is None and r.text and len(s.calls) == 3 and sleeps == [3.0, 2] and r.request_params["http_attempts"] == 3
    for status, kind in ((401, "AUTH"), (403, "AUTH"), (400, "REQUEST_REJECTED"), (422, "REQUEST_REJECTED")):
        s = Session(Resp(status, {"error": "x"}))
        r = cls("m", cfg(prov), api_key=KEY, session=s, sleep=lambda x: None).complete(REQ)
        assert r.error.kind == kind and r.error.status_code == status and len(s.calls) == 1  # not retried
    s = Session(Resp(529), Resp(529), Resp(529))
    r = cls("m", cfg(prov), api_key=KEY, session=s, sleep=lambda x: None).complete(REQ)
    assert r.error.kind == "INFRA_SERVER" and len(s.calls) == 3
    s = Session(requests.ConnectionError("x"), requests.Timeout("y"), requests.ConnectionError("z"))
    r = cls("m", cfg(prov), api_key=KEY, session=s, sleep=lambda x: None).complete(REQ)
    assert r.error.kind == "INFRA_CONNECTION" and KEY not in r.error.message
    r = cls("m", cfg(prov), api_key=KEY, session=Session(NotJson(200, {})), sleep=lambda x: None).complete(REQ)
    assert r.error and r.error.kind == "OTHER"


@pytest.mark.parametrize("cls,prov,ok", ADAPTER_CLASSES)
def test_missing_key_is_an_auth_error_without_a_request(cls, prov, ok, monkeypatch):
    for k in ("OPENAI_API_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY", "TOGETHER_API_KEY", "TOGETHERAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    s = Session()
    r = cls("m", cfg(prov), session=s).complete(REQ)
    assert r.error.kind == "AUTH" and s.calls == []


def test_registry_and_config_cover_the_slate():
    models = load_models()["models"]
    assert set(ADAPTERS) == {"anthropic", "openai", "google", "together"}
    for key, m in models.items():
        ad = build_adapter(key, m)
        assert ad.model == m["model"] and ad.provider == m["provider"]
        if m["provider"] != "anthropic":
            if m["enabled"]:
                assert m["pricing"]["source"] == "user" and m["pricing"]["input_per_mtok"] > 0  # user-supplied, never guessed
            else:
                assert m["pricing"] is None and m["excluded_reason"]
        if "temperature_exception" in m:  # providers that reject the parameter (confirmed by preflight)
            assert m["params"]["temperature"] is None
        else:
            assert m["params"]["temperature"] == 0.7  # one temperature across the slate
    with pytest.raises(ValueError):
        build_adapter("x", {"adapter": "nope", "model": "m"})
