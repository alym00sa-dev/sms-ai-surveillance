"""CLI: python -m src.score results/<run> [--jev off|live]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .adapters.jev import JevClient
from .benchmark.loader import DEFAULT_BENCHMARK
from .config import load_env
from .evaluation.score_run import score_run
from .evaluation.semantic_jev import JevJudge
from .reporting.results import write_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Score one or more run directories")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--jev", choices=["off", "live"], default="off", help="live calls the Jev API (costs money)")
    a = ap.parse_args(argv)
    load_env()
    judge = JevJudge(JevClient()) if a.jev == "live" else None
    for r in a.runs:
        results = score_run(Path(r), judge, DEFAULT_BENCHMARK)
        agg = write_report(Path(r), results)
        print(f"{agg['label']}: {agg['quality']['total']}/{agg['quality']['max']}"
              f"{' (provisional: ' + ', '.join(agg['provisional_reasons']) + ')' if agg['provisional'] else ''}; "
              f"critical={agg['critical_failures']['total']}; report: {Path(r) / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
