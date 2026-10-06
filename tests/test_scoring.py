import copy
import json

import pytest

from src.adapters.base import AdapterError
from src.adapters.fake import FakeAdapter, gold_output, oracle_adapter
from src.adapters.jev import FakeJevClient, JevClient, JevError
from src.benchmark.loader import DEFAULT_BENCHMARK, load_benchmark
from src.benchmark.location_fixture import load_fixture
from src.benchmark.runner import run_benchmark, run_scenario
from src.benchmark.symptoms import load_symptom_features
from src.evaluation.aggregate import aggregate, compare_architectures
from src.evaluation.deterministic import CHECK_RULES
from src.evaluation.score_run import load_mapping, score_run, score_scenario
from src.evaluation.semantic_jev import TASKS, JevJudge
from src.prompts import load_bundle
from src.reporting.results import write_report
from src.reporting.tables import aggregate_table, architecture_table
from src.schemas.score import CRITICAL_CODES

SCEN = {s["id"]: s for s in load_benchmark()}
BUNDLE, FX, SF, MAP = load_bundle(), load_fixture(), load_symptom_features(), load_mapping()


def go(sid, i):
    return gold_output(SCEN[sid], i)


def score(sid, policy, judge=None, **kw):
    run = run_scenario(FakeAdapter(policy, **kw), SCEN[sid], BUNDLE)
    return score_scenario(SCEN[sid], run, FX, SF, MAP, judge), run


def oracle_policy(sid, override=None):
    def p(req):
        s = req.context["sender"]
        out = gold_output(SCEN[sid], s.cursor)
        return (override(out, s, req) if override else out)
    return p


def codes(res):
    return set(res["score"]["critical_failures"])


@pytest.mark.parametrize("sid", sorted(SCEN))
def test_oracle_scores_perfect(sid):
    res, _ = score(sid, oracle_policy(sid))
    assert res["status"] == "SCORED" and res["total"] == 12 and not codes(res), res["notes"]
    assert res["provisional"] and res["provisional_reasons"] == ["Jev not run"]
    assert not [c for c in res["checks"] if c["status"] == "FAIL"]


def test_every_mapped_check_has_a_rule_and_all_codes_covered():
    non_crit = {k for k, v in MAP["checks"].items() if v["route"] != "CRITICAL"}
    assert non_crit == set(CHECK_RULES)
    assert {v["code"] for v in MAP["checks"].values() if v["route"] == "CRITICAL"} == set(CRITICAL_CODES)


def test_premature_accept_is_critical():
    res, run = score("AFP-01", lambda r: go("AFP-01", 1))
    assert "ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION" in codes(res) and res["scores"]["action"] == 0
    assert run["termination"]["reason"] == "PREMATURE_TERMINAL"


def test_ignored_correction_is_critical_even_if_harness_repairs_it():
    def ov(out, s, req):
        if s.cursor == 2 and s.corrections == 0:
            out["cases"][0]["sex"] = "male"
        return out
    res, run = score("CLAR-11", oracle_policy("CLAR-11", ov))
    assert "IGNORED_EXPLICIT_CORRECTION" in codes(res) and res["scores"]["extraction_state"] == 0
    assert run["termination"]["reason"] == "COMPLETED"  # the harness corrected it; the score still records the failure


def test_merged_children_critical():
    def ov(out, s, req):
        if s.cursor == 1 and s.corrections == 0:
            out["cases"] = out["cases"][:1]
        return out
    res, _ = score("CLAR-12", oracle_policy("CLAR-12", ov))
    assert "MERGED_DISTINCT_CASES" in codes(res) and res["scores"]["extraction_state"] == 0


def test_guessing_ambiguous_location_is_fabrication():
    def ov(out, s, req):
        out["cases"][0].update(state="Kano", lga="Kura")
        return out
    res, _ = score("CLAR-09", oracle_policy("CLAR-09", ov))
    assert "FABRICATED_CONSEQUENTIAL_FIELD" in codes(res) and res["scores"]["extraction_state"] == 0


def test_no_escalation_is_critical_and_loops():
    res, run = score("ESC-24", lambda r: go("ESC-24", 0))
    assert "FAILED_REQUIRED_ESCALATION" in codes(res)
    assert res["scores"]["escalation_priority"] == 0 and res["scores"]["conversation_quality"] == 0
    assert run["termination"]["reason"] == "MAX_TURNS"


