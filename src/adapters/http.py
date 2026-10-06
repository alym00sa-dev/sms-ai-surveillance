"""Shared HTTP plumbing for the REST-based adapters (OpenAI, Google, Together)."""
from __future__ import annotations

import time
from abc import abstractmethod
from dataclasses import dataclass

import requests

from ..config import compute_cost
from .base import AdapterError, AdapterRequest, AdapterResponse, ModelAdapter

_RETRY = {408, 429, 500, 502, 503, 504, 529}


@dataclass
class HttpOutcome:
    status: int | None
    body: dict | None
    headers: dict
    latency_ms: float
    attempts: int
    error: AdapterError | None = None


def classify(status: int) -> str:
    if status in (401, 403):
        return "AUTH"
    if status in (400, 404, 413, 422):
        return "REQUEST_REJECTED"
    if status in (408, 429):
        return "INFRA_RATE_LIMIT"
    return "INFRA_SERVER" if status >= 500 else "OTHER"


def post_json(session, url: str, headers: dict, body: dict, timeout: float, max_attempts: int = 3,
              sleep=time.sleep) -> HttpOutcome:
    """POST with retry on 408/429/5xx and connection errors (honours Retry-After). Never raises."""
    t0 = time.perf_counter()
    last: AdapterError | None = None
    for attempt in range(1, max_attempts + 1):
        retry_after = None
        try:
            r = session.post(url, json=body, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            last = AdapterError("INFRA_CONNECTION", type(e).__name__)
        else:
            rid = r.headers.get("x-request-id") or r.headers.get("request-id") or r.headers.get("x-goog-request-id")
            if r.status_code == 200:
                try:
                    return HttpOutcome(200, r.json(), dict(r.headers), (time.perf_counter() - t0) * 1000, attempt)
                except ValueError:
                    last = AdapterError("OTHER", "200 response was not JSON", 200, rid)
                    break
            last = AdapterError(classify(r.status_code), f"HTTP {r.status_code}: {r.text[:300]}", r.status_code, rid)
            if r.status_code not in _RETRY:
                break
            try:
                retry_after = float(r.headers.get("retry-after", ""))
            except ValueError:
                retry_after = None
        if attempt < max_attempts:
            sleep(min(retry_after if retry_after is not None else 2 ** (attempt - 1), 20))
    return HttpOutcome(last.status_code if last else None, None, {}, (time.perf_counter() - t0) * 1000, attempt, last)


class HttpAdapter(ModelAdapter):
    """Template: subclasses build the provider request and parse the provider response."""
    env_keys: tuple[str, ...] = ()
    default_base_url = ""

    def __init__(self, key: str, cfg: dict, api_key: str | None = None, session: requests.Session | None = None,
                 native_schema: bool | None = None, timeout_s: float = 120.0, max_attempts: int = 3, sleep=time.sleep):
        import os
        self.key, self.cfg, self.model = key, cfg, cfg["model"]
        self._api_key = api_key or next((os.environ[k] for k in self.env_keys if os.environ.get(k)), None)
        self.base_url = (cfg.get("base_url") or self.default_base_url).rstrip("/")
        self._mode = cfg.get("structured_output", "prompt_only")
        self.native_schema = (self._mode in ("native_json_schema", "json_object")) if native_schema is None else native_schema
        self.timeout_s, self.max_attempts, self._sleep = timeout_s, max_attempts, sleep
        self._session = session or requests.Session()

    @property
    def structured_output_mode(self) -> str:
        if not self.native_schema:
            return "prompt_only"
        return self._mode if self._mode in ("native_json_schema", "json_object") else "native_json_schema"

    def describe(self) -> dict:
        d = super().describe()
        d.update(structured_output_mode=self.structured_output_mode, base_url=self.base_url, timeout_s=self.timeout_s,
                 max_attempts=self.max_attempts, streaming=False, api_key_env=list(self.env_keys))
        return d

    @abstractmethod
    def build(self, req: AdapterRequest) -> tuple[str, dict, dict, dict]:
        """-> (url, headers without the key, body, loggable params)"""

    @abstractmethod
    def auth_header(self) -> dict: ...

    @abstractmethod
    def parse(self, body: dict) -> tuple[str | None, str | None, dict, str | None, str | None]:
        """-> (text, stop_reason, usage, request_id, model)"""

    def complete(self, req: AdapterRequest) -> AdapterResponse:
        url, headers, body, params = self.build(req)
        if not self._api_key:
            err = AdapterError("AUTH", f"no API key in {' / '.join(self.env_keys)}")
            return AdapterResponse(None, None, {}, 0.0, None, None, None, params, self.structured_output_mode, error=err)
        out = post_json(self._session, url, {**headers, **self.auth_header()}, body, self.timeout_s, self.max_attempts, self._sleep)
        if out.error:
            return AdapterResponse(None, None, {}, out.latency_ms, None, out.error.request_id, None, params,
                                   self.structured_output_mode, error=out.error)
        text, stop, usage, rid, model = self.parse(out.body)
        return AdapterResponse(text, out.body, usage, out.latency_ms, stop, rid, model or self.model, {**params, "http_attempts": out.attempts},
                               self.structured_output_mode, cost_usd=compute_cost(usage, self.cfg.get("pricing")))

