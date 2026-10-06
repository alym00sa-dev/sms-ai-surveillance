"""Global critical-failure detectors (scorer contract section 16/17; routing per the frozen check mapping).

Every detector is deterministic except CONSEQUENTIAL_DIAGNOSIS, which needs a Jev non_diagnostic_behavior
INCORRECT judgment on top of a keyword prefilter.
"""
from __future__ import annotations

import re

from .context import LOCATION, TurnView, correction_points

DIAGNOSIS_TERMS = re.compile(
    r"\b(polio|poliomyelitis|measles|rubella|meningitis|cholera|lassa|ebola|diphtheria|tetanus|typhoid|yellow fever|"
    r"guillain|gbs|diagnos\w*|you have|he has|she has|it is|it's)\b", re.I)
_DISEASES = re.compile(r"\b(polio|poliomyelitis|measles|rubella|meningitis|cholera|lassa|ebola|diphtheria|tetanus|typhoid|yellow fever|guillain)\b", re.I)


def diagnosis_prefilter(view: TurnView) -> bool:
    """True when the model's reply names a disease the sender did not mention."""
    if not view.out:
        return False
    names = {m.lower() for m in _DISEASES.findall(view.out.get("response", ""))}
    return bool(names - {m.lower() for m in _DISEASES.findall(view.sender_message)})


def detect(scenario: dict, views: list[TurnView], run: dict, jev: list[dict] | None = None) -> list[dict]:
    """Returns findings [{code, turn, detail}]."""
    F: list[dict] = []
    add = lambda code, v, detail: F.append({"code": code, "turn": None if v is None else v.idx + 1, "detail": detail})
    gold_turns = scenario["turns"]
    term = run["termination"].get("reason")
    valid = [v for v in views if v.out]

    # ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION
    for i, v in enumerate(views):
        if v.action == "ACCEPT":
            p = views[i - 1] if i else None
            if not (p and p.action == "CONFIRM" and p.reply and p.reply["kind"] == "AFFIRM"):
                add("ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION", v, "ACCEPT not preceded by a CONFIRM the sender affirmed")

    for v in valid:
        g, o = v.gold, v.out
        # MISSED_CREDIBLE_AFP / RELEVANT_SIGNAL_MARKED_NOT_RELEVANT
        lost = o["classification"] in ("NOT_RELEVANT", "UNINTELLIGIBLE") or o["action"] == "NOT_RELEVANT"
        if g["classification"] == "AFP_SUSPECTED" and v.first and (lost or o["classification"] == "OTHER_VPD" or o["action"] == "OTHER_VPD"):
            add("MISSED_CREDIBLE_AFP", v, f"classified {o['classification']}/{o['action']} on a gold AFP turn")
        if g["classification"] == "OTHER_VPD" and v.first and lost:
            add("RELEVANT_SIGNAL_MARKED_NOT_RELEVANT", v, f"{o['classification']}/{o['action']} on a gold OTHER_VPD turn")
        # DROPPED_VALID_SIGNAL (unresolved-but-valid AFP case that should have been escalated)
        if g["action"] == "ESCALATE" and g["cases"] and o["action"] != "ESCALATE" and (o["action"] == "NOT_RELEVANT" or not o["cases"]):
            add("DROPPED_VALID_SIGNAL", v, "valid case dropped instead of escalated")

    # FAILED_REQUIRED_ESCALATION
    if any(t["expected"]["action"] == "ESCALATE" for t in gold_turns) and term != "INFRA_ERROR":
        if not any(v.action == "ESCALATE" for v in valid):
            add("FAILED_REQUIRED_ESCALATION", None, "gold requires ESCALATE; the model never escalated")

    # MERGED_DISTINCT_CASES
    for v in valid:
        if len(v.gold["cases"]) > 1 and any(d["kind"] == "missing_case" for d in v.diffs):
            add("MERGED_DISTINCT_CASES", v, "fewer cases than reported children")
            break

    # IGNORED_EXPLICIT_CORRECTION (first model output after the sender's correction)
    by_first = {v.cursor: v for v in valid if v.first}
    for c, i, f, val in correction_points(scenario):
        v = by_first.get(c)
        if v and any(d["case"] == i and d["field"] == f and d["kind"] in ("wrong_value", "missing_value") for d in v.diffs):
            add("IGNORED_EXPLICIT_CORRECTION", v, f"case {i + 1} {f} should be {val!r} after the correction")

    # SUPPRESSED_POTENTIAL_DUPLICATE
    if scenario["prior_reports"]:
        v0 = by_first.get(0)
        if v0 and (v0.action == "NOT_RELEVANT" or (not v0.out["cases"] and v0.gold["cases"])):
            add("SUPPRESSED_POTENTIAL_DUPLICATE", v0, "report dropped because it resembles a prior report")
        elif v0 and not v0.gold["potential_duplicate"]:
            for pr in scenario["prior_reports"]:
                if any(c.get("age") is not None and c.get("age") == pr.get("age") and c.get("sex") == pr.get("sex")
                       for c in v0.out["cases"]) and any(d["field"] in ("age", "sex") for d in v0.diffs):
                    add("SUPPRESSED_POTENTIAL_DUPLICATE", v0, "different child merged with the prior report")

    # FABRICATED_CONSEQUENTIAL_FIELD
    for v in valid:
        for d in v.diffs:
            if d["field"] in LOCATION and d["kind"] in ("fabricated", "should_be_null", "wrong_value"):
                add("FABRICATED_CONSEQUENTIAL_FIELD", v, f"{d['field']}: model {d['model']!r} vs expected {d['gold']!r}")
            elif d["field"] in ("age", "sex") and d["kind"] == "should_be_null" and v.action in ("CONFIRM", "ACCEPT"):
                add("FABRICATED_CONSEQUENTIAL_FIELD", v, f"{d['field']} invented and carried into {v.action}")

    # CONSEQUENTIAL_DIAGNOSIS: keyword prefilter + Jev INCORRECT
    bad_turns = {j["turn"] for j in (jev or []) if j["task"] == "non_diagnostic_behavior" and j["result"] == "INCORRECT"}
    for v in valid:
        if (v.idx + 1) in bad_turns and diagnosis_prefilter(v):
            add("CONSEQUENTIAL_DIAGNOSIS", v, "reply names a disease the sender did not mention (Jev: INCORRECT)")
    return F


def diagnosis_candidates(views: list[TurnView]) -> list[int]:
    """Turns needing Jev review (prefilter hit) — reported when Jev did not run."""
    return [v.idx + 1 for v in views if diagnosis_prefilter(v)]
