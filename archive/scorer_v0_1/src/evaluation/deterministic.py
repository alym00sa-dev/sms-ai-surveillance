"""Deterministic scorer: six 0/1/2 dimensions + per-check results (scorer contract v0.1, draft rules).

Dimension rubric -> `rubric` score; failed DIM/JEV checks from the frozen mapping can only lower a
dimension (cap); critical findings force extraction_state to 0 where the contract says so.
Thresholds are listed in THRESHOLDS and documented in SMS_AI_SURVEILLANCE_SCORER_RULES_v0_1_draft.md.
"""
from __future__ import annotations

import re
from collections import Counter

from ..benchmark.compare import _Index
from ..benchmark.location_fixture import LocationResolver  # noqa: F401  (re-export for callers)
from .context import LOCATION, TurnView, correction_points

THRESHOLDS = {"sms_chars_ok": 320, "sms_chars_max": 480, "extra_turns_partial": 1, "extra_turns_incorrect": 2,
              "jev_min_confidence": 0.5}
ORDER = {"CORRECT": 0, "PARTIAL": 1, "INCORRECT": 2}
_WORSE = lambda a, b: a if ORDER[a] >= ORDER[b] else b
_SEX_WORDS = {"male": ("boy", "male", "son"), "female": ("girl", "female", "daughter")}


# ---------------------------------------------------------------- dimensions
def score_classification(views: list[TurnView]) -> tuple[int, list[str]]:
    notes, bad, partial = [], 0, 0
    for v in views:
        if not v.first:
            continue
        if v.out is None:
            bad += 1
            notes.append(f"turn {v.idx + 1}: no valid output")
            continue
        g, m = v.gold["classification"], v.out["classification"]
        if m == g:
            continue
        if g == "AFP_SUSPECTED" and m == "HEALTH_RELATED_UNCLEAR" and v.gold["action"] == "CLARIFY":
            partial += 1
            notes.append(f"turn {v.idx + 1}: HEALTH_RELATED_UNCLEAR for incomplete AFP report (defensible)")
        else:
            bad += 1
            notes.append(f"turn {v.idx + 1}: classification {m} (expected {g})")
    return (0 if bad or partial > 1 else 1 if partial else 2), notes


def score_action(views: list[TurnView], term: str) -> tuple[int, list[str]]:
    notes, major, minor = [], 0, 0
    for v in views:
        if v.out is None:
            major += 1
            notes.append(f"turn {v.idx + 1}: no valid output")
            continue
        a, g = v.action, v.gold["action"]
        if a != g:
            if (a, g) in {("CLARIFY", "CONFIRM"), ("CONFIRM", "ACCEPT")}:
                minor += 1
                notes.append(f"turn {v.idx + 1}: {a} where {g} expected (safe but inefficient)")
            else:
                major += 1
                notes.append(f"turn {v.idx + 1}: {a} where {g} expected")
        elif "OFF_TARGET_CLARIFY" in v.events:
            minor += 1
            notes.append(f"turn {v.idx + 1}: off-target clarification")
    if term in ("PREMATURE_TERMINAL", "MAX_TURNS", "CONFIRMATION_NOT_CONVERGING", "OUTPUT_INVALID", "UNKNOWN_ACTION"):
        major += 1
        notes.append(f"scenario ended {term}")
    return (0 if major or minor > 1 else 1 if minor else 2), notes


def _gate_symptom_only(v: TurnView) -> bool:
    gd = (v.reply or {}).get("meta", {}).get("gate_diffs", [])
    return bool(gd) and all(d["kind"] == "symptom_mismatch" or d["field"] == "symptom" for d in gd)


