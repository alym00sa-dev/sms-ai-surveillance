"""Bake-off driver: run every model one after another over the benchmark, then score everything.

  python -m src.bakeoff run   --out DIR [--models a b ...] [--scenarios ...] [--max-usd 15] [--resume]
  python -m src.bakeoff score DIR [--jev live|off]
  python -m src.bakeoff all   --out DIR ...            # run, then score

Layout: DIR/bakeoff.json, DIR/runs/<model_key>/{run_config,summary}.json + scenarios/, then scores/ and report.md per
run and DIR/comparison.{md,json}. Runs are sequential; a circuit breaker stops a model after 3 consecutive
infrastructure errors; --max-usd stops everything when known cost passes the cap.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .adapters.jev import JevClient
from .adapters.registry import build_adapter
from .benchmark.loader import DEFAULT_BENCHMARK, load_benchmark
from .benchmark.runner import run_benchmark
from .config import load_env, load_models
from .evaluation.aggregate import aggregate
from .evaluation.score_run import score_run
from .evaluation.semantic_jev import JevJudge
from .prompts import load_bundle
from .reporting.comparison import write_comparison
from .reporting.results import write_report
from .schemas.benchmark_case import validate_benchmark

CONSECUTIVE_INFRA_LIMIT = 3
EST_CALLS_PER_MODEL, EST_IN_TOKENS, EST_OUT_TOKENS = 80, 4500, 1000   # deliberately generous (reasoning models)


def estimate_cost(cfg: dict) -> float | None:
    p = cfg.get("pricing")
    if not p:
        return None
    return EST_CALLS_PER_MODEL * (EST_IN_TOKENS * p["input_per_mtok"] + EST_OUT_TOKENS * p["output_per_mtok"]) / 1e6


def _spent(out_dir: Path) -> float:
    total = 0.0
    for s in (out_dir / "runs").glob("*/summary.json"):
        c = json.loads(s.read_text())["totals"]["cost_usd"]
        total += c or 0.0
    return total


def run_bakeoff(adapters, scenarios: list[dict], out_dir: Path, max_extra_turns: int = 3, max_usd: float | None = None,
                resume: bool = False, benchmark_path: Path = DEFAULT_BENCHMARK, log=print) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle = load_bundle()
    meta = {"started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "scenario_ids": [s["id"] for s in scenarios],
            "max_usd": max_usd, "models": []}
    for ad in adapters:
        base_spent = _spent(out_dir)

        def should_stop(rows, base=base_spent):
            if len(rows) >= CONSECUTIVE_INFRA_LIMIT and all(r["termination"] == "INFRA_ERROR" for r in rows[-CONSECUTIVE_INFRA_LIMIT:]):
                return f"{CONSECUTIVE_INFRA_LIMIT} consecutive infrastructure errors"
            if max_usd is not None:
                cur = sum(r["cost_usd"] or 0 for r in rows)
                if base + cur > max_usd:
                    return f"budget cap ${max_usd} reached (spent ${base + cur:.2f})"
            return None

        log(f"== {ad.key} ({ad.model})")
        t0 = datetime.now(timezone.utc)
        out = run_benchmark(ad, scenarios, bundle, out_dir / "runs", benchmark_path, run_id=ad.key,
                            max_extra_turns=max_extra_turns, resume=resume, should_stop=should_stop)
        s = json.loads((out / "summary.json").read_text())
        entry = {"model_key": ad.key, "model": ad.model, "run_dir": str(out.relative_to(out_dir)), "aborted": s["aborted"],
                 "totals": s["totals"], "wall_seconds": round((datetime.now(timezone.utc) - t0).total_seconds(), 1)}
        meta["models"].append(entry)
        log(f"   {s['totals']['terminations']} cost=${s['totals']['cost_usd']} aborted={s['aborted']}")
        (out_dir / "bakeoff.json").write_text(json.dumps(meta, indent=2))
        if s["aborted"] and s["aborted"].startswith("budget cap"):
            log("   budget cap reached: stopping the bake-off")
            break
    meta["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out_dir / "bakeoff.json").write_text(json.dumps(meta, indent=2))
    return meta


def score_bakeoff(out_dir: Path, judge, log=print, tag: str = "", cache_from: str | None = None) -> dict:
    runs = []
    for d in sorted((out_dir / "runs").iterdir()):
        if not (d / "run_config.json").exists():
            continue
        results = score_run(d, judge, DEFAULT_BENCHMARK, tag=tag, cache_from=cache_from)
        agg = write_report(d, results, tag=tag)
        cfg = json.loads((d / "run_config.json").read_text())
        runs.append((cfg, results, agg))
        log(f"{agg['label']}: {agg['quality']['total']}/{agg['quality']['max']} critical={agg['critical_failures']['total']}"
            f"{' (provisional)' if agg['provisional'] else ''}")
    order = {k: i for i, k in enumerate(load_models()["models"])}
    runs.sort(key=lambda r: order.get(r[0]["adapter"]["key"], 99))
    return write_comparison(out_dir, runs, tag=tag)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score", "all"])
    ap.add_argument("dir", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--models", nargs="*")
    ap.add_argument("--scenarios", nargs="*", default=["all"])
    ap.add_argument("--max-usd", type=float, default=None)
    ap.add_argument("--max-extra-turns", type=int, default=3)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--jev", choices=["off", "live"], default="live")
    ap.add_argument("--tag", default="", help="scoring output suffix, e.g. v0_2")
    ap.add_argument("--cache-from", default=None, help="earlier scores dir whose identical Jev judgments are reused")
    ap.add_argument("--yes", action="store_true", help="skip the cost confirmation line (non-interactive)")
    a = ap.parse_args(argv)
    load_env()
    out = Path(a.out or a.dir or "")
    if a.cmd in ("run", "all"):
        if not a.out:
            print("--out is required", file=sys.stderr)
            return 2
        cfgs = load_models()["models"]
        keys = a.models or [k for k, c in cfgs.items() if c.get("enabled", True)]
        bad = [k for k in keys if not cfgs.get(k, {}).get("enabled", True)]
        if bad or any(k not in cfgs for k in keys):
            print(f"unknown or disabled models: {bad}", file=sys.stderr)
            return 2
        rows = load_benchmark()
        validate_benchmark(rows)
        scen = rows if a.scenarios == ["all"] else [r for r in rows if r["id"] in set(a.scenarios)]
        est = {k: estimate_cost(cfgs[k]) for k in keys}
        print("Planned (sequential): " + ", ".join(f"{k} (~${v:.2f})" if v is not None else k for k, v in est.items()))
        print(f"Generous upper-bound estimate: ${sum(v for v in est.values() if v is not None):.2f} for {len(scen)} scenarios x {len(keys)} models")
        adapters = [build_adapter(k, cfgs[k]) for k in keys]
        run_bakeoff(adapters, scen, out, a.max_extra_turns, a.max_usd, a.resume)
    if a.cmd in ("score", "all"):
        judge = JevJudge(JevClient()) if a.jev == "live" else None
        score_bakeoff(out, judge, tag=a.tag, cache_from=a.cache_from)
        print(f"comparison: {out / 'comparison.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