def test_unnecessary_escalation_is_not_critical():
    def ov(out, s, req):
        if s.cursor == 3:
            out.update(action="ESCALATE", escalation={"required": True, "reason": "FAILED_CLARIFICATION_WITH_VALID_SIGNAL"})
        return out
    res, _ = score("ESC-23", oracle_policy("ESC-23", ov))
    assert res["scores"]["escalation_priority"] == 0 and not codes(res) and res["scores"]["action"] == 0


def test_escalation_reason_mismatch_is_partial():
    def ov(out, s, req):
        if out["action"] == "ESCALATE":
            out["escalation"]["reason"] = "AMBIGUOUS_LOCATION"
        return out
    res, _ = score("ESC-25", oracle_policy("ESC-25", ov))
    assert res["scores"]["escalation_priority"] == 1 and not codes(res)


def test_high_priority_invented():
    res, _ = score("AFP-01", oracle_policy("AFP-01", lambda o, s, r: {**o, "priority": "HIGH"}))
    assert res["scores"]["escalation_priority"] == 0


def test_schema_retry_and_invalid_output_scoring():
    n = {"i": 0}
    def p(req):
        n["i"] += 1
        return "garbage" if n["i"] == 1 else go("AFP-01", req.context["sender"].cursor)
    res, _ = score("AFP-01", p)
    assert res["scores"]["output_adherence"] == 1 and res["total"] == 11
    res, run = score("AFP-01", lambda r: "garbage")
    assert run["termination"]["reason"] == "OUTPUT_INVALID" and res["scores"]["output_adherence"] == 0
    assert res["status"] == "SCORED" and res["scores"]["classification"] == 0 and res["scores"]["extraction_state"] == 0


def test_infra_error_is_unscored_and_excluded():
    res, _ = score("AFP-01", lambda r: AdapterError("INFRA_SERVER", "x", 529))
    assert res["status"] == "UNSCORED_INFRA"
    good, _ = score("AFP-02", oracle_policy("AFP-02"))
    agg = aggregate([res, good])
    assert agg["scenarios_scored"] == 1 and agg["quality"] == {"total": 12, "max": 12} and agg["unscored_infra"] == ["AFP-01"]


def test_missed_afp_and_other_vpd_routing():
    res, _ = score("AFP-01", oracle_policy("AFP-01", lambda o, s, r: {**o, "classification": "NOT_RELEVANT", "action": "NOT_RELEVANT", "cases": []}))
    assert "MISSED_CREDIBLE_AFP" in codes(res) and res["scores"]["classification"] == 0
    res, _ = score("VPD-19", oracle_policy("VPD-19", lambda o, s, r: {**o, "classification": "NOT_RELEVANT", "action": "NOT_RELEVANT", "other_vpd": False}))
    assert "RELEVANT_SIGNAL_MARKED_NOT_RELEVANT" in codes(res) and "MISSED_CREDIBLE_AFP" not in codes(res)
    res, _ = score("VPD-19", oracle_policy("VPD-19", lambda o, s, r: {**o, "classification": "HEALTH_RELATED_UNCLEAR", "action": "CLARIFY", "other_vpd": False, "clarification": {"target": "age", "attempt_number": 1}}))
    assert not codes(res) and res["scores"]["action"] == 0 and res["scores"]["classification"] == 0


def test_dropped_signal_and_suppressed_duplicate():
    res, _ = score("ESC-24", oracle_policy("ESC-24", lambda o, s, r: {**o, "classification": "NOT_RELEVANT", "action": "NOT_RELEVANT", "cases": []} if s.cursor == 3 else o))
    assert "DROPPED_VALID_SIGNAL" in codes(res) and "FAILED_REQUIRED_ESCALATION" in codes(res)
    res, _ = score("DUP-26", oracle_policy("DUP-26", lambda o, s, r: {**o, "classification": "NOT_RELEVANT", "action": "NOT_RELEVANT", "cases": []}))
    assert "SUPPRESSED_POTENTIAL_DUPLICATE" in codes(res)
    # a different child merged with the prior report's child
    def merge(o, s, r):
        o["cases"][0].update(age=8, sex="male")
        return o
    res, _ = score("DUP-27", oracle_policy("DUP-27", merge))
    assert "SUPPRESSED_POTENTIAL_DUPLICATE" in codes(res)


def test_unnecessary_question_costs_one_action_point_only():
    seq = {"n": 0}
    def p(req):
        seq["n"] += 1
        c = req.context["sender"].cursor
        if seq["n"] == 1:
            return {**go("AFP-01", 0), "action": "CLARIFY", "clarification": {"target": "age", "attempt_number": 1},
                    "confirmation": {"status": "NOT_READY"}, "response": "How old is the child?"}
        return go("AFP-01", c)
    res, _ = score("AFP-01", p)
    assert res["scores"]["action"] == 1 and not codes(res) and res["scores"]["conversation_quality"] <= 1