def score_extraction(views: list[TurnView], crit_codes: set[str], term: str, jev_symptom: dict | None = None) -> tuple[int, list[str]]:
    notes = []
    valid = [v for v in views if v.out]
    if term == "OUTPUT_INVALID":
        notes.append("no valid output on the final turn")
        return 0, notes
    incorrect_conf = [v for v in views if "INCORRECT_CONFIRMATION" in v.events]
    material_conf = [v for v in valid if v.action in ("CONFIRM", "ACCEPT") and v.material]
    material_other = [v for v in valid if v.action not in ("CONFIRM", "ACCEPT") and v.material]
    final = valid[-1] if valid else None
    final_material = bool(final and final.material)
    sym = [v for v in valid if v.symptom_diffs and not v.material]
    if jev_symptom:  # Jev symptom_equivalence refines keyword symptom diffs
        sym = [v for v in sym if jev_symptom.get(v.idx + 1, "INCORRECT") != "CORRECT"]
    if crit_codes & {"FABRICATED_CONSEQUENTIAL_FIELD", "MERGED_DISTINCT_CASES", "IGNORED_EXPLICIT_CORRECTION"}:
        notes.append("critical state failure: " + ", ".join(sorted(crit_codes & {"FABRICATED_CONSEQUENTIAL_FIELD", "MERGED_DISTINCT_CASES", "IGNORED_EXPLICIT_CORRECTION"})))
        return 0, notes
    mat_conf_events = [v for v in incorrect_conf if not _gate_symptom_only(v)]
    if final_material or len(incorrect_conf) >= 2:
        notes.append("material state error persisted to the final turn" if final_material else "two or more incorrect confirmations")
        return 0, notes
    if mat_conf_events or material_conf:
        notes.append("incorrect confirmation repaired after a sender correction")
        return 1, notes
    if material_other:
        notes.append("material state error on a non-confirm turn, repaired by the end")
        return 1, notes
    if incorrect_conf or sym:
        notes.append("symptom wording differs from gold features")
        return 1, notes
    return 2, notes


def score_escalation(views: list[TurnView], gold_turns: list[dict]) -> tuple[int, list[str]]:
    notes, valid = [], [v for v in views if v.out]
    if any(v.out["priority"] == "HIGH" for v in valid):
        return 0, ["HIGH priority without a supplied rule"]
    gold_esc = [t["expected"] for t in gold_turns if t["expected"]["action"] == "ESCALATE"]
    esc = [v for v in valid if v.action == "ESCALATE"]
    if gold_esc:
        if not esc:
            return 0, ["required escalation missing"]
        o = esc[0].out
        if o["escalation"]["reason"] != gold_esc[0]["escalation_reason"] or not o["escalation"]["required"]:
            return 1, [f"escalated with reason {o['escalation']['reason']!r} (expected {gold_esc[0]['escalation_reason']!r})"]
        return 2, notes
    if esc:
        return 0, ["unnecessary escalation"]
    if any(v.action == "CLARIFY" and v.attempts_before >= 3 for v in valid):
        return 0, ["continued clarifying past the three-attempt limit"]
    if any(v.out["escalation"]["required"] or v.out["escalation"]["reason"] for v in valid):
        return 1, ["escalation metadata set without escalating"]
    return 2, notes


def score_output(views: list[TurnView], term: str) -> tuple[int, list[str]]:
    notes = []
    if term == "OUTPUT_INVALID":
        return 0, ["all attempts invalid"]
    retried = [v for v in views if len(v.attempts) > 1]
    warns = sorted({w for v in views if v.attempts and "validation" in v.attempts[-1] for w in v.attempts[-1]["validation"]["warnings"]})
    for v in views:
        if v.out and v.first and v.action == v.gold["action"] and v.out["confirmation"]["status"] != v.gold["confirmation_status"]:
            warns.append(f"turn {v.idx + 1}: confirmation.status {v.out['confirmation']['status']} (expected {v.gold['confirmation_status']})")
    if retried:
        notes.append(f"schema retry on turn(s) {[v.idx + 1 for v in retried]} (max 1)")
    notes += warns
    return (1 if retried or warns else 2), notes


