"""Model output contract (prompt README, "Required JSON output shape").

Two artifacts from one definition:
  * pydantic models + `validate_output` for deterministic validation (errors vs warnings);
  * `MODEL_OUTPUT_JSON_SCHEMA`, exported to data/model_output.schema.json, for providers with native
    structured output.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

CLASSIFICATION = ["AFP_SUSPECTED", "OTHER_VPD", "HEALTH_RELATED_UNCLEAR", "NOT_RELEVANT", "UNINTELLIGIBLE"]
ACTION = ["ACCEPT", "CLARIFY", "CONFIRM", "ESCALATE", "OTHER_VPD", "NOT_RELEVANT"]
PRIORITY = ["NORMAL", "HIGH"]
SEX = ["male", "female", "unknown"]
CONFIDENCE = ["high", "medium", "low"]
TARGET = ["symptom", "age", "sex", "location", "state", "lga", "settlement", "other"]
ESCALATION_REASON = ["FAILED_CLARIFICATION_WITH_VALID_SIGNAL", "AMBIGUOUS_LOCATION", "CONFLICTING_INFORMATION",
                     "UNABLE_TO_CLASSIFY", "OTHER"]
CONFIRMATION = ["NOT_READY", "PENDING", "CONFIRMED"]


_NULLISH = {"", "n/a", "na", "null", "none"}


class _M(BaseModel):
    # strict: no type coercion (e.g. "false" for a boolean, 7.5 for an age). Wrong types, invalid enum values and
    # missing required fields are schema ERRORS. Only extra keys (and valid-but-inconsistent combinations) are warnings.
    model_config = ConfigDict(extra="allow", strict=True)


class Case(_M):
    case_id: str
    symptom: Optional[str]
    age: Union[int, str, None]
    sex: Optional[Literal["male", "female", "unknown"]]
    state: Optional[str]
    lga: Optional[str]
    settlement: Optional[str]

    @field_validator("symptom", "age", "state", "lga", "settlement")
    @classmethod
    def _no_nullish_strings(cls, v):
        # contract "Null handling": use JSON null, never "" or "N/A"
        if isinstance(v, str) and v.strip().casefold() in _NULLISH:
            raise ValueError("use JSON null for missing values, not an empty string or N/A")
        return v


class LocationResolution(_M):
    case_id: str
    raw_location: Optional[str]

    @field_validator("raw_location")
    @classmethod
    def _no_nullish(cls, v):
        if isinstance(v, str) and v.strip().casefold() in _NULLISH:
            raise ValueError("use JSON null for missing values, not an empty string or N/A")
        return v
    inferred_fields: list[str]
    confidence: Literal["high", "medium", "low"]


class Escalation(_M):
    required: bool
    reason: Optional[Literal[tuple(ESCALATION_REASON)]]  # type: ignore[valid-type]


class Clarification(_M):
    target: Optional[Literal[tuple(TARGET)]]  # type: ignore[valid-type]
    attempt_number: int


class Confirmation(_M):
    status: Literal["NOT_READY", "PENDING", "CONFIRMED"]


class ModelOutput(_M):
    classification: Literal[tuple(CLASSIFICATION)]  # type: ignore[valid-type]
    other_vpd: bool
    action: Literal[tuple(ACTION)]  # type: ignore[valid-type]
    priority: Literal["NORMAL", "HIGH"]
    cases: list[Case]
    location_resolution: list[LocationResolution]
    missing_information: list[str]
    potential_duplicate: bool
    duplicate_candidate_ids: list[str]
    escalation: Escalation
    clarification: Clarification
    confirmation: Confirmation
    response: str


# ---- JSON Schema for native structured output -------------------------------------------------
def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def _obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


_STR = {"type": "string"}
MODEL_OUTPUT_JSON_SCHEMA: dict = _obj({
    "classification": {"type": "string", "enum": CLASSIFICATION},
    "other_vpd": {"type": "boolean"},
    "action": {"type": "string", "enum": ACTION},
    "priority": {"type": "string", "enum": PRIORITY},
    "cases": {"type": "array", "items": _obj({
        "case_id": _STR,
        "symptom": _nullable(_STR),
        "age": {"anyOf": [{"type": "integer"}, _STR, {"type": "null"}]},
        "sex": _nullable({"type": "string", "enum": SEX}),
        "state": _nullable(_STR),
        "lga": _nullable(_STR),
        "settlement": _nullable(_STR),
    })},
    "location_resolution": {"type": "array", "items": _obj({
        "case_id": _STR,
        "raw_location": _nullable(_STR),
        "inferred_fields": {"type": "array", "items": _STR},
        "confidence": {"type": "string", "enum": CONFIDENCE},
    })},
    "missing_information": {"type": "array", "items": _STR},
    "potential_duplicate": {"type": "boolean"},
    "duplicate_candidate_ids": {"type": "array", "items": _STR},
    "escalation": _obj({"required": {"type": "boolean"}, "reason": _nullable({"type": "string", "enum": ESCALATION_REASON})}),
    "clarification": _obj({"target": _nullable({"type": "string", "enum": TARGET}), "attempt_number": {"type": "integer"}}),
    "confirmation": _obj({"status": {"type": "string", "enum": CONFIRMATION}}),
    "response": _STR,
})


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    parsed: dict | None = None


_EXPECTED_STATUS = {"CONFIRM": "PENDING", "ACCEPT": "CONFIRMED", "CLARIFY": "NOT_READY", "ESCALATE": "NOT_READY",
                    "OTHER_VPD": "NOT_READY", "NOT_RELEVANT": "NOT_READY"}


def parse_json_text(text: str | None) -> tuple[Any, list[str]]:
    """Strict JSON first; a single code-fenced JSON object is recoverable (warning)."""
    warnings: list[str] = []
    if text is None:
        raise ValueError("empty response")
    t = text.strip()
    try:
        return json.loads(t), warnings
    except json.JSONDecodeError:
        if t.startswith("```") and t.endswith("```"):
            inner = t.strip("`").removeprefix("json").strip()
            try:
                obj = json.loads(inner)
                return obj, ["wrapped_in_code_fence"]
            except json.JSONDecodeError:
                pass
        raise


def validate_output(obj: Any) -> ValidationResult:
    if not isinstance(obj, dict):
        return ValidationResult(False, ["top-level value is not a JSON object"])
    try:
        m = ModelOutput.model_validate(obj)
    except ValidationError as e:
        errs = [f"{'.'.join(str(p) for p in x['loc'])}: {x['msg']}" for x in e.errors()]
        return ValidationResult(False, errs)
    warnings = []
    extra = set(obj) - set(ModelOutput.model_fields)
    if extra:
        warnings.append(f"extra top-level keys: {sorted(extra)}")
    for i, c in enumerate(m.cases):
        if c.model_extra:
            warnings.append(f"cases[{i}] extra keys: {sorted(c.model_extra)}")
    if m.other_vpd != (m.classification == "OTHER_VPD"):
        warnings.append("consistency: other_vpd does not match classification")
    if m.escalation.required != (m.action == "ESCALATE"):
        warnings.append("consistency: escalation.required does not match action")
    if m.action in _EXPECTED_STATUS and m.confirmation.status != _EXPECTED_STATUS[m.action]:
        warnings.append(f"consistency: confirmation.status should be {_EXPECTED_STATUS[m.action]} for {m.action}")
    if m.action == "CLARIFY" and m.clarification.target is None:
        warnings.append("consistency: CLARIFY without clarification.target")
    return ValidationResult(True, [], warnings, obj)
