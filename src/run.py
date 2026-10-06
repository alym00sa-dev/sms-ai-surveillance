"""CLI: python -m src.run --model haiku-4-5 --scenarios AFP-01   (or --oracle for an API-free dry run)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.registry import build_adapter
from .adapters.fake import oracle_adapter
from .benchmark.loader import DEFAULT_BENCHMARK, load_benchmark
from .benchmark.runner import run_benchmark
from .config import ROOT, load_env, load_models
from .prompts import load_bundle
from .schemas.benchmark_case import validate_benchmark


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Run the SMS AI surveillance benchmark")
    ap.add_argument("--model", help="key in config/models.json")
    ap.add_argument("--oracle", action="store_true", help="dry run with a gold-replaying fake model (no API)")
    ap.add_argument("--scenarios", nargs="*", default=["all"], help="scenario ids or 'all'")
    ap.add_argument("--results-dir", default=str(ROOT / "results"))
    ap.add_argument("--no-native-schema", action="store_true", help="prompt-only output contract (logged as such)")
    ap.add_argument("--max-extra-turns", type=int, default=3)
    a = ap.parse_args(argv)

    load_env()
    rows = load_benchmark()
    validate_benchmark(rows)
    chosen = rows if a.scenarios == ["all"] else [r for r in rows if r["id"] in set(a.scenarios)]
    missing = set(a.scenarios) - {r["id"] for r in chosen} - {"all"}
    if missing:
        print(f"unknown scenario ids: {sorted(missing)}", file=sys.stderr)
        return 2
    if a.oracle:
        adapter = oracle_adapter()
    else:
        cfg = load_models()["models"].get(a.model or "")
        if not cfg:
            print(f"unknown --model {a.model!r}; see config/models.json", file=sys.stderr)
            return 2
        try:
            adapter = build_adapter(a.model, cfg, native_schema=False if a.no_native_schema else None)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
    out = run_benchmark(adapter, chosen, load_bundle(), Path(a.results_dir), DEFAULT_BENCHMARK,
                        max_extra_turns=a.max_extra_turns)
    s = json.loads((out / "summary.json").read_text())
    print(f"run dir: {out}")
    print(json.dumps(s["totals"], indent=2))
    for r in s["scenarios"]:
        print(f"{r['scenario_id']:9} {r['termination']:20} gold={r['gold_actions']} model={r['model_actions']} "
              f"calls={r['api_calls']} retries={r['schema_retries']} cost={r['cost_usd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
