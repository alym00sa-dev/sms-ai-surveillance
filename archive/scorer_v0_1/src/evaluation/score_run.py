"""Score runs: deterministic + (optional) Jev semantic judgments -> six 0/1/2 dimensions per scenario."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..benchmark.loader import load_benchmark
from ..benchmark.location_fixture import load_fixture
from ..benchmark.symptoms import load_symptom_features
from ..schemas.score import ScenarioScore
from . import critical_failures as cf
from . import deterministic as det
from .context import build_views
from .semantic_jev import JEV_EVALUATOR_VERSION

SCORER_VERSION = "v0.1"
ROOT = Path(__file__).resolve().parents[2]
DIMS = ["classification", "extraction_state", "action", "conversation_quality", "escalation_priority", "output_adherence"]


def load_mapping() -> dict:
    return json.loads((ROOT / "data" / "critical_check_mapping_v0_1.json").read_text())


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def score_scenario(scenario: dict, run: dict, fixture: dict, sf: dict, mapping: dict, judge=None) -> dict:
    term = run["termination"].get("reason")
    base = {"scenario_id": scenario["id"], "model": run["model_key"], "termination": run["termination"],
            "metrics": run["metrics"], "scorer_version": SCORER_VERSION}
    if term == "INFRA_ERROR":
        return {**base, "status": "UNSCORED_INFRA", "notes": ["API/infrastructure failure; not a model-quality result"]}

    views = build_views(scenario, run, fixture, sf)
    jev_all = judge.judge_scenario(scenario, views, fixture) if judge else []
    jev = [j for j in jev_all if j.get("result")]
    jev_errors = [j for j in jev_all if not j.get("result")]
    findings = cf.detect(scenario, views, run, jev)
    codes = {f["code"] for f in findings}

    judgments = det.det_judgments(views, len(scenario["turns"])) + jev
    diag_pending = [] if judge else cf.diagnosis_candidates(views)
    if diag_pending:
        judgments.append({"task": "non_diagnostic_behavior", "result": "PARTIAL", "turn": diag_pending[0], "source": "det",
                          "detail": f"names a disease the sender did not mention (turns {diag_pending}); needs Jev review"})
    checks = det.run_checks(mapping, scenario, views, findings, judgments)
    caps = det.dimension_caps(checks)

    jev_sym: dict[int, str] = {}
    for j in jev:
        if j["task"] == "symptom_equivalence":
            jev_sym[j["turn"]] = max(jev_sym.get(j["turn"], "CORRECT"), j["result"], key=det.ORDER.get)
    ex, ex_notes = det.score_extraction(views, codes, term, jev_sym or None)
    if jev_sym:
        worst = max(jev_sym.values(), key=det.ORDER.get)
        if worst == "INCORRECT":
            ex, ex_notes = 0, ex_notes + ["Jev: recorded symptom changes the meaning"]
        elif worst == "PARTIAL" and ex == 2:
            ex, ex_notes = 1, ex_notes + ["Jev: recorded symptom loses or adds a detail"]
    cl, cl_notes = det.score_classification(views)
    ac, ac_notes = det.score_action(views, term)
    cq, cq_notes, worst_tasks = det.score_conversation(judgments, term, codes)
    ep, ep_notes = det.score_escalation(views, scenario["turns"])
    oa, oa_notes = det.score_output(views, term)

    rubric = {"classification": cl, "extraction_state": ex, "action": ac, "conversation_quality": cq,
              "escalation_priority": ep, "output_adherence": oa}
    scores = {d: min(rubric[d], caps.get(d, 2)) for d in DIMS}
    notes = [f"{d}: {n}" for d, ns in (("classification", cl_notes), ("extraction", ex_notes), ("action", ac_notes),
             ("conversation", cq_notes), ("escalation", ep_notes), ("output", oa_notes)) for n in ns]
    for d in DIMS:
        if scores[d] < rubric[d]:
            notes.append(f"{d}: capped at {scores[d]} by failed mapped check(s) " +
                         ", ".join(sorted({c['check'] for c in checks if c['status'] == 'FAIL' and c.get('dimension') == d})))
    provisional = judge is None or bool(jev_errors)
    core = ScenarioScore(
        scenario_id=scenario["id"], model=run["model_key"], scores=scores, total=sum(scores.values()),
        critical_failures=sorted(codes), notes=notes, scorer_version=SCORER_VERSION,
        mapping_sha256=_sha(ROOT / "data" / "critical_check_mapping_v0_1.json"),
        deterministic_checks={"confirmation_before_accept": "ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION" not in codes,
                              "correction_applied": "IGNORED_EXPLICIT_CORRECTION" not in codes,
                              "case_count_match": not any(d["kind"] in ("missing_case", "extra_case") for v in views for d in v.diffs),
                              "completed": term == "COMPLETED"},
        jev_judgments={t: r for t, r in worst_tasks.items() if any(j["task"] == t and j["source"] == "jev" for j in jev)})
    return {**base, "status": "SCORED", "provisional": provisional,
            "provisional_reasons": (["Jev not run"] if judge is None else []) + (["Jev errors"] if jev_errors else []),
            "score": json.loads(core.model_dump_json()), "scores": scores, "total": core.total, "rubric": rubric,
            "critical_findings": findings, "diagnosis_review_turns": diag_pending,
            "checks": checks, "judgments": judgments, "jev_errors": jev_errors,
            "resolver_compliance": det.resolver_compliance(run, fixture), "notes": notes}


def score_run(run_dir: Path | str, judge=None, benchmark_path=None) -> list[dict]:
    run_dir = Path(run_dir)
    scen = {s["id"]: s for s in load_benchmark(benchmark_path)}
    fixture, sf, mapping = load_fixture(), load_symptom_features(), load_mapping()
    results = []
    (run_dir / "scores").mkdir(exist_ok=True)
    for p in sorted((run_dir / "scenarios").glob("*.json")):
        run = json.loads(p.read_text())
        res = score_scenario(scen[run["scenario_id"]], run, fixture, sf, mapping, judge)
        (run_dir / "scores" / p.name).write_text(json.dumps(res, indent=2, ensure_ascii=False))
        results.append(res)
    cfg = {"scorer_version": SCORER_VERSION, "jev_evaluator": judge.describe() if judge else None,
           "jev_evaluator_version": JEV_EVALUATOR_VERSION if judge else None, "thresholds": det.THRESHOLDS,
           "mapping_sha256": _sha(ROOT / "data" / "critical_check_mapping_v0_1.json"),
           "scorer_contract_sha256": _sha(ROOT / "SMS_AI_SURVEILLANCE_SCORER_CONTRACT_v0_1.md"),
           "symptom_features_sha256": _sha(ROOT / "data" / "symptom_features_v0_1.json"),
           "fixture_sha256": _sha(ROOT / "data" / "location_fixture_v0_1.json")}
    (run_dir / "scoring_config.json").write_text(json.dumps(cfg, indent=2))
    return results
