import copy

import pytest

from src.benchmark.loader import load_benchmark
from src.benchmark.scripted_user import ALREADY_TOLD, DONT_KNOW, ScriptedUser

SCEN = {s["id"]: s for s in load_benchmark()}


def gold_output(sc, i):
    e = sc["turns"][i]["expected"]
    cases = [{**{k: None for k in ("age", "sex", "state", "lga", "settlement", "symptom")}, **c} for c in e["cases"]]
    return {"classification": e["classification"], "action": e["action"], "cases": cases,
            "clarification": {"target": e["clarification_target"]}}


def drive(sc, model, **kw):
    """model(user_message, turn_index) -> structured output. Returns (user, transcript)."""
    u = ScriptedUser(sc, **kw)
    msg, log = u.first_message, []
    for n in range(50):
        out = model(msg, n, u)
        r = u.respond(out)
        log.append((msg, out["action"], r))
        if r.kind == "TERMINATE":
            return u, log
        msg = r.text
    raise AssertionError("runaway")


@pytest.mark.parametrize("sid", sorted(SCEN))
def test_oracle_completes_every_scenario(sid):
    sc = SCEN[sid]
    u, log = drive(sc, lambda m, n, u: gold_output(sc, u.cursor))
    assert log[-1][2].reason == "COMPLETED"
    assert [a for _, a, _ in log] == [t["expected"]["action"] for t in sc["turns"]]
    assert [m for m, _, _ in log] == [t["user"] for t in sc["turns"]]


def test_attempt_counting():
    for sid in ("ESC-23", "ESC-24"):
        u, _ = drive(SCEN[sid], lambda m, n, u, sid=sid: gold_output(SCEN[sid], u.cursor))
        assert u.clarification_attempts == 3
    u, _ = drive(SCEN["CLAR-10"], lambda m, n, u: gold_output(SCEN["CLAR-10"], u.cursor))
    assert u.clarification_attempts == 1  # the "Her mother is Aisha" reply


def test_premature_accept_terminates():
    sc = SCEN["AFP-01"]
    u, log = drive(sc, lambda m, n, u: {**gold_output(sc, 1), "action": "ACCEPT"})
    r = log[-1][2]
    assert len(log) == 1 and r.reason == "PREMATURE_TERMINAL" and "ACCEPT_WITHOUT_CONFIRM" in r.detail


def test_wrong_terminal_terminates():
    sc = SCEN["AFP-01"]
    _, log = drive(sc, lambda m, n, u: {**gold_output(sc, 0), "action": "ESCALATE"})
    assert log[-1][2].reason == "PREMATURE_TERMINAL"
    sc = SCEN["VPD-19"]
    _, log = drive(sc, lambda m, n, u: {**gold_output(sc, 0), "action": "NOT_RELEVANT"})
    assert log[-1][2].reason == "PREMATURE_TERMINAL"


def test_incorrect_confirmation_is_corrected_not_affirmed():
    sc = SCEN["CLAR-12"]  # girl's age must become 8
    def model(m, n, u):
        out = gold_output(sc, u.cursor)
        if u.cursor == 1 and n < 3:
            out = copy.deepcopy(out)
            out["cases"][1]["age"] = 9  # ignores the sender's correction
        return out
    u, log = drive(sc, model)
    kinds = [r.kind for _, _, r in log]
    assert "CORRECTION" in kinds and "AFFIRM" in kinds and kinds.index("CORRECTION") < kinds.index("AFFIRM")
    corr = next(r for _, _, r in log if r.kind == "CORRECTION")
    assert "second child" in corr.text and "age is 8" in corr.text and "INCORRECT_CONFIRMATION" in corr.events
    assert log[-1][2].reason == "COMPLETED"


def test_merged_children_corrected():
    sc = SCEN["CLAR-12"]
    def model(m, n, u):
        out = gold_output(sc, u.cursor)
        if u.cursor == 1 and n < 3:
            out["cases"] = out["cases"][:1]
        return out
    _, log = drive(sc, model)
    corr = next(r for _, _, r in log if r.kind == "CORRECTION")
    assert "2 children were reported" in corr.text and "girl aged 8" in corr.text


def test_fabricated_field_not_affirmed_and_not_converging():
    sc = SCEN["CLAR-06"]  # model confirms with an invented age while age is unresolved? gold age 8 given;
    # use CLAR-09: ambiguous Kura, model guesses Kano then confirms
    sc = SCEN["CLAR-09"]
    def model(m, n, u):
        out = gold_output(sc, u.cursor)
        out["action"] = "CONFIRM"
        out["cases"][0].update(state="Kano", lga="Kura")
        return out
    u, log = drive(sc, model)
    assert log[0][2].kind == "CORRECTION" and "do not know the" in log[0][2].text
    assert log[-1][2].reason == "CONFIRMATION_NOT_CONVERGING"


def test_off_target_question_gets_no_new_information():
    sc = SCEN["CLAR-06"]  # gold missing: location; model asks sex (already known)
    def model(m, n, u):
        if n == 0:
            return {**gold_output(sc, 0), "clarification": {"target": "sex"}}
        return gold_output(sc, u.cursor)
    u, log = drive(sc, model)
    r = log[0][2]
    assert r.kind == "NEUTRAL" and r.text == ALREADY_TOLD and "OFF_TARGET_CLARIFY" in r.events
    assert log[1][0] == ALREADY_TOLD and u.clarification_attempts >= 1


