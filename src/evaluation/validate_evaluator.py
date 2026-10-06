"""Evaluator validation against human judgments (scorer contract section 26).

  python -m src.evaluation.validate_evaluator template <scored_run_dir> [ids...]   -> human_labels_<run>.json (blind: no machine scores)
  python -m src.evaluation.validate_evaluator compare  <scored_run_dir> <filled_labels.json>

Humans score the six dimensions (0/1/2) and list critical-failure codes from the transcript alone; the comparison
then reports agreement per dimension and critical-failure precision/recall. Freeze the scorer only after review.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DIMS = ["classification", "extraction_state", "action", "conversation_quality", "escalation_priority", "output_adherence"]
SUGGESTED = ["AFP-01", "CLAR-09", "CLAR-11", "CLAR-12", "MESSY-18", "VPD-19", "ESC-23", "ESC-24", "ESC-25", "DUP-26"]


def make_template(run_dir: Path, ids: list[str] | None = None) -> dict:
    out = {"run": run_dir.name, "instructions": "Fill scores (0/1/2) and critical_failures (codes from the scorer contract) from the transcript only.",
           "labels": {}}
    for sid in ids or SUGGESTED:
        p = run_dir / "scenarios" / f"{sid}.json"
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        out["labels"][sid] = {"transcript": [f"{m['role']}: {m['content']}" for m in r["conversation"]],
                              "model_actions": r["model_actions"], "ended": r["termination"].get("reason"),
                              "scores": {d: None for d in DIMS}, "critical_failures": [], "notes": ""}
    return out


def compare(run_dir: Path, labels: dict) -> dict:
    rows, agree = [], {d: 0 for d in DIMS}
    absdiff = {d: 0 for d in DIMS}
    tp = fp = fn = 0
    n = 0
    for sid, lab in labels["labels"].items():
        if any(v is None for v in lab["scores"].values()):
            continue
        m = json.loads((run_dir / "scores" / f"{sid}.json").read_text())
        if m["status"] != "SCORED":
            continue
        n += 1
        for d in DIMS:
            agree[d] += int(m["scores"][d] == lab["scores"][d])
            absdiff[d] += abs(m["scores"][d] - lab["scores"][d])
        mc, hc = set(m["score"]["critical_failures"]), set(lab["critical_failures"])
        tp += len(mc & hc); fp += len(mc - hc); fn += len(hc - mc)
        diff = {d: (m["scores"][d], lab["scores"][d]) for d in DIMS if m["scores"][d] != lab["scores"][d]}
        if diff or mc != hc:
            rows.append({"scenario": sid, "machine_vs_human": diff, "critical_machine": sorted(mc), "critical_human": sorted(hc)})
    return {"scenarios_compared": n,
            "exact_agreement": {d: (agree[d] / n if n else None) for d in DIMS},
            "mean_abs_diff": {d: (absdiff[d] / n if n else None) for d in DIMS},
            "critical_failure": {"tp": tp, "fp": fp, "fn": fn,
                                 "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / (tp + fn) if tp + fn else None},
            "disagreements": rows}


def main(argv=None) -> int:
    a = argv or sys.argv[1:]
    if len(a) >= 2 and a[0] == "template":
        run = Path(a[1])
        t = make_template(run, a[2:] or None)
        out = run / f"human_labels_{run.name}.json"
        out.write_text(json.dumps(t, indent=2))
        print(out)
        return 0
    if len(a) == 3 and a[0] == "compare":
        print(json.dumps(compare(Path(a[1]), json.loads(Path(a[2]).read_text())), indent=2))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
