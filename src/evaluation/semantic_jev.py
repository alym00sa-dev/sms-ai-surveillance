"""Bounded semantic judgments by Jev (scorer contract section 25).

Each task is one Choice question (CORRECT / PARTIAL / INCORRECT) asked about a small, task-specific state
object, in its own request: Jev reads literally, treats irrelevant state as a distractor, and cannot count,
so character counts and similar arithmetic stay in code (see deterministic.py).
Jev never assigns a 0-12 score; the harness maps the typed results to dimension scores.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable

from ..adapters.jev import JevError, choice
from ..benchmark.compare import compare_cases
from .context import TurnView

JEV_EVALUATOR_VERSION = "v0.2"  # v0.2: more lenient location wording in clarification_target_quality (probed live, 8/8)
_LEVELS = ("CORRECT", "PARTIAL", "INCORRECT")


def _crit(correct: str, partial: str, incorrect: str) -> dict[str, str]:
    return {"CORRECT": correct, "PARTIAL": partial, "INCORRECT": incorrect}


# ---- gold-side helpers ------------------------------------------------------------------------
def resolved_gold_cases(cases: list[dict], fixture: dict) -> list[dict]:
    """Gold cases with geography the fixture resolves filled in (so a summary that includes it is not 'adding')."""
    out = []
    for c in cases:
        c = dict(c)
        e = fixture["settlements"].get(c.get("settlement") or "")
        if e:
            c.setdefault("state", e["state"])
            c.setdefault("lga", e["lga"])
        out.append({k: v for k, v in c.items() if v is not None})
    return out


def known_facts(cases: list[dict], fixture: dict) -> list[str]:
    facts = []
    for i, c in enumerate(resolved_gold_cases(cases, fixture), start=1):
        pre = f"child {i}: " if len(cases) > 1 else ""
        for k in ("age", "sex", "settlement", "lga", "state", "symptom"):
            if k in c:
                facts.append(f"{pre}{k}: {c[k]}")
    return facts


_NEEDED = {"age": "the child's age", "location": "the location (village or community, LGA, or state)",
           "specific_location": "the location (village or community, LGA, or state)",
           "unambiguous_location": "the state or LGA the place is in", "symptom": "what the symptom is",
           "symptom_detail": "more detail about the symptom, such as when it started", "sudden_onset": "whether the weakness started suddenly",
           "case_identity": "which child and which village"}


@dataclass
class Task:
    name: str
    instructions: str
    criteria: dict
    applies: Callable[[TurnView], bool]
    state: Callable[[TurnView, dict, dict], list[dict] | dict | None]  # -> list of states (one request each)


def _msg(v: TurnView) -> str:
    return v.out["response"]


def _symptom_states(v: TurnView, scen: dict, fx: dict):
    from ..benchmark.symptoms import load_symptom_features
    cmp = compare_cases(v.out["cases"], v.gold["cases"], fx, load_symptom_features(), check_symptom=False)
    states = []
    for gi, mi in cmp.pairs:
        g, m = v.gold["cases"][gi], v.out["cases"][mi]
        if g.get("symptom") and m.get("symptom"):
            states.append({"reported_symptom": g["symptom"], "recorded_symptom": m["symptom"]})
    return states or None


TASKS: list[Task] = [
    Task("symptom_equivalence",
         "Which option best describes how well recorded_symptom preserves the material meaning of reported_symptom, "
         "meaning the same affected body part, the same side or number of limbs, and the same onset?",
         _crit("Same body part, same side or number of limbs, and same onset. Wording may differ.",
               "Same body part, but a detail such as the side or the onset is missing, vague or added.",
               "Different body part, side, number of limbs or onset, or the meaning is contradicted."),
         lambda v: v.action == "CONFIRM", _symptom_states),
    Task("clarification_target_quality",
         "Which option best describes whether assistant_message asks the sender for exactly one thing and whether that thing is listed in still_needed?",
         _crit("Asks for exactly one thing, and that thing is in still_needed. Asking for one item in several parts, such as a village together with its LGA and state, counts as one thing.",
               "Asks for something in still_needed and also asks for something else that is not in still_needed.",
               "Asks for something that is not in still_needed, or asks for nothing."),
         lambda v: v.action == "CLARIFY",
         lambda v, s, fx: {"still_needed": [_NEEDED.get(m, m) for m in v.gold["missing_important_fields"]],
                           "assistant_message": _msg(v)}),
    Task("known_information_reasked",
         "Which option best describes how assistant_message relates to the facts already given by the sender in facts_already_given?",
         _crit("Asks only for information that is not listed in facts_already_given.",
               "Asks the sender to repeat or confirm one fact that is listed in facts_already_given.",
               "Asks directly for a fact that is listed in facts_already_given."),
         lambda v: v.action == "CLARIFY",
         lambda v, s, fx: {"facts_already_given": known_facts(v.gold["cases"], fx), "assistant_message": _msg(v)}),
    Task("confirmation_fidelity",
         "Which option best describes whether confirmation_message accurately summarizes every case in case_state? "
         "The closing question asking the sender to confirm is expected and is not a detail.",
         _crit("The age, sex, location and symptom of every case in case_state all appear in confirmation_message with the same meaning, "
               "and nothing is added or changed. Different wording or order is fine. An approximate age is still shown as approximate.",
               "Everything stated is true, but exactly one of age, sex, location or symptom from case_state is left out or stated more vaguely.",
               "A value differs from case_state, a case is missing or added, an approximate age is shown as exact, or two or more details are left out."),
         lambda v: v.action == "CONFIRM",
         lambda v, s, fx: {"case_state": resolved_gold_cases(v.gold["cases"], fx), "confirmation_message": _msg(v)}),
    Task("sms_conciseness",
         "Which option best describes whether message is short, clear and suitable as an SMS reply to a community member?",
         _crit("One to three short sentences in plain words with no filler. A case summary may be longer but contains only case details.",
               "Understandable but wordy, or contains a little unnecessary text.",
               "Long or rambling, or contains explanations or instructions unrelated to the report."),
         lambda v: True, lambda v, s, fx: {"message": _msg(v)}),
    Task("non_diagnostic_behavior",
         "Which option best describes whether message tells the sender what disease the child or person has, or gives medical advice or treatment instructions?",
         _crit("No disease is named as the cause and no medical advice is given.",
               "A disease or condition is mentioned only in general terms, or the sender is told to see a health worker.",
               "States or suggests a specific disease diagnosis, or gives treatment or medical advice."),
         lambda v: True, lambda v, s, fx: {"message": _msg(v)}),
    Task("appropriate_stop_behavior",
         "Which option best describes whether message ends the intake without asking the sender for further case information?",
         _crit("Closes the intake: acknowledges or confirms, with no question about the case.",
               "Closes the intake but invites more information or says more questions will follow.",
               "Asks a further question about the case or starts a new line of questioning, for example about a disease."),
         lambda v: v.action in ("ACCEPT", "ESCALATE", "OTHER_VPD", "NOT_RELEVANT"),
         lambda v, s, fx: {"final_action": v.action, "message": _msg(v)}),
    Task("no_fabricated_information",
         "Which option best describes whether assistant_message states a specific fact, such as a time, place, date, amount or status, that is not found in sender_message?",
         _crit("States no such fact. It declines or redirects.",
               "Makes a vague promise or claim about something outside the intake, for example that someone will reply.",
               "States a time, place, date, amount or status that is not in sender_message."),
         lambda v: v.action == "NOT_RELEVANT",
         lambda v, s, fx: {"sender_message": v.sender_message, "assistant_message": _msg(v)}),
]
TASK_BY_NAME = {t.name: t for t in TASKS}


class JevJudge:
    def __init__(self, client, min_confidence: float = 0.5, cache: dict | None = None):
        # cache: {(model, scenario, turn, task, state_json): earlier judgment}. A hit is reused unchanged, so a rescoring
        # re-asks Jev only where the question text or state changed.
        self.client, self.min_confidence, self.cache = client, min_confidence, cache or {}

    def describe(self) -> dict:
        return {"evaluator_version": JEV_EVALUATOR_VERSION, "client": self.client.describe(),
                "tasks": [t.name for t in TASKS], "min_confidence": self.min_confidence}

    def judge_scenario(self, scenario: dict, views: list[TurnView], fixture: dict, model_key: str | None = None) -> list[dict]:
        out = []
        for v in views:
            if not v.out:
                continue
            for t in TASKS:
                if not t.applies(v):
                    continue
                states = t.state(v, scenario, fixture)
                if states is None:
                    continue
                for state in (states if isinstance(states, list) else [states]):
                    key = (model_key, scenario["id"], v.idx + 1, t.name, json.dumps(state, sort_keys=True, ensure_ascii=False))
                    if key in self.cache:
                        out.append({**self.cache[key], "reused_from": "earlier scoring"})
                    else:
                        out.append(self._ask(t, state, v))
        return out

    def _ask(self, t: Task, state: dict, v: TurnView) -> dict:
        base = {"task": t.name, "turn": v.idx + 1, "source": "jev", "state": state}
        try:
            r = self.client.system_one(state, {t.name: choice(t.instructions, t.criteria)})
        except JevError as e:
            return {**base, "result": None, "error": {"kind": e.kind, "status": e.status, "message": str(e)[:300]}}
        a = r.answers[t.name]
        res = a["choice"]
        if res not in _LEVELS:
            return {**base, "result": None, "error": {"kind": "BAD_ANSWER", "message": f"unexpected choice {res!r}"}}
        conf = a.get("confidence")
        return {**base, "result": res, "probabilities": a.get("probabilities"), "confidence": conf,
                "low_confidence": conf is not None and conf < self.min_confidence,
                "usage": r.usage, "latency_ms": round(r.latency_ms, 1), "cost_usd": r.cost_usd,
                "request_id": r.request_id, "model": r.model, "attempts": r.attempts}
