"""Benchmark scenario schema (v0.3.1 JSONL rows)."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from .model_output import ACTION, CLASSIFICATION


class ExpectedTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    classification: Literal[tuple(CLASSIFICATION)]  # type: ignore[valid-type]
    action: Literal[tuple(ACTION)]  # type: ignore[valid-type]
    priority: Literal["NORMAL", "HIGH"]
    score_priority: bool
    missing_important_fields: list[str]
    clarification_target: Optional[str]
    potential_duplicate: bool
    escalation_reason: Optional[str]
    response_intent: str
    critical_checks: list[str]
    other_vpd: bool
    cases: list[dict[str, Any]]
    confirmation_status: Literal["NOT_READY", "PENDING", "CONFIRMED"]

    @field_validator("cases")
    @classmethod
    def _case_keys(cls, v):
        allowed = {"age", "sex", "state", "lga", "settlement", "symptom"}
        for c in v:
            bad = set(c) - allowed
            if bad:
                raise ValueError(f"unknown gold case keys {sorted(bad)}")
        return v


class Turn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user: str
    expected: ExpectedTurn


class BenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str
    category: str
    tags: list[str]
    prior_reports: list[dict[str, Any]]
    turns: list[Turn]
    notes: str
    benchmark_version: Optional[str] = None


def validate_benchmark(rows: list[dict]) -> list[BenchmarkCase]:
    cases = [BenchmarkCase.model_validate(r) for r in rows]
    ids = [c.id for c in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate scenario ids")
    return cases
