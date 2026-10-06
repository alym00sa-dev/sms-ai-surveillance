import json

from src.adapters.base import AdapterError
from src.adapters.fake import FakeAdapter, gold_output, oracle_adapter
from src.bakeoff import estimate_cost, run_bakeoff, score_bakeoff
from src.benchmark.loader import load_benchmark
from src.config import load_models

SCEN = load_benchmark()
SUB = [s for s in SCEN if s["id"] in ("AFP-01", "CLAR-06", "ESC-24", "VPD-19", "IRR-30")]


def oracle(key):
    ad = oracle_adapter()
    ad.key = key
    return ad


def test_sequential_runs_then_scoring_and_comparison(tmp_path):
    meta = run_bakeoff([oracle("model-a"), oracle("model-b")], SUB, tmp_path, log=lambda *_: None)
    assert [m["model_key"] for m in meta["models"]] == ["model-a", "model-b"]
    assert (tmp_path / "runs" / "model-a" / "summary.json").exists() and (tmp_path / "bakeoff.json").exists()
    doc = score_bakeoff(tmp_path, None, log=lambda *_: None)
    md = (tmp_path / "comparison.md").read_text()
    assert "model-a" in md and "model-b" in md and "Provisional" in md and "Scenario totals" in md
    assert [a["quality"] for a in doc["aggregates"]] == [{"total": 60, "max": 60}, {"total": 60, "max": 60}]
    assert (tmp_path / "runs" / "model-a" / "report.md").exists() and doc["warnings"] == []


def test_circuit_breaker_stops_a_dead_model_but_not_the_rest(tmp_path):
    dead = FakeAdapter(lambda r: AdapterError("REQUEST_REJECTED", "bad", 400), key="dead")
    meta = run_bakeoff([dead, oracle("ok")], SUB, tmp_path, log=lambda *_: None)
    d, ok = meta["models"]
    assert d["aborted"] == "3 consecutive infrastructure errors" and d["totals"]["scenarios"] == 3
    assert ok["aborted"] is None and ok["totals"]["terminations"] == {"COMPLETED": 5}


def test_budget_cap_stops_everything(tmp_path):
    pricey = oracle("pricey")
    pricey.cost_per_call = 1.0
    nxt = oracle("never-runs")
    meta = run_bakeoff([pricey, nxt], SUB, tmp_path, max_usd=3.0, log=lambda *_: None)
    assert [m["model_key"] for m in meta["models"]] == ["pricey"] and meta["models"][0]["aborted"].startswith("budget cap")


def test_resume_keeps_finished_scenarios_and_reruns_infra_errors(tmp_path):
    calls = {"n": 0}
    def flaky(req):
        calls["n"] += 1
        sc = req.context["scenario"]
        if sc["id"] == "CLAR-06":
            return AdapterError("INFRA_SERVER", "overloaded", 529)
        return gold_output(sc, req.context["sender"].cursor)
    ad = FakeAdapter(flaky, key="flaky")
    run_bakeoff([ad], SUB[:2], tmp_path, log=lambda *_: None)
    first = calls["n"]
    ok = oracle("flaky")
    run_bakeoff([ok], SUB[:2], tmp_path, resume=True, log=lambda *_: None)
    assert len(ok.calls) == 3  # only CLAR-06 (INFRA_ERROR before) is rerun: 3 turns; AFP-01 is kept
    s = json.loads((tmp_path / "runs" / "flaky" / "summary.json").read_text())
    assert s["totals"]["terminations"] == {"COMPLETED": 2}


def test_estimates_use_user_pricing_and_skip_unpriced():
    m = load_models()["models"]
    assert estimate_cost(m["kimi-k3"]) > estimate_cost(m["gpt-6-luna"]) > 0
    assert estimate_cost(m["gemma-4-31b"]) is None
