"""Aggregate scenario scores into per-model tables (harness README section 25)."""
from __future__ import annotations

import statistics

DIMS = ["classification", "extraction_state", "action", "conversation_quality", "escalation_priority", "output_adherence"]


def aggregate(results: list[dict], run_config: dict | None = None, label: str | None = None) -> dict:
    scored = [r for r in results if r["status"] == "SCORED"]
    n = len(scored)
    dim_tot = {d: sum(r["scores"][d] for r in scored) for d in DIMS}
    crit_codes: dict[str, int] = {}
    for r in scored:
        for c in r["score"]["critical_failures"]:
            crit_codes[c] = crit_codes.get(c, 0) + 1
    lat = [r["metrics"]["latency_ms_total"] for r in scored]
    costs = [r["metrics"]["cost_usd"] for r in scored]
    turns = sum(r["metrics"]["model_turns"] for r in scored)
    jev = [j for r in scored for j in r["judgments"] if j["source"] == "jev"]
    jev_err = [e for r in scored for e in r["jev_errors"]]
    rc = [r["resolver_compliance"] for r in scored]
    rc_turns = sum(x["turns_checked"] for x in rc)
    return {
        "label": label or (run_config or {}).get("run_id") or (scored[0]["model"] if scored else "unknown"),
        "architecture_mode": (run_config or {}).get("architecture_mode", "end_to_end_llm"),
        "model": ((run_config or {}).get("adapter") or {}).get("model"),
        "scenarios_total": len(results), "scenarios_scored": n,
        "unscored_infra": [r["scenario_id"] for r in results if r["status"] == "UNSCORED_INFRA"],
        "provisional": any(r.get("provisional") for r in scored),
        "provisional_reasons": sorted({x for r in scored for x in r.get("provisional_reasons", [])}),
        "quality": {"total": sum(r["total"] for r in scored), "max": 12 * n},
        "dimensions": {d: {"total": dim_tot[d], "max": 2 * n} for d in DIMS},
        "critical_failures": {"scenarios_with_failures": sum(1 for r in scored if r["score"]["critical_failures"]),
                              "total": sum(crit_codes.values()), "by_code": dict(sorted(crit_codes.items())),
                              "scenarios": {r["scenario_id"]: r["score"]["critical_failures"] for r in scored if r["score"]["critical_failures"]}},
        "operational": {
            "avg_model_turns": (turns / n) if n else None,
            "avg_clarification_turns": (sum(r["metrics"]["clarification_turns"] for r in scored) / n) if n else None,
            "avg_confirmation_turns": (sum(r["metrics"]["confirmation_turns"] for r in scored) / n) if n else None,
            "avg_latency_ms": statistics.mean(lat) if lat else None, "median_latency_ms": statistics.median(lat) if lat else None,
            "avg_cost_usd": None if not scored or any(c is None for c in costs) else statistics.mean(costs),
            "schema_retry_rate": (sum(r["metrics"]["schema_retries"] for r in scored) / turns) if turns else None,
            "schema_failure_rate_first_attempt": (sum(r["metrics"]["schema_failures_first_attempt"] for r in scored) / turns) if turns else None,
            "harness_corrections": sum(r["metrics"]["harness_corrections"] for r in scored)},
        "terminations": {k: sum(1 for r in results if r["termination"].get("reason") == k)
                         for k in sorted({r["termination"].get("reason") for r in results})},
        "resolver_compliance": {"turns": rc_turns, "noncompliant": sum(x["noncompliant_turns"] for x in rc),
                                "rate": (sum(x["noncompliant_turns"] for x in rc) / rc_turns) if rc_turns else None},
        "jev": {"judgments": len(jev), "low_confidence": sum(1 for j in jev if j.get("low_confidence")), "errors": len(jev_err),
                "cost_usd": sum(j.get("cost_usd") or 0 for j in jev)} if (jev or jev_err) else None,
    }


def compare_architectures(baseline: dict, candidate: dict) -> dict:
    """Side-by-side of an end-to-end LLM baseline and a Jev-assisted configuration (harness README section 25).
    Both must be aggregates over the same benchmark; the candidate is labelled an architecture, not a model."""
    pick = lambda a: {
        "label": a["label"], "architecture_mode": a["architecture_mode"], "quality": a["quality"],
        "dimensions": {d: a["dimensions"][d] for d in DIMS},
        "critical_failures": a["critical_failures"]["total"],
        "avg_turns": a["operational"]["avg_model_turns"], "avg_latency_ms": a["operational"]["avg_latency_ms"],
        "avg_cost_usd": a["operational"]["avg_cost_usd"], "schema_retry_rate": a["operational"]["schema_retry_rate"]}
    b, c = pick(baseline), pick(candidate)
    delta = {"quality": c["quality"]["total"] - b["quality"]["total"], "critical_failures": c["critical_failures"] - b["critical_failures"],
             "dimensions": {d: c["dimensions"][d]["total"] - b["dimensions"][d]["total"] for d in DIMS}}
    for k in ("avg_turns", "avg_latency_ms", "avg_cost_usd", "schema_retry_rate"):
        delta[k] = None if b[k] is None or c[k] is None else c[k] - b[k]
    return {"baseline": b, "candidate": c, "delta_candidate_minus_baseline": delta,
            "comparable": baseline["scenarios_scored"] == candidate["scenarios_scored"]}
