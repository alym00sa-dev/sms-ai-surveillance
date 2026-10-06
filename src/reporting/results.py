"""Write report artifacts for a scored run directory."""
from __future__ import annotations

import json
from pathlib import Path

from ..evaluation.aggregate import aggregate
from .tables import aggregate_table, critical_table, scenario_table


def write_report(run_dir: Path | str, results: list[dict], tag: str = "") -> dict:
    run_dir = Path(run_dir)
    suffix = f"_{tag}" if tag else ""
    cfg = json.loads((run_dir / "run_config.json").read_text())
    agg = aggregate(results, cfg)
    (run_dir / f"aggregate{suffix}.json").write_text(json.dumps(agg, indent=2))
    md = [f"# {agg['label']}", "",
          f"Architecture: `{agg['architecture_mode']}` · model: `{agg['model']}` · scorer `{results[0]['scorer_version'] if results else '?'}`", ""]
    if agg["provisional"]:
        md += [f"> **Provisional scores** ({', '.join(agg['provisional_reasons'])}). Do not compare against final runs.", ""]
    if agg["unscored_infra"]:
        md += [f"> Excluded as infrastructure failures: {', '.join(agg['unscored_infra'])}", ""]
    md += ["## Aggregate", "", aggregate_table([agg]), "", "## Critical failures", "", critical_table(results), "",
           "## Scenarios", "", scenario_table(results), "",
           f"Terminations: {json.dumps(agg['terminations'])}  \nResolver non-compliance: {json.dumps(agg['resolver_compliance'])}", ""]
    (run_dir / f"report{suffix}.md").write_text("\n".join(md))
    return agg
