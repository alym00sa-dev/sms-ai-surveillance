import json

from src.adapters.anthropic import AnthropicAdapter
from src.adapters.base import AdapterError
from src.adapters.fake import FakeAdapter, gold_output, oracle_adapter
from src.benchmark.loader import DEFAULT_BENCHMARK, load_benchmark
from src.benchmark.runner import run_benchmark, run_scenario
from src.prompts import load_bundle

SCEN = {s["id"]: s for s in load_benchmark()}
BUNDLE = load_bundle()


def test_oracle_completes_all_scenarios_and_persists_artifacts(tmp_path):
    out = run_benchmark(oracle_adapter(), list(SCEN.values()), BUNDLE, tmp_path, DEFAULT_BENCHMARK, run_id="t")
    assert {p.name for p in out.iterdir()} == {"run_config.json", "summary.json", "scenarios"}
    s = json.loads((out / "summary.json").read_text())
    assert s["totals"]["terminations"] == {"COMPLETED": 30}
    sc = json.loads((out / "scenarios" / "CLAR-11.json").read_text())
    assert sc["model_actions"] == ["CLARIFY", "CONFIRM", "CONFIRM", "ACCEPT"]
    t0 = sc["turns"][0]
    assert t0["envelope"]["location_resolver"]["status"] == "AMBIGUOUS" and t0["attempts"][0]["raw_text"]
    cfg = json.loads((out / "run_config.json").read_text())
    for k in ("prompt_version", "prompt_hashes", "benchmark", "location_fixture", "critical_check_mapping",
              "scorer_version", "adapter", "sender_policy_version", "output_schema_sha256"):
        assert k in cfg
    assert cfg["critical_check_mapping"]["sha256"] == json.loads(
        (DEFAULT_BENCHMARK.parent / "FROZEN_MANIFEST.json").read_text())["artifacts"]["critical_check_mapping"]["sha256"]


def test_envelope_carries_resolver_and_attempts():
    ad = oracle_adapter()
    run_scenario(ad, SCEN["ESC-24"], BUNDLE)
    envs = [json.loads(c.messages[0]["content"]) for c in ad.calls]
    assert [e["clarification_attempts"] for e in envs] == [0, 1, 2, 3]
    assert all(e["location_resolver"]["status"] == "UNRESOLVED" for e in envs)
    assert envs[0]["current_case_state"] == {"cases": []} and envs[1]["current_case_state"]["cases"][0]["age"] == 6


def test_schema_retry_preserves_first_invalid_output():
    sc = SCEN["AFP-01"]
    n = {"i": 0}
    def policy(req):
        n["i"] += 1
        if n["i"] == 1:
            return "Sure! Here is the JSON: {not json"
        return gold_output(sc, req.context["sender"].cursor)
    ad = FakeAdapter(policy)
    res = run_scenario(ad, sc, BUNDLE)
    t = res["turns"][0]
    assert len(t["attempts"]) == 2 and t["status"] == "OK"
    assert t["attempts"][0]["raw_text"].startswith("Sure!") and not t["attempts"][0]["validation"]["ok"]
    assert t["attempts"][1]["validation"]["ok"]
    retry_msgs = ad.calls[1].messages
    assert retry_msgs[1] == {"role": "assistant", "content": "Sure! Here is the JSON: {not json"}
    assert "invalid" in retry_msgs[2]["content"]
    m = res["metrics"]
    assert m["schema_retries"] == 1 and m["schema_failures_first_attempt"] == 1 and m["api_calls"] == 3
    assert res["termination"]["reason"] == "COMPLETED"


def test_two_invalid_outputs_terminate_as_output_invalid():
    res = run_scenario(FakeAdapter(lambda r: "nope"), SCEN["AFP-01"], BUNDLE)
    assert res["termination"]["reason"] == "OUTPUT_INVALID" and len(res["turns"][0]["attempts"]) == 2
    assert res["turns"][0]["reply"] is None and res["model_actions"] == []


