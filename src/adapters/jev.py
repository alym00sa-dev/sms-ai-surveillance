"""Jev (TypeSafe System One) HTTP client.

POST https://api.typesafe.ai/v1/systemone  with `Authorization: Bearer <key>`;
body {model, state, questions}; answers carry typed values, probabilities and confidence.
Docs: https://docs.typesafe.ai/api.md  (model pinned to jev-1.13.0 for reproducibility, not the jev-latest alias).
The key is read from JEV_API_KEY (or TYPESAFE_API_KEY) and never logged.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import requests

JEV_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-1.13.0"
JEV_PRICING = {"input_per_mtok": 0.042, "output_per_mtok": 0.0,
               "source": "https://docs.typesafe.ai/models.md ($0.042 per million input tokens; output free)"}
_RETRY_STATUS = {429, 500, 502, 503, 504, 529}


class JevError(Exception):
    def __init__(self, kind: str, message: str, status: int | None = None, request_id: str | None = None):
        super().__init__(message)
        self.kind, self.status, self.request_id = kind, status, request_id


@dataclass
class JevResult:
    answers: dict
    usage: dict
    latency_ms: float
    model: str | None
    request_id: str | None
    attempts: int
    cost_usd: float | None = None


def noul(instructions: str, criteria: dict | None = None) -> dict:
    q = {"type": "noul", "instructions": instructions}
    if criteria:
        q["criteria"] = criteria
    return q


def choice(instructions: str, criteria: dict[str, str]) -> dict:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


class JevClient:
    def __init__(self, api_key: str | None = None, model: str = JEV_MODEL, url: str = JEV_URL, timeout_s: float = 30.0,
                 max_attempts: int = 4, sleep=time.sleep, session: requests.Session | None = None):
        self._key = api_key or os.environ.get("JEV_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
        self.model, self.url, self.timeout_s, self.max_attempts = model, url, timeout_s, max_attempts
        self._sleep, self._session = sleep, session or requests.Session()

    def describe(self) -> dict:
        return {"provider": "typesafe", "model": self.model, "endpoint": self.url, "timeout_s": self.timeout_s,
                "max_attempts": self.max_attempts, "pricing": JEV_PRICING}

    def system_one(self, state, questions: dict) -> JevResult:
        if not self._key:
            raise JevError("AUTH", "no Jev API key in JEV_API_KEY / TYPESAFE_API_KEY")
        body = {"model": self.model, "state": state, "questions": questions}
        headers = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        last: JevError | None = None
        for attempt in range(1, self.max_attempts + 1):
            t0 = time.perf_counter()
            try:
                r = self._session.post(self.url, json=body, headers=headers, timeout=self.timeout_s)
            except requests.RequestException as e:
                last = JevError("INFRA_CONNECTION", f"{type(e).__name__}")
            else:
                rid = r.headers.get("request-id") or r.headers.get("x-request-id")
                if r.status_code == 200:
                    j = r.json()
                    usage = j.get("usage", {})
                    cost = (usage.get("input_tokens", 0) * JEV_PRICING["input_per_mtok"] / 1e6) if usage else None
                    return JevResult(j["answers"], usage, (time.perf_counter() - t0) * 1000, j.get("model"), rid, attempt, cost)
                kind = {401: "AUTH", 422: "REQUEST_REJECTED", 429: "INFRA_RATE_LIMIT", 529: "INFRA_OVERLOADED"}.get(
                    r.status_code, "INFRA_SERVER" if r.status_code >= 500 else "OTHER")
                last = JevError(kind, f"HTTP {r.status_code}: {r.text[:300]}", r.status_code, rid)
                if r.status_code not in _RETRY_STATUS:
                    raise last
            if attempt < self.max_attempts:
                self._sleep(min(2 ** (attempt - 1), 8))
        raise last  # type: ignore[misc]


class FakeJevClient:
    """answer_fn(state, questions) -> {question_id: {"choice":..., "probabilities":..., "confidence":...}}"""
    def __init__(self, answer_fn, model: str = JEV_MODEL):
        self.answer_fn, self.model, self.calls = answer_fn, model, []

    def describe(self) -> dict:
        return {"provider": "fake-typesafe", "model": self.model}

    def system_one(self, state, questions: dict) -> JevResult:
        self.calls.append((state, questions))
        return JevResult(self.answer_fn(state, questions), {"input_tokens": 100, "output_tokens": 10}, 1.0, self.model, "req_fake", 1, 100 * 0.042 / 1e6)
