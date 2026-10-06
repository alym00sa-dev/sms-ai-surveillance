"""Per-turn model input envelope (see SMS_AI_SURVEILLANCE_PROMPT_README.md)."""
from __future__ import annotations

from .location_fixture import LocationResolver


def build_envelope(conversation: list[dict], current_case_state: dict, clarification_attempts: int,
                   candidate_prior_reports: list[dict], resolver: LocationResolver) -> dict:
    user_messages = [m["content"] for m in conversation if m["role"] == "user"]
    return {
        "conversation": [dict(m) for m in conversation],  # snapshot: the runner keeps appending to its own list
        "current_case_state": current_case_state,
        "clarification_attempts": clarification_attempts,
        "candidate_prior_reports": candidate_prior_reports,
        "location_resolver": resolver.resolve(user_messages),
    }
