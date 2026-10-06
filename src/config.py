"""Environment and model-config loading. Secrets are read from the environment only and never logged."""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_env(path: Path | str | None = None) -> list[str]:
    """Load KEY=VALUE lines into os.environ without overriding existing variables.
    Returns the NAMES of variables that were set (never values)."""
    p = Path(path or ROOT / ".env")
    loaded = []
    if not p.exists():
        return loaded
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().removeprefix("export ").strip(), v.strip().strip("'\"")
        if v and k not in os.environ:
            os.environ[k] = v
            loaded.append(k)
    return loaded


def load_models(path: Path | str | None = None) -> dict:
    with open(path or ROOT / "config" / "models.json", encoding="utf-8") as f:
        return json.load(f)


def compute_cost(usage: dict, pricing: dict | None) -> float | None:
    """USD cost, or None when pricing (or a needed price component) is unknown."""
    if not pricing:
        return None
    parts = [("input_tokens", "input_per_mtok"), ("output_tokens", "output_per_mtok"),
             ("cache_read_input_tokens", "cache_read_per_mtok"), ("cache_creation_input_tokens", "cache_write_per_mtok")]
    total = 0.0
    for ukey, pkey in parts:
        n = usage.get(ukey) or 0
        if n and pricing.get(pkey) is None and ukey == "cache_read_input_tokens" and pricing.get("cache_fallback") == "input_price":
            total += n * pricing["input_per_mtok"] / 1_000_000  # upper bound: cached tokens at the full input price
            continue
        if n and pricing.get(pkey) is None:
            return None
        if n:
            total += n * pricing[pkey] / 1_000_000
    return total
