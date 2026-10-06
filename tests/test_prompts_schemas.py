import json

from src.config import compute_cost, load_models
from src.prompts import CONTRACT_FILE, README, SYSTEM_FILE, extract_from_readme, load_bundle
from src.schemas.benchmark_case import validate_benchmark
from src.benchmark.loader import load_benchmark
from src.schemas.model_output import MODEL_OUTPUT_JSON_SCHEMA, parse_json_text, validate_output
from src.adapters.fake import gold_output


def test_prompt_files_match_readme_mechanically():
    system, contract, version = extract_from_readme(README.read_text(encoding="utf-8"))
    assert SYSTEM_FILE.read_text(encoding="utf-8") == system + "\n"
    assert CONTRACT_FILE.read_text(encoding="utf-8") == contract + "\n"
    b = load_bundle()
    assert b.version == version == "v0.3"
    assert "LOCATION RESOLVER" in b.system_prompt and "Required JSON output shape" in b.output_contract
    assert "Multi-turn input" not in b.output_contract


def test_exported_json_schema_in_sync():
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / "data" / "model_output.schema.json"
    assert json.loads(p.read_text()) == MODEL_OUTPUT_JSON_SCHEMA


def test_json_schema_is_strict_objects():
    def walk(s):
        if isinstance(s, dict):
            if s.get("type") == "object":
                assert s["additionalProperties"] is False and set(s["required"]) == set(s["properties"])
            for v in s.values():
                walk(v)
        elif isinstance(s, list):
            for v in s:
                walk(v)
    walk(MODEL_OUTPUT_JSON_SCHEMA)


def test_benchmark_rows_valid_and_gold_outputs_validate():
    rows = load_benchmark()
    validate_benchmark(rows)
    for sc in rows:
        for i in range(len(sc["turns"])):
            r = validate_output(gold_output(sc, i))
            assert r.ok and not r.warnings, (sc["id"], i, r.errors, r.warnings)


def test_validator_errors_and_warnings():
    good = gold_output(load_benchmark()[0], 0)
    assert not validate_output({**good, "action": "MAYBE"}).ok
    assert not validate_output({k: v for k, v in good.items() if k != "cases"}).ok
    assert not validate_output({**good, "cases": [{**good["cases"][0], "sex": "boy"}]}).ok
    r = validate_output({**good, "note": "x"})
    assert r.ok and any("extra" in w for w in r.warnings)
    r = validate_output({**good, "confirmation": {"status": "CONFIRMED"}})
    assert r.ok and any("confirmation.status" in w for w in r.warnings)
    assert parse_json_text("```json\n" + json.dumps(good) + "\n```")[1] == ["wrapped_in_code_fence"]


def test_cost_never_guessed():
    u = {"input_tokens": 1_000_000, "output_tokens": 1_000_000}
    assert compute_cost(u, {"input_per_mtok": 1.0, "output_per_mtok": 5.0}) == 6.0
    assert compute_cost(u, None) is None
    assert compute_cost({**u, "cache_read_input_tokens": 5}, {"input_per_mtok": 1.0, "output_per_mtok": 5.0, "cache_read_per_mtok": None}) is None
    models = load_models()["models"]
    assert models["gemma-4-31b"]["pricing"] is None and models["haiku-4-5"]["pricing"]["source"] == "anthropic"
    fb = {"input_per_mtok": 2.0, "output_per_mtok": 10.0, "cache_fallback": "input_price"}
    assert compute_cost({"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 1_000_000}, fb) == 2.0  # upper bound
