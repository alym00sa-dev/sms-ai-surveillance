"""Scenario runner: envelope -> model -> validate (one schema retry) -> scripted sender -> persist.

Failure classes are kept apart:
  * infrastructure / API errors  -> termination INFRA_ERROR   (not a model-quality failure)
  * unusable structured output   -> termination OUTPUT_INVALID (after one retry)
  * model-behavior outcomes      -> sender terminations (COMPLETED, PREMATURE_TERMINAL, MAX_TURNS, ...)
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from ..adapters.base import AdapterRequest, ModelAdapter
from ..prompts import PromptBundle
from ..schemas.model_output import MODEL_OUTPUT_JSON_SCHEMA, parse_json_text, validate_output
from .envelope import build_envelope
from .location_fixture import RESOLVER_VERSION, LocationResolver, load_fixture
from .scripted_user import ScriptedUser

ROOT = Path(__file__).resolve().parents[2]
SENDER_POLICY_VERSION = "v0.1"
SCHEMA_RETRIES = 1


def file_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git_commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def _call_model(adapter: ModelAdapter, bundle: PromptBundle, envelope: dict, ctx: dict) -> tuple[dict | None, str, list[dict]]:
    """Returns (parsed_output | None, status, attempt_records). status: OK | INFRA_ERROR | OUTPUT_INVALID."""
    messages = [{"role": "user", "content": json.dumps(envelope, ensure_ascii=False)}]
    records: list[dict] = []
    for n in range(1 + SCHEMA_RETRIES):
        resp = adapter.complete(AdapterRequest(bundle.system_text, messages, MODEL_OUTPUT_JSON_SCHEMA, ctx))
        rec = {"attempt": n + 1, "request_params": resp.request_params, "messages_sent": messages,
               "structured_output_mode": resp.structured_output_mode, "raw_text": resp.text, "raw_response": resp.raw,
               "usage": resp.usage, "latency_ms": round(resp.latency_ms, 1), "cost_usd": resp.cost_usd,
               "stop_reason": resp.stop_reason, "request_id": resp.request_id, "model": resp.model}
        if resp.error:
            rec["infra_error"] = asdict(resp.error)
            records.append(rec)
            return None, "INFRA_ERROR", records
        try:
            obj, parse_warnings = parse_json_text(resp.text)
            vr = validate_output(obj)
            errors, warnings = vr.errors, parse_warnings + vr.warnings
        except Exception as e:  # JSON parse failure or empty response
            vr, errors, warnings = None, [f"json: {type(e).__name__}: {e}"], []
        if resp.stop_reason == "max_tokens":
            errors = errors + ["stop_reason=max_tokens (truncated)"]
        rec["validation"] = {"ok": not errors, "errors": errors, "warnings": warnings}
        records.append(rec)
        if not errors:
            return vr.parsed, "OK", records
        messages = messages + [
            {"role": "assistant", "content": resp.text or "(empty)"},
            {"role": "user", "content": "Your previous output was invalid: " + "; ".join(errors[:5]) +
             ". Return only the corrected JSON object per the output contract."}]
    return None, "OUTPUT_INVALID", records


def run_scenario(adapter: ModelAdapter, scenario: dict, bundle: PromptBundle, fixture: dict | None = None,
                 resolver: LocationResolver | None = None, max_extra_turns: int = 3) -> dict:
    fixture = fixture or load_fixture()
    resolver = resolver or LocationResolver(fixture)
    sender = ScriptedUser(scenario, fixture, max_extra_turns=max_extra_turns)
    conversation = [{"role": "user", "content": sender.first_message}]
    state: dict = {"cases": []}
    turns: list[dict] = []
    termination: dict = {}
    for n in range(sender.max_model_turns + 1):
        envelope = build_envelope(conversation, state, sender.clarification_attempts,
                                  scenario["prior_reports"], resolver)
        ctx = {"scenario": scenario, "sender": sender}
        out, status, attempts = _call_model(adapter, bundle, envelope, ctx)
        turn = {"turn": n + 1, "gold_cursor": sender.cursor, "gold_action": sender.expected["action"],
                "sender_message": conversation[-1]["content"], "envelope": envelope, "attempts": attempts,
                "status": status, "output": out, "reply": None,
                "clarification_attempts_before": sender.clarification_attempts}
        turns.append(turn)
        if status == "INFRA_ERROR":
            termination = {"reason": "INFRA_ERROR", "detail": attempts[-1]["infra_error"]}
            break
        if status == "OUTPUT_INVALID":
            termination = {"reason": "OUTPUT_INVALID", "detail": attempts[-1]["validation"]["errors"]}
            break
        state = {"cases": out["cases"]}
        conversation.append({"role": "assistant", "content": out["response"]})
        reply = sender.respond(out)
        turn["reply"] = {"kind": reply.kind, "text": reply.text, "reason": reply.reason, "detail": reply.detail,
                         "events": reply.events, "meta": reply.meta}
        turn["clarification_attempts_after"] = sender.clarification_attempts
        if reply.kind == "TERMINATE":
            termination = {"reason": reply.reason, "detail": reply.detail}
            break
        conversation.append({"role": "user", "content": reply.text})
    return {
        "scenario_id": scenario["id"], "title": scenario["title"], "model_key": adapter.key,
        "termination": termination, "turns": turns, "conversation": conversation, "final_state": state,
        "gold_actions": [t["expected"]["action"] for t in scenario["turns"]],
        "model_actions": [t["output"]["action"] for t in turns if t["output"]],
        "metrics": _metrics(turns, sender),
    }


def _metrics(turns: list[dict], sender: ScriptedUser) -> dict:
    atts = [a for t in turns for a in t["attempts"]]
    costs = [a["cost_usd"] for a in atts]
    acts = [t["output"]["action"] for t in turns if t["output"]]
    return {
        "model_turns": len(turns), "api_calls": len(atts),
        "schema_retries": sum(1 for t in turns if len(t["attempts"]) > 1),
        "schema_failures_first_attempt": sum(1 for t in turns if not t["attempts"][0].get("validation", {"ok": True})["ok"]),
        "latency_ms_total": round(sum(a["latency_ms"] for a in atts), 1),
        "input_tokens": sum(a["usage"].get("input_tokens", 0) for a in atts),
        "output_tokens": sum(a["usage"].get("output_tokens", 0) for a in atts),
        "cost_usd": None if any(c is None for c in costs) else round(sum(costs), 6),
        "clarification_turns": acts.count("CLARIFY"), "confirmation_turns": acts.count("CONFIRM"),
        "harness_corrections": sender.corrections, "clarification_attempts_final": sender.clarification_attempts,
    }


def run_config(adapter: ModelAdapter, bundle: PromptBundle, benchmark_path: Path, extra: dict | None = None) -> dict:
    manifest = json.loads((ROOT / "data" / "FROZEN_MANIFEST.json").read_text())["artifacts"]
    return {
        "run_started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "architecture_mode": "end_to_end_llm", "adapter": adapter.describe(),
        "prompt_version": bundle.version, "prompt_hashes": bundle.hashes(),
        "output_schema_sha256": hashlib.sha256(json.dumps(MODEL_OUTPUT_JSON_SCHEMA, sort_keys=True).encode()).hexdigest(),
        "benchmark": {"version": "v0.3.1", "path": str(benchmark_path.relative_to(ROOT)), "sha256": file_sha256(benchmark_path)},
        "location_fixture": {"path": "data/location_fixture_v0_1.json", "sha256": file_sha256(ROOT / "data/location_fixture_v0_1.json"),
                             "resolver_version": RESOLVER_VERSION},
        "symptom_features": {"path": "data/symptom_features_v0_1.json", "sha256": file_sha256(ROOT / "data/symptom_features_v0_1.json")},
        "critical_check_mapping": {"version": "v0.1", "sha256": manifest["critical_check_mapping"]["sha256"]},
        "scorer_version": "v0.1", "scorer_contract_sha256": file_sha256(ROOT / "SMS_AI_SURVEILLANCE_SCORER_CONTRACT_v0_1.md"),
        "sender_policy_version": SENDER_POLICY_VERSION, "schema_retries_allowed": SCHEMA_RETRIES,
        "jev_evaluator": None, "jev_decisioning": None,
        "git_commit": _git_commit(), "python": platform.python_version(), "platform": platform.platform(),
        **(extra or {}),
    }


def run_benchmark(adapter: ModelAdapter, scenarios: list[dict], bundle: PromptBundle, results_dir: Path,
                  benchmark_path: Path, run_id: str | None = None, max_extra_turns: int = 3,
                  resume: bool = False, should_stop=None) -> Path:
    """Run scenarios one after another. `resume` keeps scenarios already saved without an INFRA_ERROR;
    `should_stop(rows) -> reason | None` is checked after each scenario (circuit breaker / budget)."""
    run_id = run_id or f"{adapter.key}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    out_dir = Path(results_dir) / run_id
    (out_dir / "scenarios").mkdir(parents=True, exist_ok=True)
    cfg = run_config(adapter, bundle, benchmark_path, {"run_id": run_id, "max_extra_turns": max_extra_turns,
                                                         "scenario_ids": [s["id"] for s in scenarios]})
    if not (resume and (out_dir / "run_config.json").exists()):
        (out_dir / "run_config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
    fixture = load_fixture()
    resolver = LocationResolver(fixture)
    rows, aborted = [], None
    for sc in scenarios:
        path = out_dir / "scenarios" / f"{sc['id']}.json"
        res = None
        if resume and path.exists():
            old = json.loads(path.read_text())
            if old["termination"].get("reason") != "INFRA_ERROR":
                res = old
        if res is None:
            res = run_scenario(adapter, sc, bundle, fixture, resolver, max_extra_turns)
            path.write_text(json.dumps(res, indent=2, ensure_ascii=False))
        rows.append({"scenario_id": sc["id"], "termination": res["termination"].get("reason"),
                     "gold_actions": res["gold_actions"], "model_actions": res["model_actions"], **res["metrics"]})
        if should_stop and (aborted := should_stop(rows)):
            break
    totals = {"scenarios": len(rows), "cost_usd": None if any(r["cost_usd"] is None for r in rows) else round(sum(r["cost_usd"] for r in rows), 6),
              "latency_ms_total": round(sum(r["latency_ms_total"] for r in rows), 1),
              "input_tokens": sum(r["input_tokens"] for r in rows), "output_tokens": sum(r["output_tokens"] for r in rows),
              "terminations": {k: sum(1 for r in rows if r["termination"] == k) for k in sorted({r["termination"] for r in rows})}}
    (out_dir / "summary.json").write_text(json.dumps({"totals": totals, "aborted": aborted, "scenarios": rows}, indent=2))
    return out_dir
