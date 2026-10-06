"""Calibration of the scorer on hand-authored model outputs (no live model involved).

  python -m src.evaluation.calibration        # prints a table and exits non-zero on any disagreement
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from ..adapters.base import AdapterRequest
from ..adapters.fake import FakeAdapter, gold_output
from ..adapters.jev import FakeJevClient
from ..benchmark.loader import load_benchmark
from ..benchmark.location_fixture import load_fixture
from ..benchmark.runner import run_scenario
from ..benchmark.symptoms import load_symptom_features
from ..prompts import load_bundle
from .score_run import DIMS, load_mapping, score_scenario
from .semantic_jev import JevJudge

CAL_FILE = Path(__file__).resolve().parents[2] / "data" / "calibration" / "calibration_v0_1.json"


def _set(d: dict, path: str, value) -> None:
    keys = path.split(".")
    for k in keys[:-1]:
        d = d[int(k)] if isinstance(d, list) else d[k]
    last = keys[-1]
    if isinstance(d, list):
        d[int(last)] = value
    else:
        d[last] = value


def build_output(scenario: dict, spec: dict):
    if "raw" in spec:
        return spec["raw"]
    out = copy.deepcopy(gold_output(scenario, spec["from_gold"]))
    for path, val in spec.get("set", {}).items():
        _set(out, path, val)
    return out


def _fake_jev(script: dict | None) -> JevJudge:
    script = script or {}
    def answer(state, questions):
        (qid, _), = questions.items()
        pick = script.get(qid, "CORRECT")
        return {qid: {"choice": pick, "probabilities": {pick: 1.0}, "confidence": 0.95}}
    return JevJudge(FakeJevClient(answer))


def run_case(case: dict, scenarios: dict, fixture, sf, mapping) -> dict:
    sc = scenarios[case["scenario"]]
    queue = [build_output(sc, o) for o in case["outputs"]]
    idx = {"i": 0}

    def policy(req: AdapterRequest):
        out = queue[min(idx["i"], len(queue) - 1)]
        idx["i"] += 1
        return out

    run = run_scenario(FakeAdapter(policy), sc, load_bundle())
    res = score_scenario(sc, run, fixture, sf, mapping, _fake_jev(case.get("jev")))
    return {"run": run, "result": res}


def calibrate() -> list[dict]:
    doc = json.loads(CAL_FILE.read_text())
    scen = {s["id"]: s for s in load_benchmark()}
    fx, sf, mp = load_fixture(), load_symptom_features(), load_mapping()
    rows = []
    for c in doc["cases"]:
        r = run_case(c, scen, fx, sf, mp)
        res, exp = r["result"], c["expected"]
        got = {"termination": r["run"]["termination"].get("reason"), "scores": res["scores"], "total": res["total"],
               "critical_failures": res["score"]["critical_failures"]}
        diffs = {}
        if got["termination"] != exp["termination"]:
            diffs["termination"] = (got["termination"], exp["termination"])
        for d in DIMS:
            if got["scores"][d] != exp["scores"][d]:
                diffs[d] = (got["scores"][d], exp["scores"][d])
        if sorted(got["critical_failures"]) != sorted(exp["critical_failures"]):
            diffs["critical_failures"] = (sorted(got["critical_failures"]), sorted(exp["critical_failures"]))
        rows.append({"id": c["id"], "scenario": c["scenario"], "description": c["description"], "expected": exp, "got": got,
                     "diffs": diffs, "notes": res["notes"]})
    return rows


def main() -> int:
    rows = calibrate()
    bad = [r for r in rows if r["diffs"]]
    for r in rows:
        mark = "OK  " if not r["diffs"] else "DIFF"
        print(f"{mark} {r['id']} {r['scenario']:9} {r['got']['total']:2}/12 (expected {r['expected']['total']:2})  {r['description']}")
        for k, (g, e) in r["diffs"].items():
            print(f"       {k}: scorer={g} label={e}")
    print(f"\n{len(rows) - len(bad)}/{len(rows)} cases agree with the hand-authored labels")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
