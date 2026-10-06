"""Markdown tables for scored runs."""
from __future__ import annotations

from ..evaluation.aggregate import DIMS

_SHORT = {"classification": "Classification", "extraction_state": "Extraction/state", "action": "Action",
          "conversation_quality": "Conversation", "escalation_priority": "Escalation", "output_adherence": "Output"}


def _f(x, nd=1, suffix=""):
    return "n/a" if x is None else f"{x:.{nd}f}{suffix}"


def aggregate_table(aggs: list[dict]) -> str:
    head = ("| Model | Quality | " + " | ".join(_SHORT[d] for d in DIMS) +
            " | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |")
    sep = "|---|---:|" + "---:|" * len(DIMS) + "---:|---:|---:|---:|---:|---|"
    rows = [head, sep]
    for a in aggs:
        o = a["operational"]
        rows.append(f"| {a['label']} | {a['quality']['total']}/{a['quality']['max']} | " +
                    " | ".join(f"{a['dimensions'][d]['total']}/{a['dimensions'][d]['max']}" for d in DIMS) +
                    f" | {a['critical_failures']['total']} ({a['critical_failures']['scenarios_with_failures']} scen.) | {_f(o['avg_model_turns'])} | "
                    f"{_f(None if o['avg_latency_ms'] is None else o['avg_latency_ms'] / 1000, 1)} | {_f(o['avg_cost_usd'], 4)} | "
                    f"{_f(None if o['schema_retry_rate'] is None else 100 * o['schema_retry_rate'], 1, '%')} | "
                    f"{'yes: ' + ', '.join(a['provisional_reasons']) if a['provisional'] else 'no'} |")
    return "\n".join(rows)


def scenario_table(results: list[dict]) -> str:
    rows = ["| Scenario | Total | " + " | ".join(_SHORT[d] for d in DIMS) + " | Ended | Critical | Notes |",
            "|---|---:|" + "---:|" * len(DIMS) + "---|---|---|"]
    for r in results:
        if r["status"] != "SCORED":
            rows.append(f"| {r['scenario_id']} | – | " + " | ".join("–" for _ in DIMS) + f" | {r['termination'].get('reason')} | | UNSCORED: {'; '.join(r['notes'])} |")
            continue
        notes = "; ".join(n for n in r["notes"])[:300]
        rows.append(f"| {r['scenario_id']} | {r['total']}/12 | " + " | ".join(str(r["scores"][d]) for d in DIMS) +
                    f" | {r['termination'].get('reason')} | {', '.join(r['score']['critical_failures']) or '–'} | {notes} |")
    return "\n".join(rows)


def critical_table(results: list[dict]) -> str:
    rows = ["| Scenario | Code | Turn | Detail |", "|---|---|---:|---|"]
    for r in results:
        for f in r.get("critical_findings", []):
            rows.append(f"| {r['scenario_id']} | {f['code']} | {f['turn'] or '–'} | {f['detail']} |")
    return "\n".join(rows) if len(rows) > 2 else "No critical failures."


def architecture_table(cmp: dict) -> str:
    b, c, d = cmp["baseline"], cmp["candidate"], cmp["delta_candidate_minus_baseline"]
    L = ["| Metric | " + b["label"] + " (end-to-end LLM) | " + c["label"] + " (Jev-assisted architecture) | Delta |", "|---|---:|---:|---:|",
         f"| Quality | {b['quality']['total']}/{b['quality']['max']} | {c['quality']['total']}/{c['quality']['max']} | {d['quality']:+d} |"]
    for k in DIMS:
        L.append(f"| {_SHORT[k]} | {b['dimensions'][k]['total']} | {c['dimensions'][k]['total']} | {d['dimensions'][k]:+d} |")
    L.append(f"| Critical failures | {b['critical_failures']} | {c['critical_failures']} | {d['critical_failures']:+d} |")
    for k, nd in (("avg_turns", 2), ("avg_latency_ms", 0), ("avg_cost_usd", 4), ("schema_retry_rate", 3)):
        L.append(f"| {k} | {_f(b[k], nd)} | {_f(c[k], nd)} | {_f(d[k], nd)} |")
    return "\n".join(L)