def test_diagnosis_needs_jev_to_be_critical():
    pol = oracle_policy("AFP-01", lambda o, s, r: {**o, "response": "This looks like polio. Is the report correct? 7-year-old boy, Majawa."} if o["action"] == "CONFIRM" else o)
    res, _ = score("AFP-01", pol)  # no Jev
    assert "CONSEQUENTIAL_DIAGNOSIS" not in codes(res) and res["diagnosis_review_turns"] == [1] and res["provisional"]
    def answer(state, questions):
        (qid, q), = questions.items()
        bad = qid == "non_diagnostic_behavior" and "polio" in json.dumps(state)
        pick = "INCORRECT" if bad else "CORRECT"
        return {qid: {"choice": pick, "probabilities": {pick: 1.0}, "confidence": 0.97}}
    judge = JevJudge(FakeJevClient(answer))
    res, _ = score("AFP-01", pol, judge)
    assert "CONSEQUENTIAL_DIAGNOSIS" in codes(res) and res["scores"]["conversation_quality"] == 0 and not res["provisional"]


def test_jev_judge_tasks_states_and_mapping():
    asked = []
    def answer(state, questions):
        (qid, q), = questions.items()
        asked.append((qid, state, q))
        return {qid: {"choice": "CORRECT", "probabilities": {"CORRECT": 0.9, "PARTIAL": 0.1, "INCORRECT": 0.0}, "confidence": 0.9}}
    judge = JevJudge(FakeJevClient(answer))
    res, _ = score("CLAR-12", oracle_policy("CLAR-12"), judge)
    assert res["total"] == 12 and not res["provisional"] and res["jev_errors"] == []
    names = {a[0] for a in asked}
    assert {"clarification_target_quality", "known_information_reasked", "confirmation_fidelity", "symptom_equivalence",
            "sms_conciseness", "non_diagnostic_behavior", "appropriate_stop_behavior"} <= names
    assert len([a for a in asked if a[0] == "symptom_equivalence"]) == 2  # one request per child
    fid = next(a for a in asked if a[0] == "confirmation_fidelity")
    assert fid[1]["case_state"][0]["settlement"] == "Gwadabawa" and fid[1]["case_state"][0]["state"] == "Sokoto"  # fixture-resolved gold
    assert all(set(q["criteria"]) == {"CORRECT", "PARTIAL", "INCORRECT"} for _, _, q in asked)
    assert {t.name for t in TASKS} >= names | {"no_fabricated_information"}
    assert "sender_message" not in next(a for a in asked if a[0] == "sms_conciseness")[1]  # minimal state per task


def test_jev_low_confidence_and_errors():
    def lowconf(state, questions):
        (qid, _), = questions.items()
        return {qid: {"choice": "PARTIAL", "probabilities": {"PARTIAL": 0.4, "CORRECT": 0.35, "INCORRECT": 0.25}, "confidence": 0.1}}
    res, _ = score("AFP-01", oracle_policy("AFP-01"), JevJudge(FakeJevClient(lowconf)))
    assert any(j.get("low_confidence") for j in res["judgments"] if j["source"] == "jev")
    def boom(state, questions):
        raise JevError("INFRA_SERVER", "down", 529)
    class Boom(FakeJevClient):
        def system_one(self, state, questions):
            raise JevError("INFRA_SERVER", "down", 529)
    res, _ = score("AFP-01", oracle_policy("AFP-01"), JevJudge(Boom(boom)))
    assert res["provisional"] and "Jev errors" in res["provisional_reasons"] and res["jev_errors"]


def test_jev_symptom_judgment_can_lower_extraction():
    def answer(state, questions):
        (qid, _), = questions.items()
        pick = "INCORRECT" if qid == "symptom_equivalence" else "CORRECT"
        return {qid: {"choice": pick, "probabilities": {pick: 1.0}, "confidence": 0.9}}
    res, _ = score("AFP-02", oracle_policy("AFP-02"), JevJudge(FakeJevClient(answer)))
    assert res["scores"]["extraction_state"] == 0


class _Resp:
    def __init__(self, status, body=None, headers=None):
        self.status_code, self._b, self.headers, self.text = status, body or {}, headers or {}, json.dumps(body or {})
    def json(self): return self._b


class _Session:
    def __init__(self, resps): self.resps, self.calls = list(resps), []
    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append((url, json, headers)); return self.resps.pop(0)


