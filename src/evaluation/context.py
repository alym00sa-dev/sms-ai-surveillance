"""Per-turn views over a scenario run, shared by the deterministic scorer and the critical-failure detectors."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..benchmark.compare import compare_cases

LOCATION = {"state", "lga", "settlement"}
FIELDS = ("age", "sex", "state", "lga", "settlement")
TERMINAL = {"ACCEPT", "ESCALATE", "OTHER_VPD", "NOT_RELEVANT"}


@dataclass
class TurnView:
    idx: int
    cursor: int
    gold: dict
    out: dict | None
    status: str
    reply: dict | None
    first: bool                      # first model output at this gold cursor
    diffs: list[dict]                # state vs gold at this cursor (symptom included)
    attempts: list[dict]
    sender_message: str
    attempts_before: int
    events: list[str] = field(default_factory=list)

    @property
    def action(self):
        return self.out["action"] if self.out else None

    @property
    def material(self) -> list[dict]:
        return [d for d in self.diffs if d["kind"] != "symptom_mismatch"]

    @property
    def symptom_diffs(self) -> list[dict]:
        return [d for d in self.diffs if d["kind"] == "symptom_mismatch" or d["field"] == "symptom"]


def build_views(scenario: dict, run: dict, fixture: dict, symptom_features: dict) -> list[TurnView]:
    gold, seen, views = scenario["turns"], set(), []
    for t in run["turns"]:
        c, out = t["gold_cursor"], t["output"]
        first = c not in seen
        seen.add(c)
        diffs = compare_cases(out["cases"], gold[c]["expected"]["cases"], fixture, symptom_features).diffs if out else []
        reply = t["reply"]
        views.append(TurnView(
            idx=t["turn"] - 1, cursor=c, gold=gold[c]["expected"], out=out, status=t["status"], reply=reply,
            first=first, diffs=diffs, attempts=t["attempts"], sender_message=t["sender_message"],
            attempts_before=t["clarification_attempts_before"], events=(reply or {}).get("events", [])))
    return views


def correction_points(scenario: dict) -> list[tuple[int, int, str, object]]:
    """Gold-defined corrections: (cursor, case index, field, new value) where a non-null value changes to another."""
    pts, gold = [], scenario["turns"]
    for c in range(1, len(gold)):
        prev, cur = gold[c - 1]["expected"]["cases"], gold[c]["expected"]["cases"]
        for i, (p, q) in enumerate(zip(prev, cur)):
            for f in FIELDS:
                if p.get(f) is not None and q.get(f) is not None and p[f] != q[f]:
                    pts.append((c, i, f, q[f]))
    return pts
