"""Preflight: cheap checks before a bake-off.

  python -m src.preflight --models haiku-4-5 gpt-6-luna ...        # tiny "ping" per model with the configured params
  python -m src.preflight --models gpt-6.1-sol --smoke              # + one real AFP-01 scenario per model

The ping uses the same adapter and parameters as the benchmark (including temperature) but no schema and a trivial
prompt, so it shows whether the API accepts the configured parameters for essentially no cost.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.base import AdapterRequest
from .adapters.registry import build_adapter
from .benchmark.loader import DEFAULT_BENCHMARK, load_benchmark
from .benchmark.runner import run_benchmark
from .config import ROOT, load_env, load_models
from .prompts import load_bundle


def ping(adapter) -> dict:
    r = adapter.complete(AdapterRequest("Reply with the single word OK.", [{"role": "user", "content": "ping"}], None))
    out = {"model_key": adapter.key, "model": adapter.model, "ok": r.error is None, "latency_ms": round(r.latency_ms),
           "usage": r.usage, "cost_usd": r.cost_usd, "temperature_sent": adapter.cfg.get("params", {}).get("temperature")}
    if r.error:
        out["error"] = {"kind": r.error.kind, "status": r.error.status_code, "message": r.error.message[:300]}
    else:
        out["reply"] = (r.text or "")[:40]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--smoke", action="store_true", help="also run one real AFP-01 scenario per model")
    ap.add_argument("--out", default=None, help="directory for smoke runs (default: a scratch dir you choose)")
    a = ap.parse_args(argv)
    load_env()
    models = load_models()["models"]
    results = []
    for k in a.models:
        cfg = models[k]
        if not cfg.get("enabled", True):
            print(f"{k}: excluded ({cfg.get('excluded_reason')})")
            continue
        ad = build_adapter(k, cfg)
        res = ping(ad)
        results.append(res)
        print(json.dumps(res))
        if a.smoke and res["ok"]:
            scen = [s for s in load_benchmark() if s["id"] == "AFP-01"]
            out = run_benchmark(ad, scen, load_bundle(), Path(a.out or ROOT / "results" / "_preflight"), DEFAULT_BENCHMARK)
            s = json.loads((out / "summary.json").read_text())
            print(f"  smoke AFP-01: {s['scenarios'][0]['termination']} actions={s['scenarios'][0]['model_actions']} "
                  f"cost={s['scenarios'][0]['cost_usd']} dir={out}")
    return 0 if all(r["ok"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