# ---------------------------------------------------------------- conversation judgments (deterministic)
def _numbers(x) -> list[str]:
    return re.findall(r"\d+", str(x)) if x is not None else []


def confirmation_summary_check(v: TurnView) -> tuple[str, str]:
    text = v.out["response"].casefold()
    cases = v.out["cases"]
    wrong_sex = [c for c in cases if c.get("sex") in _SEX_WORDS and any(
        w in text for s, ws in _SEX_WORDS.items() if s != c["sex"] for w in ws) and not any(w in text for w in _SEX_WORDS[c["sex"]])]
    if wrong_sex and len(cases) == 1:
        return "INCORRECT", "summary contradicts the case sex"
    missing = []
    for c in cases:
        if c.get("age") is not None and _numbers(c["age"]) and _numbers(c["age"])[0] not in text:
            missing.append("age")
        if c.get("settlement") and re.sub(r"\b(village|town)\b", "", c["settlement"].casefold()).strip() not in text:
            missing.append("settlement")
    return ("PARTIAL", f"summary omits {sorted(set(missing))}") if missing else ("CORRECT", "")


def det_judgments(views: list[TurnView], gold_turn_count: int) -> list[dict]:
    J = []
    add = lambda task, res, v, detail="": J.append({"task": task, "result": res, "turn": v.idx + 1 if v else None, "source": "det", "detail": detail})
    for v in views:
        if not v.out:
            continue
        text = v.out["response"]
        n = len(text)
        add("sms_conciseness", "CORRECT" if n <= THRESHOLDS["sms_chars_ok"] else "PARTIAL" if n <= THRESHOLDS["sms_chars_max"] else "INCORRECT", v, f"{n} chars")
        if v.action == "CLARIFY":
            # one focused clarification = a structured target that is still needed (Jev adds the bounded semantic check)
            tgt, off = v.out["clarification"]["target"], "OFF_TARGET_CLARIFY" in v.events
            if tgt is None:
                add("clarification_target_quality", "INCORRECT", v, "CLARIFY without a structured target")
            elif off:
                add("clarification_target_quality", "PARTIAL" if v.gold["action"] == "CONFIRM" else "INCORRECT", v,
                    f"target {tgt!r} is not what the report still needs")
            else:
                add("clarification_target_quality", "CORRECT", v, f"target {tgt!r} is needed")
        if v.action == "CONFIRM":
            res, d = confirmation_summary_check(v)
            add("confirmation_fidelity", res, v, d)
        if v.action in ("ACCEPT", "ESCALATE", "OTHER_VPD", "NOT_RELEVANT") and v.out["clarification"]["target"] is not None:
            add("appropriate_stop_behavior", "PARTIAL", v, "terminal turn still carries a clarification target")
    told = sum(1 for v in views if (v.reply or {}).get("text") == "I already told you that.")
    if told:
        add("known_information_reasked", "PARTIAL" if told == 1 else "INCORRECT", None, f"{told} question(s) asked for a known fact")
    ic = sum(1 for v in views if "INCORRECT_CONFIRMATION" in v.events)
    if ic:
        add("confirmation_fidelity", "PARTIAL" if ic == 1 else "INCORRECT", None, f"{ic} incorrect confirmation(s)")
    extra = max(0, len([v for v in views if v.out]) - gold_turn_count)
    if extra:
        add("turn_efficiency", "PARTIAL" if extra < THRESHOLDS["extra_turns_incorrect"] else "INCORRECT", None, f"{extra} extra turn(s)")
    return J


