import json

import pytest

from src.adapters.fake import FakeAdapter, gold_output
from src.benchmark.loader import load_benchmark
from src.benchmark.runner import run_scenario
from src.evaluation.calibration import CAL_FILE, calibrate
from src.prompts import load_bundle
from src.schemas.model_output import validate_output

SCEN = {s["id"]: s for s in load_benchmark()}
BUNDLE = load_bundle()


def test_calibration_set_agrees_with_labels():
    rows = calibrate()
    assert len(rows) >= 29
    assert [r["id"] for r in rows if r["diffs"]] == [], [(r["id"], r["diffs"]) for r in rows if r["diffs"]]
    doc = json.loads(CAL_FILE.read_text())
    assert "No live model output is used" in doc["note"] and doc["label_revisions_after_first_run"]


# ---- rule (3): schema errors vs warnings -------------------------------------------------------
GOOD = gold_output(SCEN["AFP-01"], 0)


def _with(**kw):
    out = json.loads(json.dumps(GOOD))
    for k, v in kw.items():
        if k.startswith("case_"):
            out["cases"][0][k[5:]] = v
        else:
            out[k] = v
    return out


@pytest.mark.parametrize("bad", [
    _with(action="MAYBE"), _with(classification="afp_suspected"), _with(priority="URGENT"), _with(case_sex="boy"),
    _with(case_age=7.5), _with(case_age=True), _with(other_vpd="false"), _with(cases={"case_id": "case_1"}),
    _with(case_state="N/A"), _with(case_lga=""), _with(case_settlement="null"), _with(case_symptom="none"),
    _with(escalation={"required": False, "reason": "WHATEVER"}), _with(clarification={"target": "village", "attempt_number": 0}),
    _with(confirmation={"status": "DONE"}), _with(response=None), _with(missing_information="age"),
    {k: v for k, v in GOOD.items() if k != "priority"}, {k: v for k, v in GOOD.items() if k != "location_resolution"},
    [GOOD], "text",
])
def test_invalid_enums_types_and_missing_fields_are_errors(bad):
    r = validate_output(bad)
    assert not r.ok and r.errors


def test_only_extras_and_inconsistent_combinations_are_warnings():
    r = validate_output({**GOOD, "note": "hi"})
    assert r.ok and any("extra" in w for w in r.warnings)
    r = validate_output(_with(confirmation={"status": "CONFIRMED"}))
    assert r.ok and any("confirmation.status" in w for w in r.warnings)
    r = validate_output({**GOOD, "other_vpd": True})
    assert r.ok and any("other_vpd" in w for w in r.warnings)
    clar = {**GOOD, "action": "CLARIFY", "confirmation": {"status": "PENDING"}}
    assert validate_output(clar).ok and any("NOT_READY" in w for w in validate_output(clar).warnings)
    assert validate_output(_with(case_age="about 10-11", case_sex="unknown")).ok  # valid values


# ---- rule (2): neutral/correction branches stay on the current gold node ---------------------------
def test_correction_and_neutral_branches_stay_on_the_gold_node():
    sc = SCEN["CLAR-06"]  # gold: CLARIFY(0) -> CONFIRM(1) -> ACCEPT(2)
    seq = iter([
        {**gold_output(sc, 0), "clarification": {"target": "sex", "attempt_number": 1}},          # off-target -> neutral
        gold_output(sc, 0),                                                                          # on target -> advance to node 1
        {**gold_output(sc, 1), "cases": [{**gold_output(sc, 1)["cases"][0], "age": 9}]},            # wrong confirm -> correction
        gold_output(sc, 1),                                                                          # re-confirm -> affirmation
        gold_output(sc, 2),
    ])
    res = run_scenario(FakeAdapter(lambda r: next(seq)), sc, BUNDLE)
    t = res["turns"]
    assert [x["reply"]["kind"] for x in t] == ["NEUTRAL", "ADVANCE", "CORRECTION", "AFFIRM", "TERMINATE"]
    assert [x["gold_cursor"] for x in t] == [0, 0, 1, 1, 2]           # neutral and correction replies do not move the node
    assert [x["gold_action"] for x in t] == ["CLARIFY", "CLARIFY", "CONFIRM", "CONFIRM", "ACCEPT"]
    assert t[3]["output"]["action"] == "CONFIRM" and t[3]["reply"]["text"] == "Yes, that is correct."  # re-confirmation expected after a correction
    assert res["termination"]["reason"] == "COMPLETED"


