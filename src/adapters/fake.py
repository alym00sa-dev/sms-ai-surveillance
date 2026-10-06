"""Fake adapters for tests and API-free dry runs."""
from __future__ import annotations

import json
from typing import Callable

from .base import AdapterError, AdapterRequest, AdapterResponse, ModelAdapter


_QUESTION = {"age": "How old is the child?", "location": "Which village or community is the child in?",
             "symptom": "Can you describe the symptom?", "sex": "Is the child a boy or a girl?",
             "state": "Which state is it in?", "lga": "Which LGA is it in?", "settlement": "Which village is it in?", "other": "Can you tell me more?"}


def _describe(c: dict) -> str:
    who = {"male": "boy", "female": "girl"}.get(c.get("sex"), "child")
    age = c.get("age")
    parts = [f"{who}" + (f", age {age}" if age is not None else "")]
    place = ", ".join(str(c[k]) for k in ("settlement", "lga", "state") if c.get(k))
    if place:
        parts.append(place)
    if c.get("symptom"):
        parts.append(c["symptom"])
    return ", ".join(parts)


def gold_output(scenario: dict, i: int) -> dict:
    e = scenario["turns"][i]["expected"]
    keys = ("age", "sex", "state", "lga", "settlement", "symptom")
    cases = [{"case_id": f"case_{n + 1}", **{k: c.get(k) for k in keys}} for n, c in enumerate(e["cases"])]
    if e["action"] == "CONFIRM":
        body = "; ".join(f"{n + 1}) {_describe(c)}" for n, c in enumerate(cases)) if len(cases) > 1 else _describe(cases[0])
        response = f"I have: {body}. Is this correct?"
    elif e["action"] == "CLARIFY":
        response = _QUESTION.get(e["clarification_target"], _QUESTION["other"])
    elif e["action"] == "ACCEPT":
        response = "Thank you. Your report has been received and will be followed up."
    elif e["action"] == "ESCALATE":
        response = "Thank you. A health worker will contact you."
    elif e["action"] == "OTHER_VPD":
        response = "Thank you. Your report has been recorded."
    else:
        response = "Sorry, this line is only for health reports."
    ids = [p["case_id"] for p in scenario["prior_reports"]] if e["potential_duplicate"] else []
    return {
        "classification": e["classification"], "other_vpd": e["other_vpd"], "action": e["action"],
        "priority": e["priority"], "cases": cases, "location_resolution": [],
        "missing_information": list(e["missing_important_fields"]),
        "potential_duplicate": e["potential_duplicate"], "duplicate_candidate_ids": ids,
        "escalation": {"required": e["action"] == "ESCALATE", "reason": e["escalation_reason"]},
        "clarification": {"target": e["clarification_target"], "attempt_number": 0},
        "confirmation": {"status": e["confirmation_status"]},
        "response": response,
    }


class FakeAdapter(ModelAdapter):
    """policy(request) -> dict | str | AdapterError."""
    provider = "fake"

    def __init__(self, policy: Callable[[AdapterRequest], object], key: str = "fake", model: str = "fake-model",
                 cost_per_call: float | None = 0.0):
        self.policy, self.key, self.model, self.cost_per_call = policy, key, model, cost_per_call
        self.cfg = {"params": {}, "structured_output": "native_json_schema", "pricing": None, "verified": False}
        self.calls: list[AdapterRequest] = []

    def complete(self, req: AdapterRequest) -> AdapterResponse:
        self.calls.append(req)
        out = self.policy(req)
        params = {"model": self.model}
        if isinstance(out, AdapterError):
            return AdapterResponse(None, None, {}, 1.0, None, None, None, params, "native_json_schema", error=out)
        text = out if isinstance(out, str) else json.dumps(out)
        usage = {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
        return AdapterResponse(text, {"fake": True}, usage, 1.0, "end_turn", "req_fake", self.model, params,
                               "native_json_schema", cost_usd=self.cost_per_call)


def oracle_adapter() -> FakeAdapter:
    """Replays the gold annotation for the sender's current cursor."""
    def policy(req: AdapterRequest):
        ctx = req.context
        return gold_output(ctx["scenario"], ctx["sender"].cursor)
    return FakeAdapter(policy, key="oracle", model="oracle")
