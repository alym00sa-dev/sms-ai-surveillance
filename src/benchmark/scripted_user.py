"""Deterministic, state-aware scripted sender (no LLM user simulator in v1).

Policy
  * Advance the script only when the model's action is the expected one for the current gold turn.
  * Off-target or unnecessary questions get a neutral, information-free reply and do not advance.
  * An affirmative confirmation is sent only when the model's interpreted state is materially correct.
  * An incorrect confirmation gets a deterministic correction built from the gold diff.
  * A terminal action that is not the expected terminal ends the scenario (PREMATURE_TERMINAL).
  * A hard cap on model turns ends runaway conversations (MAX_TURNS).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .compare import compare_cases
from .symptoms import extract_features

TERMINAL = {"ACCEPT", "ESCALATE", "OTHER_VPD", "NOT_RELEVANT"}
ALREADY_TOLD = "I already told you that."
DONT_KNOW = "I don't know."

_FAMILY = {
    "age": "age", "sex": "sex", "symptom": "symptom", "symptom_detail": "symptom", "sudden_onset": "symptom",
    "location": "location", "state": "location", "lga": "location", "settlement": "location",
    "unambiguous_location": "location", "specific_location": "location", "case_identity": "location",
}


@dataclass
class Reply:
    kind: str                      # ADVANCE | AFFIRM | CORRECTION | NEUTRAL | TERMINATE
    text: str | None = None
    reason: str | None = None      # termination reason
    detail: str | None = None
    events: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


class ScriptedUser:
    def __init__(self, scenario: dict, fixture: dict | None = None, max_extra_turns: int = 3,
                 max_corrections: int = 2):
        self.turns = scenario["turns"]
        self.fixture = fixture
        self.max_model_turns = len(self.turns) + max_extra_turns
        self.max_corrections = max_corrections
        self.cursor = 0
        self.model_turns = 0
        self.corrections = 0
        self.clarification_attempts = 0
        self.last_action: str | None = None
        self.last_reply_kind: str | None = None
        self.terminated: Reply | None = None

    # ---- accessors ------------------------------------------------------
    @property
    def first_message(self) -> str:
        return self.turns[0]["user"]

    @property
    def expected(self) -> dict:
        return self.turns[self.cursor]["expected"]

    # ---- main entry -----------------------------------------------------
    def respond(self, out: dict) -> Reply:
        if self.terminated:
            raise RuntimeError("scenario already terminated")
        self.model_turns += 1
        action, gold = out.get("action"), self.expected
        prev, self.last_action = self.last_action, action
        prev_reply = self.last_reply_kind
        reply = self._decide(out, action, gold, prev, prev_reply)
        self.last_reply_kind = reply.kind
        if reply.kind != "TERMINATE" and self.model_turns >= self.max_model_turns:
            reply = Reply("TERMINATE", reason="MAX_TURNS", detail=f"cap={self.max_model_turns}")
        if reply.kind == "TERMINATE":
            self.terminated = reply
        return reply

    def _decide(self, out, action, gold, prev, prev_reply=None) -> Reply:
        last = self.cursor == len(self.turns) - 1
        if action in TERMINAL:
            if last and action == gold["action"]:
                return Reply("TERMINATE", reason="COMPLETED")
            unconfirmed = action == "ACCEPT" and (prev != "CONFIRM" or prev_reply != "AFFIRM")  # the sender has not affirmed the latest summary
            detail = "ACCEPT_WITHOUT_CONFIRM" if unconfirmed else f"expected={gold['action']}"
            return Reply("TERMINATE", reason="PREMATURE_TERMINAL", detail=f"{action}; {detail}")
        if action == "CONFIRM":
            return self._on_confirm(out, gold)
        if action == "CLARIFY":
            return self._on_clarify(out, gold)
        return Reply("TERMINATE", reason="UNKNOWN_ACTION", detail=str(action))

    # ---- CONFIRM --------------------------------------------------------
    def _on_confirm(self, out, gold) -> Reply:
        cmp = compare_cases(out.get("cases"), gold["cases"], self.fixture)
        meta = {"model_symptom_features": [extract_features(c.get("symptom")) for c in out.get("cases") or []],
                "gate_diffs": cmp.diffs}
        if not cmp.ok:
            if self.corrections >= self.max_corrections:
                return Reply("TERMINATE", reason="CONFIRMATION_NOT_CONVERGING", detail=str(cmp.diffs))
            self.corrections += 1
            return Reply("CORRECTION", self._correction_text(cmp.diffs, gold["cases"]),
                         events=["INCORRECT_CONFIRMATION"], meta=meta)
        if gold["action"] == "CONFIRM":
            reply = self._advance()
            reply.meta = meta
            return reply
        if gold["action"] == "ACCEPT":  # sender already affirmed; resend the affirmation
            return Reply("AFFIRM", self.turns[self.cursor]["user"], events=["REPEATED_CONFIRM"], meta=meta)
        return Reply("NEUTRAL", DONT_KNOW, events=["PREMATURE_CONFIRM"], meta=meta)

    # ---- CLARIFY --------------------------------------------------------
    def _on_clarify(self, out, gold) -> Reply:
        target = (out.get("clarification") or {}).get("target")
        fam = _FAMILY.get(target, "other")
        wanted = {_FAMILY.get(m) for m in gold["missing_important_fields"]}
        if gold["action"] == "CLARIFY" and fam in wanted:
            nxt = self.turns[self.cursor + 1]["expected"] if self.cursor + 1 < len(self.turns) else None
            unresolved = (nxt is None or nxt["action"] in {"ESCALATE", "NOT_RELEVANT"}
                          or fam in {_FAMILY.get(m) for m in nxt["missing_important_fields"]})
            self.clarification_attempts += unresolved
            return self._advance()
        self.clarification_attempts += 1
        known = self._known(fam, gold["cases"])
        return Reply("NEUTRAL", ALREADY_TOLD if known else DONT_KNOW, events=["OFF_TARGET_CLARIFY"])

    @staticmethod
    def _known(fam: str, cases: list[dict]) -> bool:
        keys = {"age": ("age",), "sex": ("sex",), "symptom": ("symptom",),
                "location": ("settlement", "lga", "state")}.get(fam, ())
        return any(c.get(k) is not None for c in cases for k in keys)

    def _advance(self) -> Reply:
        if self.cursor + 1 >= len(self.turns):
            return Reply("TERMINATE", reason="SCRIPT_EXHAUSTED")
        self.cursor += 1
        nxt = self.turns[self.cursor]
        kind = "AFFIRM" if nxt["expected"]["confirmation_status"] == "CONFIRMED" else "ADVANCE"
        return Reply(kind, nxt["user"])

    # ---- correction text ------------------------------------------------
    @staticmethod
    def _correction_text(diffs: list[dict], gold_cases: list[dict]) -> str:
        label = {"state": "state", "lga": "LGA", "settlement": "village", "age": "age", "sex": "sex",
                 "symptom": "symptom"}
        ordinal = ["first", "second", "third", "fourth"]
        multi = len(gold_cases) > 1
        parts = []
        for d in diffs:
            who = f"For the {ordinal[d['case']]} child: " if multi and d["case"] is not None else ""
            word = {"male": "boy", "female": "girl"}
            if d["kind"] == "missing_case":
                parts.append(f"{len(gold_cases)} children were reported: " + "; ".join(
                    f"a {word.get(c.get('sex'), 'child')}" + (f" aged {c['age']}" if c.get("age") is not None else "")
                    for c in gold_cases) + ".")
            elif d["kind"] == "extra_case":
                parts.append(f"Only {len(gold_cases)} child{'ren were' if len(gold_cases) != 1 else ' was'} reported.")
            elif d["kind"] == "should_be_null":
                parts.append(f"{who}I do not know the {label[d['field']]}.")
            elif d["field"] == "sex":
                parts.append(f"{who}It is a {word[d['gold']]}.")
            else:
                parts.append(f"{who}The {label[d['field']]} is {d['gold']}.")
        return "No, that is not correct. " + " ".join(dict.fromkeys(parts)) if parts else "No, that is not correct."