def test_unnecessary_question_not_rewarded():
    sc = SCEN["AFP-01"]  # complete report; model asks for the age instead of confirming
    def model(m, n, u):
        return {**gold_output(sc, 0), "action": "CLARIFY", "clarification": {"target": "age"}} if n == 0 \
            else gold_output(sc, u.cursor)
    u, log = drive(sc, model)
    assert log[0][2].text == ALREADY_TOLD and u.cursor == 1 and log[-1][2].reason == "COMPLETED"
    # unknown info -> "I don't know."
    sc = SCEN["CLAR-06"]
    _, log = drive(sc, lambda m, n, u: {**gold_output(sc, 0), "clarification": {"target": "other"}})
    assert log[0][2].text == DONT_KNOW


def test_wanted_family_is_any_missing_field():
    sc = SCEN["CLAR-13"]  # missing age AND specific location: either question is on target
    for tgt in ("age", "location"):
        u, log = drive(sc, lambda m, n, u: {**gold_output(sc, u.cursor), "clarification": {"target": tgt}})
        assert log[0][2].kind == "ADVANCE" and log[0][2].text == sc["turns"][1]["user"]


def test_max_turn_cap():
    sc = SCEN["ESC-24"]  # never escalates, keeps asking about location
    u, log = drive(sc, lambda m, n, u: gold_output(SCEN["ESC-24"], 0))
    assert log[-1][2].reason == "MAX_TURNS" and len(log) == u.max_model_turns == 7


def test_clarify_after_correct_confirm_gets_neutral():
    sc = SCEN["AFP-01"]
    seq = iter([gold_output(sc, 0), {**gold_output(sc, 1), "action": "CLARIFY", "clarification": {"target": "age"}},
                gold_output(sc, 1)])
    _, log = drive(sc, lambda m, n, u: next(seq))
    assert log[1][2].kind == "NEUTRAL" and log[-1][2].reason == "COMPLETED"


def test_one_field_correction_reconfirm_affirmation():
    """One wrong field -> targeted correction -> corrected re-confirm -> affirmation -> ACCEPT."""
    sc = SCEN["CLAR-06"]  # CLARIFY (location) -> CONFIRM -> ACCEPT; gold: 8 y/o boy in Majawa
    outs = iter([
        gold_output(sc, 0),                                              # CLARIFY location
        {**gold_output(sc, 1), "cases": [{**gold_output(sc, 1)["cases"][0], "age": 9}]},  # CONFIRM, age wrong
        gold_output(sc, 1),                                              # CONFIRM corrected
        gold_output(sc, 2),                                              # ACCEPT
    ])
    u, log = drive(sc, lambda m, n, u: next(outs))
    kinds = [r.kind for _, _, r in log]
    assert kinds == ["ADVANCE", "CORRECTION", "AFFIRM", "TERMINATE"]
    correction = log[1][2]
    assert correction.text == "No, that is not correct. The age is 8."  # only the wrong field is mentioned
    assert correction.events == ["INCORRECT_CONFIRMATION"]
    assert [d["field"] for d in correction.meta["gate_diffs"]] == ["age"]
    assert log[2][0] == correction.text and log[2][2].text == "Yes, that is correct."
    assert log[3][1] == "ACCEPT" and log[3][2].reason == "COMPLETED"
    assert u.corrections == 1 and u.cursor == 2


def test_symptom_gate_blocks_affirmation_and_logs_features():
    sc = SCEN["AFP-02"]  # gold: sudden inability to use left leg
    def model(m, n, u):
        out = gold_output(sc, u.cursor)
        if n == 0:
            out["cases"][0]["symptom"] = "sudden weakness in the right leg"
        return out
    _, log = drive(sc, model)
    first = log[0][2]
    assert first.kind == "CORRECTION" and first.text == "No, that is not correct. The symptom is sudden inability to use left leg."
    assert first.meta["model_symptom_features"][0]["laterality"] == ["one", "right"]
    assert first.meta["gate_diffs"][0]["kind"] == "symptom_mismatch"
    assert log[1][2].kind == "AFFIRM" and log[-1][2].reason == "COMPLETED"


def test_paraphrased_symptom_is_accepted():
    sc = SCEN["AFP-02"]
    def model(m, n, u):
        out = gold_output(sc, u.cursor)
        out["cases"][0]["symptom"] = "cannot use her left leg since this morning"
        return out
    _, log = drive(sc, model)
    assert [r.kind for _, _, r in log] == ["AFFIRM", "TERMINATE"]
    assert log[0][2].meta["model_symptom_features"][0] == {"body_region": ["leg"], "laterality": ["left", "one"], "onset": "sudden"}


def test_missing_symptom_in_confirmation_is_corrected():
    sc = SCEN["AFP-01"]
    seq = iter([{**gold_output(sc, 0), "cases": [{**gold_output(sc, 0)["cases"][0], "symptom": None}]},
                gold_output(sc, 0), gold_output(sc, 1)])
    _, log = drive(sc, lambda m, n, u: next(seq))
    assert log[0][2].kind == "CORRECTION" and "symptom" in log[0][2].text
