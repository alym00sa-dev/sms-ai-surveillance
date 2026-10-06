"""Provider-neutral adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AdapterRequest:
    system: str
    messages: list[dict]
    json_schema: dict | None = None
    context: dict | None = None  # harness-only (never sent to a provider); used by fake adapters


@dataclass
class AdapterError:
    kind: str            # INFRA_RATE_LIMIT | INFRA_CONNECTION | INFRA_SERVER | AUTH | REQUEST_REJECTED | OTHER
    message: str
    status_code: int | None = None
    request_id: str | None = None


@dataclass
class AdapterResponse:
    text: str | None
    raw: dict | None
    usage: dict
    latency_ms: float
    stop_reason: str | None
    request_id: str | None
    model: str | None
    request_params: dict
    structured_output_mode: str
    cost_usd: float | None = None
    error: AdapterError | None = None


class ModelAdapter(ABC):
    provider: str
    key: str            # config key
    model: str          # provider model id
    cfg: dict

    @abstractmethod
    def complete(self, req: AdapterRequest) -> AdapterResponse: ...

    def describe(self) -> dict:
        """Reproducibility record for this adapter (no secrets)."""
        return {"key": self.key, "provider": self.provider, "model": self.model,
                "params": self.cfg.get("params", {}), "structured_output": self.cfg.get("structured_output"),
                "pricing": self.cfg.get("pricing"), "verified": self.cfg.get("verified")}
