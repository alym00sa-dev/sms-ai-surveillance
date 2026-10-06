"""Cross-model comparison report for a bake-off directory."""
from __future__ import annotations

import json
from pathlib import Path

from ..evaluation.aggregate import DIMS, aggregate
from .tables import aggregate_table

COMPARABLE_KEYS = [("prompt_hashes", "system_text"), ("benchmark", "sha256"), ("critical_check_mapping", "sha256"),
                   ("scorer_contract_sha256", None), ("location_fixture", "sha256"), ("symptom_features", "sha256")]


def _get(cfg, a, b):
    v = cfg[a]
    return v[b] if b else v


def write_comparison(out_dir: Path, runs: list[tuple[dict, list[dict], dict]], tag: str = "") -> dict:
    """runs: [(run_config, scenario_results, aggregate)] in slate order."""
    cfgs = [r[0] for r in runs]
    warn = []
    for a, b in COMPARABLE_KEYS:
        vals = {json.dumps(_get(c, a, b)) for c in cfgs}
        if len(vals) > 1:
            warn.append(f"runs differ in {a}{'.' + b if b else ''}")
    aggs = [r[2] for r in runs]
    temps = {a["label"]: (c["adapter"]["params"].get("temperature")) for a, c in zip(aggs, cfgs)}
    scen_ids = sorted({r["scenario_id"] for _, res, _ in runs for r in res})
    totals = {a["label"]: {r["scenario_id"]: (r["total"] if r["status"] == "SCORED" else None) for r in res} for a, (_, res, _) in zip(aggs, runs)}
    crit_codes = sorted({c for a in aggs for c in a["critical_failures"]["by_code"]})
    md = ["# Bake-off comparison", ""]
    if warn:
        md += ["> **Not strictly comparable:** " + "; ".join(warn), ""]
    if any(a["provisional"] for a in aggs):
        md += ["> **Provisional scores** present (" + ", ".join(sorted({x for a in aggs for x in a["provisional_reasons"]})) + ").", ""]
    md += ["## Aggregate", "", aggregate_table(aggs), "",
           "Temperature sent: " + ", ".join(f"{k}={'provider default' if v is None else v}" for k, v in temps.items()), ""]
    if crit_codes:
        md += ["## Critical failures by code (scenarios affected)", "", "| Code | " + " | ".join(a["label"] for a in aggs) + " |",
               "|---|" + "---:|" * len(aggs)]
        for c in crit_codes:
            md.append(f"| {c} | " + " | ".join(str(a["critical_failures"]["by_code"].get(c, 0)) for a in aggs) + " |")
        md.append("")
    md += ["## Scenario totals (out of 12; – = unscored)", "", "| Scenario | " + " | ".join(a["label"] for a in aggs) + " |", "|---|" + "---:|" * len(aggs)]
    for sid in scen_ids:
        md.append(f"| {sid} | " + " | ".join("–" if totals[a["label"]].get(sid) is None else str(totals[a["label"]][sid]) for a in aggs) + " |")
    md += ["", "## Terminations and exclusions", ""]
    for a in aggs:
        md.append(f"- **{a['label']}**: {json.dumps(a['terminations'])}" + (f"; excluded as infra: {', '.join(a['unscored_infra'])}" if a["unscored_infra"] else "")
                  + f"; resolver non-compliance {json.dumps(a['resolver_compliance'])}")
    (out_dir / f"comparison{'_' + tag if tag else ''}.md").write_text("\n".join(md) + "\n")
    doc = {"aggregates": aggs, "warnings": warn, "temperature": temps, "scenario_totals": totals}
    (out_dir / f"comparison{'_' + tag if tag else ''}.json").write_text(json.dumps(doc, indent=2))
    return doc
