"""Google Gemini adapter (generateContent REST; `responseJsonSchema` structured output).

The newer Interactions API exists, but Google states generateContent "remains fully supported"; it is used here
because its request/response shapes are stable. Docs: https://ai.google.dev/gemini-api/docs/structured-output
"""
from __future__ import annotations

from .base import AdapterRequest
from .http import HttpAdapter


class GoogleAdapter(HttpAdapter):
    provider = "google"
    env_keys = ("GOOGLE_API_KEY", "GEMINI_API_KEY")
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"

    def auth_header(self) -> dict:
        return {"x-goog-api-key": self._api_key}

    def build(self, req: AdapterRequest):
        p = self.cfg.get("params", {})
        gen: dict = {"maxOutputTokens": p.get("max_tokens", 4096)}
        if p.get("temperature") is not None:
            gen["temperature"] = p["temperature"]
        if p.get("thinking_config"):
            gen["thinkingConfig"] = p["thinking_config"]
        if self.native_schema and req.json_schema:
            gen["responseMimeType"] = "application/json"
            gen["responseJsonSchema"] = req.json_schema
        body = {"systemInstruction": {"parts": [{"text": req.system}]},
                "contents": [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in req.messages],
                "generationConfig": gen}
        body.update(self.cfg.get("extra_body", {}))
        gl = dict(gen)
        if "responseJsonSchema" in gl:
            gl["responseJsonSchema"] = "<MODEL_OUTPUT_JSON_SCHEMA>"
        params = {"model": self.model, "generationConfig": gl}
        return f"{self.base_url}/models/{self.model}:generateContent", {"Content-Type": "application/json"}, body, params

    def parse(self, body: dict):
        cand = (body.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts if not p.get("thought")) or None
        fin = cand.get("finishReason")
        blocked = (body.get("promptFeedback") or {}).get("blockReason")
        stop = "refusal" if blocked or fin in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION") \
            else "max_tokens" if fin == "MAX_TOKENS" else "end_turn" if fin == "STOP" else fin
        u = body.get("usageMetadata") or {}
        cached = u.get("cachedContentTokenCount", 0) or 0
        thoughts = u.get("thoughtsTokenCount", 0) or 0
        usage = {"input_tokens": (u.get("promptTokenCount", 0) or 0) - cached,
                 "output_tokens": (u.get("candidatesTokenCount", 0) or 0) + thoughts,
                 "cache_read_input_tokens": cached, "cache_creation_input_tokens": 0, "reasoning_tokens": thoughts}
        return text, stop, usage, body.get("responseId"), body.get("modelVersion")