def score_conversation(judgments: list[dict], term: str, crit_codes: set[str] | None = None) -> tuple[int, list[str], dict]:
    worst: dict[str, str] = {}
    for j in judgments:
        worst[j["task"]] = _WORSE(worst.get(j["task"], "CORRECT"), j["result"])
    notes = [f"{t}: {r}" for t, r in sorted(worst.items()) if r != "CORRECT"]
    crit_codes = crit_codes or set()
    if term == "OUTPUT_INVALID":
        return 0, notes + ["no usable response"], worst
    if crit_codes & {"IGNORED_EXPLICIT_CORRECTION", "MERGED_DISTINCT_CASES"}:
        return 0, notes + ["confirmation did not reflect the sender's correction or the number of children"], worst
    if term in ("MAX_TURNS", "CONFIRMATION_NOT_CONVERGING"):
        return 0, notes + [f"conversation looped ({term})"], worst
    if any(worst.get(t) == "INCORRECT" for t in ("confirmation_fidelity", "appropriate_stop_behavior", "non_diagnostic_behavior")):
        return 0, notes, worst
    inc = sum(1 for r in worst.values() if r == "INCORRECT")
    par = sum(1 for r in worst.values() if r == "PARTIAL")
    return (0 if inc >= 2 else 1 if inc == 1 or par >= 2 else 2), notes, worst


# ---------------------------------------------------------------- resolver compliance (separate metric)
def resolver_compliance(run: dict, fixture: dict) -> dict:
    ix = _Index(fixture)
    bad, n = [], 0
    for t in run["turns"]:
        if not t["output"]:
            continue
        n += 1
        lr = t["envelope"]["location_resolver"]
        issues = []
        for c in t["output"]["cases"]:
            given = {f: c.get(f) for f in LOCATION if c.get(f)}
            if lr["status"] == "UNRESOLVED" and given.get("settlement") is None and (given.get("state") or given.get("lga")):
                issues.append("location supplied while resolver UNRESOLVED")
            for m in lr["mentions"]:
                if m["status"] == "AMBIGUOUS" and any(given.get(f) for f in m["requires"]):
                    issues.append(f"guessed {m['requires']} under AMBIGUOUS")
                if m["status"] == "RESOLVED":
                    for f, val in m["resolved"].items():
                        if given.get(f) and ix.canon(given[f]) != ix.canon(val):
                            issues.append(f"{f}={given[f]!r} contradicts resolver {val!r}")
        if issues:
            bad.append({"turn": t["turn"], "issues": sorted(set(issues))})
    return {"turns_checked": n, "noncompliant_turns": len(bad), "rate": (len(bad) / n) if n else None, "details": bad}


# ---------------------------------------------------------------- frozen-mapping check rules
_ALL = ("age", "sex", "state", "lga", "settlement")


def _first(views, c):
    return next((v for v in views if v.cursor == c and v.first), None)


def _diff_rule(fields):
    def rule(ctx, c):
        v = _first(ctx["views"], c)
        if v is None or v.out is None:
            return "NOT_REACHED", None, ""
        bad = [d for d in v.diffs if d["kind"] != "symptom_mismatch" and (d["field"] in fields or d["field"] is None)]
        if bad:
            last = [x for x in ctx["views"] if x.cursor == c and x.out][-1]
            persists = any(d["kind"] != "symptom_mismatch" and (d["field"] in fields or d["field"] is None) for d in last.diffs)
            return "FAIL", (0 if persists else 1), f"{[(d['field'], d['kind']) for d in bad]}" + ("" if persists else " (repaired later)")
        sym = [d for d in v.diffs if d["field"] == "symptom"] if "symptom" in fields else []
        return ("FAIL", 1, "symptom differs from gold features") if sym else ("PASS", None, "")
    return rule


