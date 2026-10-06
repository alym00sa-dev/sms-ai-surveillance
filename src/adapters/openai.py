"""OpenAI Responses API adapter (the recommended API for new projects; `text.format` json_schema, strict).

Docs: https://developers.openai.com/api/docs/guides/structured-outputs
"""
from __future__ import annotations

from .base import AdapterRequest
from .http import HttpAdapter

SCHEMA_NAME = "surveillance_turn"


class OpenAIAdapter(HttpAdapter):
    provider = "openai"
    env_keys = ("OPENAI_API_KEY",)
    default_base_url = "https://api.openai.com/v1"

    def auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}

    def build(self, req: AdapterRequest):
        p = self.cfg.get("params", {})
        body: dict = {"model": self.model, "instructions": req.system, "input": [{"role": m["role"], "content": m["content"]} for m in req.messages],
                      "max_output_tokens": p.get("max_tokens", 4096), "store": False}
        if p.get("temperature") is not None:
            body["temperature"] = p["temperature"]
        if p.get("reasoning_effort"):
            body["reasoning"] = {"effort": p["reasoning_effort"]}
        if self.native_schema and req.json_schema:
            body["text"] = {"format": {"type": "json_schema", "name": SCHEMA_NAME, "strict": True, "schema": req.json_schema}}
        body.update(self.cfg.get("extra_body", {}))
        params = {k: v for k, v in body.items() if k not in ("instructions", "input")}
        if "text" in params:
            params["text"] = {"format": {**params["text"]["format"], "schema": "<MODEL_OUTPUT_JSON_SCHEMA>"}}
        return f"{self.base_url}/responses", {"Content-Type": "application/json"}, body, params

    def parse(self, body: dict):
        texts, refusal = [], False
        for item in body.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        texts.append(part.get("text", ""))
                    elif part.get("type") == "refusal":
                        refusal = True
        status = body.get("status")
        reason = (body.get("incomplete_details") or {}).get("reason")
        stop = "refusal" if refusal else "max_tokens" if reason == "max_output_tokens" else "content_filter" if reason == "content_filter" \
            else "end_turn" if status == "completed" else (status or None)
        u = body.get("usage") or {}
        cached = (u.get("input_tokens_details") or {}).get("cached_tokens", 0) or 0
        usage = {"input_tokens": (u.get("input_tokens", 0) or 0) - cached, "output_tokens": u.get("output_tokens", 0) or 0,
                 "cache_read_input_tokens": cached, "cache_creation_input_tokens": 0,
                 "reasoning_tokens": (u.get("output_tokens_details") or {}).get("reasoning_tokens", 0) or 0}
        return ("".join(texts) or None), stop, usage, body.get("id"), body.get("model")
