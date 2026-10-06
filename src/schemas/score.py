"""Scenario result schema (scorer contract section 18)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Judgment = Literal["CORRECT", "PARTIAL", "INCORRECT"]
CRITICAL_CODES = [
    "MISSED_CREDIBLE_AFP", "FABRICATED_CONSEQUENTIAL_FIELD", "ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION",
    "FAILED_REQUIRED_ESCALATION", "DROPPED_VALID_SIGNAL", "MERGED_DISTINCT_CASES", "IGNORED_EXPLICIT_CORRECTION",
    "SUPPRESSED_POTENTIAL_DUPLICATE", "RELEVANT_SIGNAL_MARKED_NOT_RELEVANT", "CONSEQUENTIAL_DIAGNOSIS",
]


class DimensionScores(BaseModel):
    classification: int = Field(ge=0, le=2)
    extraction_state: int = Field(ge=0, le=2)
    action: int = Field(ge=0, le=2)
    conversation_quality: int = Field(ge=0, le=2)
    escalation_priority: int = Field(ge=0, le=2)
    output_adherence: int = Field(ge=0, le=2)


class ScenarioScore(BaseModel):
    scenario_id: str
    model: str
    scores: DimensionScores
    total: int = Field(ge=0, le=12)
    critical_failures: list[Literal[tuple(CRITICAL_CODES)]] = []  # type: ignore[valid-type]
    deterministic_checks: dict[str, bool] = {}
    jev_judgments: dict[str, Judgment] = {}
    notes: list[str] = []
    scorer_version: str = "v0.1"
    mapping_sha256: Optional[str] = None
