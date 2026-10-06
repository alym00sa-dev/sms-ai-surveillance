"""Side-by-side of two scorings of the same runs.  python -m src.reporting.side_by_side DIR v0_1 v0_2"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DIMS = ["classification", "extraction_state", "action", "conversation_quality", "escalation_priority", "output_adherence"]


def build(out_dir: Path, a: str, b: str) -> str:
    A = json.loads((out_dir / f"comparison_{a}.json").read_text())["aggregates"]
    B = {x["label"]: x for x in json.loads((out_dir / f"comparison_{b}.json").read_text())["aggregates"]}
    rank = lambda items: {k: i + 1 for i, k in enumerate(sorted(items, key=lambda k: -items[k]))}
    ta = {x["label"]: x["quality"]["total"] for x in A}
    tb = {k: v["quality"]["total"] for k, v in B.items()}
    ra, rb = rank(ta), rank(tb)
    L = [f"# Scorer {a} vs {b}", "", "| Model | " + a + " | " + b + " | Delta | Rank " + a + " | Rank " + b + " | Conversation " + a + " | Conversation " + b +
         " | Critical " + a + " | Critical " + b + " |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in sorted(A, key=lambda x: rb[x["label"]]):
        k = x["label"]
        L.append(f"| {k} | {ta[k]} | {tb[k]} | {tb[k] - ta[k]:+d} | {ra[k]} | {rb[k]} | {x['dimensions']['conversation_quality']['total']} | "
                 f"{B[k]['dimensions']['conversation_quality']['total']} | {x['critical_failures']['total']} | {B[k]['critical_failures']['total']} |")
    L += ["", "## Other dimensions (should be unchanged)", "", "| Model | " + " | ".join(d for d in DIMS if d != "conversation_quality") + " |", "|---|" + "---:|" * 5]
    for x in A:
        k = x["label"]
        L.append(f"| {k} | " + " | ".join(f"{x['dimensions'][d]['total']}->{B[k]['dimensions'][d]['total']}" for d in DIMS if d != "conversation_quality") + " |")
    # scenarios that changed
    L += ["", "## Scenarios whose total changed", "", "| Scenario | Model | " + a + " | " + b + " | Why (v0.2 notes) |", "|---|---|---:|---:|---|"]
    for run in sorted((out_dir / "runs").iterdir()):
        for p in sorted((run / f"scores_{a}").glob("*.json")):
            s1, s2 = json.loads(p.read_text()), json.loads((run / f"scores_{b}" / p.name).read_text())
            if s1.get("status") == "SCORED" and s1["total"] != s2["total"]:
                dd = [d for d in DIMS if s1["scores"][d] != s2["scores"][d]]
                L.append(f"| {s1['scenario_id']} | {run.name} | {s1['total']} | {s2['total']} | {', '.join(dd)} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    d = Path(sys.argv[1])
    out = build(d, sys.argv[2], sys.argv[3])
    (d / f"side_by_side_{sys.argv[2]}_vs_{sys.argv[3]}.md").write_text(out)
    print(out)