def test_accept_straight_after_a_correction_is_premature():
    sc = SCEN["CLAR-06"]
    seq = iter([gold_output(sc, 0), {**gold_output(sc, 1), "cases": [{**gold_output(sc, 1)["cases"][0], "age": 9}]}, gold_output(sc, 2)])
    res = run_scenario(FakeAdapter(lambda r: next(seq)), sc, BUNDLE)
    assert res["termination"]["reason"] == "PREMATURE_TERMINAL" and "ACCEPT_WITHOUT_CONFIRM" in res["termination"]["detail"]


# ---- rule (1): one focused clarification is judged by structure + a bounded semantic check -------------
def test_question_mark_count_is_not_used():
    from src.evaluation import deterministic
    import inspect
    assert 'count("?")' not in inspect.getsource(deterministic)
    from src.evaluation.score_run import score_scenario, load_mapping
    from src.benchmark.location_fixture import load_fixture
    from src.benchmark.symptoms import load_symptom_features
    sc = SCEN["CLAR-06"]
    def pol(req):
        out = gold_output(sc, req.context["sender"].cursor)
        if out["action"] == "CLARIFY":
            out["response"] = "Which village? Which LGA? Which state? Any landmark?"  # many '?', one structured target
        return out
    run = run_scenario(FakeAdapter(pol), sc, BUNDLE)
    res = score_scenario(sc, run, load_fixture(), load_symptom_features(), load_mapping(), None)
    tq = [j for j in res["judgments"] if j["task"] == "clarification_target_quality"]
    assert tq and all(j["result"] == "CORRECT" and j["source"] == "det" for j in tq)  # the semantic check is Jev's job
    assert res["total"] == 12


def test_calibration_exercises_all_ten_critical_codes():
    from src.schemas.score import CRITICAL_CODES
    doc = json.loads(CAL_FILE.read_text())
    seen = {c for case in doc["cases"] for c in case["expected"]["critical_failures"]}
    assert seen == set(CRITICAL_CODES), set(CRITICAL_CODES) - seen
    assert doc["calibration_version"] == "v0.2.0" and len(doc["cases"]) == 29


def test_v0_2_conversation_zero_rule_and_location_wording():
    from src.evaluation.deterministic import score_conversation
    from src.evaluation.semantic_jev import _NEEDED, TASK_BY_NAME
    j = lambda task, res: [{"task": task, "result": res, "turn": 1, "source": "jev"}]
    assert score_conversation(j("appropriate_stop_behavior", "INCORRECT"), "COMPLETED", set())[0] == 1   # mild: not 0
    assert score_conversation(j("non_diagnostic_behavior", "INCORRECT"), "COMPLETED", set())[0] == 1
    assert score_conversation(j("non_diagnostic_behavior", "INCORRECT"), "COMPLETED", {"CONSEQUENTIAL_DIAGNOSIS"})[0] == 0
    assert score_conversation(j("confirmation_fidelity", "INCORRECT"), "COMPLETED", set())[0] == 0
    two = j("appropriate_stop_behavior", "INCORRECT") + j("non_diagnostic_behavior", "INCORRECT")
    assert score_conversation(two, "COMPLETED", set())[0] == 0
    assert score_conversation([], "MAX_TURNS", set())[0] == 0
    assert "LGA" in _NEEDED["location"] and "state" in _NEEDED["location"]
    assert "several parts" in TASK_BY_NAME["clarification_target_quality"].criteria["CORRECT"]
