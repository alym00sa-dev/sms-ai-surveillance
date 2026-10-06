"""Deterministic symptom features for the confirmation gate (v0.1).

Gold side: frozen lookup in data/symptom_features_v0_1.json (keyed by gold symptom string).
Model side: this small keyword extractor over the model's `symptom` text. Only three features are
compared (body region, laterality, sudden onset); finer fidelity is judged later by Jev.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

DEFAULT_FEATURES = Path(__file__).resolve().parents[2] / "data" / "symptom_features_v0_1.json"
_LEG = {"leg", "legs", "foot", "feet"}
_ARM = {"arm", "arms", "hand", "hands"}
_PLURAL = {"legs", "arms", "hands", "feet"}
_ONE = {"one", "single", "unilateral", "either"}
_BOTH = {"both", "bilateral", "two"}
_SUDDEN = {"sudden", "suddenly", "abrupt", "abruptly", "acute", "acutely", "overnight", "today", "morning"}


def load_symptom_features(path: Path | str | None = None) -> dict:
    with open(path or DEFAULT_FEATURES, encoding="utf-8") as f:
        return json.load(f)["features"]


def extract_features(text: str | None) -> dict:
    toks = re.findall(r"[a-z]+", (text or "").casefold())
    t = set(toks)
    regions = [r for r, words in (("leg", _LEG), ("arm", _ARM)) if t & words]
    side = [x for x in ("left", "right") if x in t]
    lat = set(side)
    if t & _ONE or side:
        lat.add("one")
    if t & _BOTH:
        lat.add("both")
    elif t & _PLURAL and not (t & _ONE or side):
        lat.add("both")
    return {"body_region": sorted(regions), "laterality": sorted(lat), "onset": "sudden" if t & _SUDDEN else None}


def satisfies(gold: dict, model: dict) -> bool:
    """Every non-null gold feature must be satisfied by the model features."""
    if gold.get("body_region") and gold["body_region"] not in model["body_region"]:
        return False
    g = gold.get("laterality")
    if g == "one" and not ({"one", "left", "right"} & set(model["laterality"])):
        return False
    if g in ("both", "left", "right") and g not in model["laterality"]:
        return False
    if gold.get("onset") == "sudden" and model["onset"] != "sudden":
        return False
    return True