def _unaffected(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    changed = {(i, f) for cc, i, f, _ in correction_points(ctx["scenario"]) if cc == c}
    bad = [d for d in v.material if (d["case"], d["field"]) not in changed]
    return ("FAIL", 0, str(bad)) if bad else ("PASS", None, "")


def _case_count(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    return ("FAIL", 0, "case count differs") if any(d["kind"] in ("missing_case", "extra_case") for d in v.diffs) else ("PASS", None, "")


def _dup(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    ids = {p.get("case_id") for p in ctx["scenario"]["prior_reports"]}
    ok = v.out["potential_duplicate"] and ids & set(v.out["duplicate_candidate_ids"])
    return ("PASS", None, "") if ok else ("FAIL", 0, "duplicate flag/candidate id missing")


def _act_first(expected_action):
    def rule(ctx, c):
        v = _first(ctx["views"], c)
        if v is None or v.out is None:
            return "NOT_REACHED", None, ""
        return ("PASS", None, "") if v.action == expected_action else ("FAIL", 0, f"{v.action} at the correction turn")
    return rule


def _reconfirm(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    if v.gold["action"] == "ACCEPT":  # accepted only on the turn after an affirmed CONFIRM
        views = ctx["views"]
        p = views[v.idx - 1] if v.idx else None
        ok = v.action != "ACCEPT" or bool(p and p.action == "CONFIRM" and p.reply and p.reply["kind"] == "AFFIRM")
        return ("PASS", None, "") if ok else ("FAIL", 0, "ACCEPT without a confirmed re-summary")
    return ("PASS", None, "") if v.action == "CONFIRM" else ("FAIL", 0, f"{v.action} at the correction turn")


def _no_extra_clarify(ctx, c):
    at = [v for v in ctx["views"] if v.cursor == c and v.out]
    if not at:
        return "NOT_REACHED", None, ""
    n = sum(1 for v in at if v.action == "CLARIFY")
    return ("FAIL", 1 if n == 1 else 0, f"{n} unnecessary clarification(s)") if n else ("PASS", None, "")


def _no_interview(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    return ("FAIL", 0, "started an interview on an irrelevant message") if v.action == "CLARIFY" else ("PASS", None, "")


def _cls(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    return ("PASS", None, "") if v.out["classification"] == v.gold["classification"] else ("FAIL", 0, v.out["classification"])


def _no_escalate(ctx, c):
    return ("FAIL", 0, "escalated without a valid signal") if any(v.action == "ESCALATE" for v in ctx["views"]) else ("PASS", None, "")


def _limit(ctx, c):
    v = _first(ctx["views"], c)
    if v is None or v.out is None:
        return "NOT_REACHED", None, ""
    return ("FAIL", 0, "clarified past the limit") if v.action == "CLARIFY" else ("PASS", None, "")


def _jev_rule(task, extra=None):
    def rule(ctx, c):
        at = [v for v in ctx["views"] if v.cursor == c and v.out]
        if not at:
            return "NOT_REACHED", None, ""
        pre = extra(ctx, c, at) if extra else None
        if pre:
            return pre
        js = [j for j in ctx["judgments"] if j["task"] == task and j["turn"] in {v.idx + 1 for v in at} and j["source"] == "jev"]
        if not js:
            return "NOT_RUN", None, "Jev judgment not available"
        worst = max((j["result"] for j in js), key=ORDER.get)
        return ("PASS", None, "") if worst == "CORRECT" else ("FAIL", 1 if worst == "PARTIAL" else 0, f"Jev {task}: {worst}")
    return rule


def _reask_extra(ctx, c, at):
    return None


def _one_q(ctx, c, at):
    cl = [v for v in at if v.action == "CLARIFY"]
    if not cl:
        return "PASS", None, "no clarification at this turn"
    if any(v.out["clarification"]["target"] is None or "OFF_TARGET_CLARIFY" in v.events for v in cl):
        return "FAIL", 1, "clarification target missing or not what the report still needs"
    return None  # structured target is fine; Jev checks that exactly one item is asked


def _noclar(ctx, c, at):
    return None if any(v.action == "CLARIFY" for v in at) else ("PASS", None, "no clarification at this turn")


def _unnecessary(ctx, c, at):
    gold_action = at[0].gold["action"]
    if gold_action == "CONFIRM" and any(v.action == "CLARIFY" for v in at):
        return "FAIL", 1, "clarified where the report was already complete"
    return None if any(v.action == "CLARIFY" for v in at) else ("PASS", None, "no clarification at this turn")


def _confirm_only(ctx, c, at):
    return None if any(v.action == "CONFIRM" for v in at) else ("PASS", None, "no confirmation at this turn")


CHECK_RULES = {
    "must_not_drop_known_case_state": _diff_rule(_ALL + ("symptom",)),
    "must_use_conversation_memory": _diff_rule(_ALL), "must_integrate_followup_answer": _diff_rule(_ALL),
    "must_resolve_after_delayed_answer": _diff_rule(_ALL), "must_extract_from_telegraphic_text": _diff_rule(_ALL),
    "must_handle_typos": _diff_rule(_ALL), "must_not_get_distracted_by_story": _diff_rule(_ALL),
    "must_accept_reasonably_bounded_under_15_age": _diff_rule(("age",)),
    "must_preserve_age_uncertainty": _diff_rule(("age",)), "must_not_treat_irrelevant_answer_as_age": _diff_rule(("age",)),
    "must_resolve_location_from_followup": _diff_rule(tuple(LOCATION)),
    "must_not_retain_superseded_value": _diff_rule(_ALL),
    "must_preserve_unaffected_fields": _unaffected, "must_preserve_multiple_cases": _case_count,
    "must_normalize_location_for_duplicate_check": _dup,
    "must_reconfirm_after_correction": _reconfirm,
    "must_stop_clarifying_when_enough": _no_extra_clarify, "must_not_continue_clarifying_after_resolution": _no_extra_clarify,
    "must_not_start_surveillance_interview": _no_interview,
    "must_update_classification_after_new_evidence": _cls, "must_not_overclassify_afp": _cls, "must_not_overtrigger_afp": _cls,
    "must_not_escalate_without_valid_signal": _no_escalate, "must_stop_after_clarification_limit": _limit,
    "must_not_ask_unnecessary_question": _jev_rule("known_information_reasked", _unnecessary),
    "must_not_ask_for_known_location": _jev_rule("known_information_reasked", _noclar),
    "must_not_reask_location_if_reliably_inferred": _jev_rule("known_information_reasked", _noclar),
    "must_not_reask_explicitly_answered_onset": _jev_rule("known_information_reasked", _noclar),
    "must_ask_one_targeted_question": _jev_rule("clarification_target_quality", _one_q),
    "must_ignore_nonessential_details": _jev_rule("symptom_equivalence", _confirm_only),
    "must_not_hallucinate_meeting_information": _jev_rule("no_fabricated_information"),
}


def run_checks(mapping: dict, scenario: dict, views: list[TurnView], findings: list[dict], judgments: list[dict]) -> list[dict]:
    codes = {f["code"] for f in findings}
    ctx = {"scenario": scenario, "views": views, "judgments": judgments}
    out = []
    for c, t in enumerate(scenario["turns"]):
        for name in t["expected"]["critical_checks"]:
            m = mapping["checks"][name]
            if m["route"] == "CRITICAL":
                st = "FAIL" if m["code"] in codes else "PASS"
                if _first(views, c) is None:
                    st = "NOT_REACHED" if st == "PASS" else st
                out.append({"check": name, "cursor": c, "route": "CRITICAL", "code": m["code"], "status": st, "severity": 0 if st == "FAIL" else None, "detail": ""})
                continue
            status, sev, detail = CHECK_RULES[name](ctx, c)
            dim = m.get("dimension") or m.get("feeds_dimension")
            out.append({"check": name, "cursor": c, "route": m["route"], "dimension": dim, "status": status, "severity": sev, "detail": detail})
    return out


def dimension_caps(checks: list[dict]) -> dict[str, int]:
    caps: dict[str, int] = {}
    for c in checks:
        if c["status"] == "FAIL" and c["route"] != "CRITICAL" and c["severity"] is not None:
            d = c["dimension"]
            caps[d] = min(caps.get(d, 2), c["severity"])
    return caps