def test_infra_error_is_separate_from_model_failure():
    err = AdapterError("INFRA_SERVER", "overloaded", 529, "req_x")
    res = run_scenario(FakeAdapter(lambda r: err), SCEN["AFP-01"], BUNDLE)
    assert res["termination"]["reason"] == "INFRA_ERROR" and res["termination"]["detail"]["status_code"] == 529
    assert len(res["turns"][0]["attempts"]) == 1  # no schema retry on an API error


def test_premature_accept_ends_scenario():
    sc = SCEN["AFP-01"]
    res = run_scenario(FakeAdapter(lambda r: {**gold_output(sc, 1)}), sc, BUNDLE)
    assert res["termination"]["reason"] == "PREMATURE_TERMINAL" and len(res["turns"]) == 1


def test_unknown_pricing_gives_null_cost():
    res = run_scenario(FakeAdapter(lambda r: gold_output(SCEN["IRR-29"], 0), cost_per_call=None), SCEN["IRR-29"], BUNDLE)
    assert res["metrics"]["cost_usd"] is None


class _Usage:
    input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens = 1000, 200, 0, 0


class _Block:
    type = "text"
    def __init__(self, t): self.text = t


class _Msg:
    content, stop_reason, model, usage, _request_id = [_Block("{}")], "end_turn", "claude-haiku-4-5-20251001", _Usage(), "req_1"
    def to_dict(self): return {"id": "msg_1"}


class _Client:
    def __init__(self): self.kw = None; self.messages = self
    def create(self, **kw): self.kw = kw; return _Msg()


def test_anthropic_request_shape_and_cost():
    from src.config import load_models
    cfg = load_models()["models"]["haiku-4-5"]
    c = _Client()
    ad = AnthropicAdapter("haiku-4-5", cfg, client=c)
    from src.adapters.base import AdapterRequest
    from src.schemas.model_output import MODEL_OUTPUT_JSON_SCHEMA
    r = ad.complete(AdapterRequest("SYS", [{"role": "user", "content": "x"}], MODEL_OUTPUT_JSON_SCHEMA))
    kw = c.kw
    assert kw["model"] == "claude-haiku-4-5-20251001" and kw["temperature"] == 0.7 and kw["max_tokens"] == 16000
    assert kw["output_config"] == {"format": {"type": "json_schema", "schema": MODEL_OUTPUT_JSON_SCHEMA}}
    assert "thinking" not in kw and kw["system"] == "SYS"
    assert r.structured_output_mode == "native_json_schema" and r.cost_usd == 1000 * 1 / 1e6 + 200 * 5 / 1e6
    assert r.request_params["output_config"]["format"]["schema"] == "<MODEL_OUTPUT_JSON_SCHEMA>"  # schema not duplicated in logs
    ad2 = AnthropicAdapter("haiku-4-5", cfg, client=c, native_schema=False)
    ad2.complete(AdapterRequest("SYS", [], MODEL_OUTPUT_JSON_SCHEMA))
    assert "output_config" not in c.kw and ad2.structured_output_mode == "prompt_only"
    s = load_models()["models"]["sonnet-5-5"]
    AnthropicAdapter("sonnet-5-5", s, client=c).complete(AdapterRequest("SYS", [], None))
    assert ("temperature" in c.kw) == (s["params"]["temperature"] is not None)  # follows the config (preflight decides exceptions)


def test_persisted_envelope_is_a_snapshot_of_what_the_model_saw():
    res = run_scenario(oracle_adapter(), SCEN["CLAR-06"], BUNDLE)
    seen = [len(t["envelope"]["conversation"]) for t in res["turns"]]
    assert seen == [1, 3, 5]  # user / +assistant+user / ... , not the final conversation
    for t in res["turns"]:
        sent = json.loads(t["attempts"][0]["messages_sent"][0]["content"])
        assert sent == t["envelope"]
