"""Benchmark loading."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_BENCHMARK = Path(__file__).resolve().parents[2] / "data" / "sms_ai_benchmark_v0_3_1.jsonl"


def load_benchmark(path: Path | str | None = None) -> list[dict]:
    with open(path or DEFAULT_BENCHMARK, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
