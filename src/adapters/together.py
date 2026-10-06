"""Together AI adapter (OpenAI-compatible Chat Completions).

`structured_output` in the model config: native_json_schema (response_format json_schema) | json_object | prompt_only.
Reasoning models put their thinking in `message.reasoning` / `reasoning_content`; only `content` is used. A leading
<think>...</think> block (DeepSeek-R1 style) is stripped and logged.
Docs: https://docs.together.ai/docs/json-mode, https://docs.together.ai/docs/reasoning-overview
"""
from __future__ import annotations

import re

from .base import AdapterRequest
from .http import HttpAdapter

_THINK = re.compile(r"^\s*<think>.*?</think>\s*", re.S)


class TogetherAdapter(HttpAdapter):
    provider = "together"
    env_keys = ("TOGETHER_API_KEY", "TOGETHERAI_API_KEY")
    default_base_url = "https://api.together.ai/v1"

    def auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}

    def build(self, req: AdapterRequest):
        p = self.cfg.get("params", {})
        msgs = [{"role": "system", "content": req.system}] + [{"role": m["role"], "content": m["content"]} for m in req.messages]
        body: dict = {"model": self.model, "messages": msgs, "max_tokens": p.get("max_tokens", 4096)}
        if p.get("temperature") is not None:
            body["temperature"] = p["temperature"]
        if p.get("reasoning_effort"):
            body["reasoning_effort"] = p["reasoning_effort"]
        mode = self.cfg.get("structured_output")
        if self.native_schema and req.json_schema:
            if mode == "json_object":
                body["response_format"] = {"type": "json_object"}
            else:
                body["response_format"] = {"type": "json_schema", "json_schema": {"name": "surveillance_turn", "schema": req.json_schema}}
        body.update(self.cfg.get("extra_body", {}))
        params = {k: v for k, v in body.items() if k != "messages"}
        rf = params.get("response_format")
        if rf and rf.get("type") == "json_schema":
            params["response_format"] = {"type": "json_schema", "json_schema": {"name": "surveillance_turn", "schema": "<MODEL_OUTPUT_JSON_SCHEMA>"}}
        return f"{self.base_url}/chat/completions", {"Content-Type": "application/json"}, body, params

    def parse(self, body: dict):
        ch = (body.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        text = msg.get("content")
        if isinstance(text, str):
            text = _THINK.sub("", text) or None
        fin = ch.get("finish_reason")
        stop = "refusal" if msg.get("refusal") else "max_tokens" if fin == "length" else "end_turn" if fin in ("stop", "eos") else fin
        u = body.get("usage") or {}
        cached = ((u.get("prompt_tokens_details") or {}).get("cached_tokens", 0)) or 0
        usage = {"input_tokens": (u.get("prompt_tokens", 0) or 0) - cached, "output_tokens": u.get("completion_tokens", 0) or 0,
                 "cache_read_input_tokens": cached, "cache_creation_input_tokens": 0,
                 "reasoning_tokens": ((u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0)) or 0}
        return text, stop, usage, body.get("id"), body.get("model")