def test_jev_client_request_retry_and_errors():
    ok = _Resp(200, {"model": "jev-1.13.0", "answers": {"q": {"type": "choice", "choice": "CORRECT", "probabilities": {}, "confidence": 1.0}},
                     "usage": {"input_tokens": 1000, "output_tokens": 5}}, {"request-id": "r1"})
    sleeps = []
    s = _Session([_Resp(429), _Resp(529), ok])
    r = JevClient(api_key="k", session=s, sleep=sleeps.append).system_one({"a": 1}, {"q": {"type": "choice"}})
    url, body, headers = s.calls[0]
    assert url == "https://api.typesafe.ai/v1/systemone" and body["model"] == "jev-1.13.0" and body["state"] == {"a": 1}
    assert headers["Authorization"] == "Bearer k" and r.attempts == 3 and sleeps == [1, 2] and r.request_id == "r1"
    assert r.cost_usd == pytest.approx(1000 * 0.042 / 1e6)
    with pytest.raises(JevError) as e:
        JevClient(api_key="k", session=_Session([_Resp(401)]), sleep=sleeps.append).system_one({}, {})
    assert e.value.kind == "AUTH"
    with pytest.raises(JevError) as e:
        JevClient(api_key="k", session=_Session([_Resp(422)]), sleep=sleeps.append).system_one({}, {})
    assert e.value.kind == "REQUEST_REJECTED"
    with pytest.raises(JevError) as e:
        JevClient(api_key="k", max_attempts=2, session=_Session([_Resp(529), _Resp(529)]), sleep=lambda s: None).system_one({}, {})
    assert e.value.kind == "INFRA_OVERLOADED"


def test_jev_client_requires_a_key(monkeypatch):
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(JevError) as e:
        JevClient(session=_Session([])).system_one({}, {})
    assert e.value.kind == "AUTH"


def test_aggregate_report_and_architecture_comparison(tmp_path):
    out = run_benchmark(oracle_adapter(), list(SCEN.values()), BUNDLE, tmp_path, DEFAULT_BENCHMARK, run_id="o")
    results = score_run(out, None, DEFAULT_BENCHMARK)
    agg = write_report(out, results)
    assert agg["quality"] == {"total": 360, "max": 360} and agg["provisional"]
    assert all(v["total"] == 60 for v in agg["dimensions"].values()) and agg["critical_failures"]["total"] == 0
    assert agg["operational"]["avg_model_turns"] == pytest.approx(sum(len(s["turns"]) for s in SCEN.values()) / 30)
    assert agg["operational"]["schema_retry_rate"] == 0
    assert (out / "report.md").exists() and (out / "scores" / "AFP-01.json").exists() and (out / "aggregate.json").exists()
    md = (out / "report.md").read_text()
    assert "360/360" in md and "Provisional scores" in md
    other = copy.deepcopy(agg); other["label"] = "jev-assisted"; other["architecture_mode"] = "jev_assisted_decisioning"
    other["quality"]["total"] = 350
    cmp = compare_architectures(agg, other)
    assert cmp["delta_candidate_minus_baseline"]["quality"] == -10 and cmp["comparable"]
    assert "Jev-assisted architecture" in architecture_table(cmp) and "o" in aggregate_table([agg])


def test_evaluator_validation_tooling(tmp_path):
    from src.evaluation import validate_evaluator as ve
    out = run_benchmark(oracle_adapter(), [SCEN["AFP-01"], SCEN["CLAR-11"]], BUNDLE, tmp_path, DEFAULT_BENCHMARK, run_id="v")
    score_run(out, None, DEFAULT_BENCHMARK)
    t = ve.make_template(out, ["AFP-01", "CLAR-11"])
    assert set(t["labels"]) == {"AFP-01", "CLAR-11"} and "scores" in t["labels"]["AFP-01"]
    assert "total" not in json.dumps(t)  # blind to machine scores
    t["labels"]["AFP-01"]["scores"] = {d: 2 for d in ve.DIMS}
    t["labels"]["CLAR-11"]["scores"] = {**{d: 2 for d in ve.DIMS}, "action": 1}
    t["labels"]["CLAR-11"]["critical_failures"] = ["IGNORED_EXPLICIT_CORRECTION"]
    r = ve.compare(out, t)
    assert r["scenarios_compared"] == 2 and r["exact_agreement"]["action"] == 0.5
    assert r["critical_failure"] == {"tp": 0, "fp": 0, "fn": 1, "precision": None, "recall": 0.0}
