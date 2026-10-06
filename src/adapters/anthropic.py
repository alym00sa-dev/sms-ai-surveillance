"""Anthropic Messages API adapter (anthropic SDK, non-streaming; outputs are short)."""
from __future__ import annotations

import time

import anthropic

from ..config import compute_cost
from .base import AdapterError, AdapterRequest, AdapterResponse, ModelAdapter


class AnthropicAdapter(ModelAdapter):
    provider = "anthropic"

    def __init__(self, key: str, cfg: dict, client: "anthropic.Anthropic | None" = None,
                 native_schema: bool | None = None, sdk_max_retries: int = 2, timeout_s: float = 120.0):
        self.key, self.cfg, self.model = key, cfg, cfg["model"]
        self.sdk_max_retries, self.timeout_s = sdk_max_retries, timeout_s
        self.native_schema = (cfg.get("structured_output") == "native_json_schema") if native_schema is None else native_schema
        self.client = client or anthropic.Anthropic(max_retries=sdk_max_retries, timeout=timeout_s)  # key from ANTHROPIC_API_KEY

    @property
    def structured_output_mode(self) -> str:
        return "native_json_schema" if self.native_schema else "prompt_only"

    def describe(self) -> dict:
        d = super().describe()
        d.update(structured_output_mode=self.structured_output_mode, sdk="anthropic " + anthropic.__version__,
                 sdk_max_retries=self.sdk_max_retries, timeout_s=self.timeout_s, streaming=False)
        return d

    def _kwargs(self, req: AdapterRequest) -> dict:
        p = self.cfg.get("params", {})
        kw: dict = {"model": self.model, "max_tokens": p.get("max_tokens", 2048), "system": req.system,
                    "messages": req.messages}
        if p.get("temperature") is not None:
            kw["temperature"] = p["temperature"]
        if p.get("thinking") is not None:
            kw["thinking"] = p["thinking"]
        out_cfg: dict = {}
        if p.get("output_effort"):
            out_cfg["effort"] = p["output_effort"]
        if self.native_schema and req.json_schema:
            out_cfg["format"] = {"type": "json_schema", "schema": req.json_schema}
        if out_cfg:
            kw["output_config"] = out_cfg
        return kw

    def complete(self, req: AdapterRequest) -> AdapterResponse:
        kw = self._kwargs(req)
        params = {k: v for k, v in kw.items() if k not in ("system", "messages")}
        if "output_config" in params and "format" in params["output_config"]:
            params["output_config"] = {**params["output_config"], "format": {"type": "json_schema", "schema": "<MODEL_OUTPUT_JSON_SCHEMA>"}}
        t0 = time.perf_counter()
        try:
            msg = self.client.messages.create(**kw)
        except anthropic.RateLimitError as e:
            return self._fail("INFRA_RATE_LIMIT", e, t0, params)
        except anthropic.APIConnectionError as e:  # includes timeouts
            return self._fail("INFRA_CONNECTION", e, t0, params)
        except anthropic.AuthenticationError as e:
            return self._fail("AUTH", e, t0, params)
        except anthropic.PermissionDeniedError as e:
            return self._fail("AUTH", e, t0, params)
        except anthropic.BadRequestError as e:
            return self._fail("REQUEST_REJECTED", e, t0, params)
        except anthropic.NotFoundError as e:
            return self._fail("REQUEST_REJECTED", e, t0, params)
        except anthropic.APIStatusError as e:
            return self._fail("INFRA_SERVER" if e.status_code >= 500 else "OTHER", e, t0, params)
        latency = (time.perf_counter() - t0) * 1000
        text = "".join(b.text for b in msg.content if b.type == "text") or None
        u = msg.usage
        usage = {"input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                 "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
                 "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0}
        return AdapterResponse(
            text=text, raw=msg.to_dict(), usage=usage, latency_ms=latency, stop_reason=msg.stop_reason,
            request_id=getattr(msg, "_request_id", None), model=msg.model, request_params=params,
            structured_output_mode=self.structured_output_mode, cost_usd=compute_cost(usage, self.cfg.get("pricing")))

    def _fail(self, kind: str, e: Exception, t0: float, params: dict) -> AdapterResponse:
        status = getattr(e, "status_code", None)
        rid = getattr(e, "request_id", None)
        return AdapterResponse(
            text=None, raw=None, usage={}, latency_ms=(time.perf_counter() - t0) * 1000, stop_reason=None,
            request_id=rid, model=None, request_params=params, structured_output_mode=self.structured_output_mode,
            error=AdapterError(kind=kind, message=f"{type(e).__name__}: {str(e)[:500]}", status_code=status, request_id=rid))
