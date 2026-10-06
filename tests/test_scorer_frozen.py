"""Frozen-scorer guards.

* archive/scorer_v0_1/ must stay byte-identical to what was frozen as scorer v0.1 (the first bake-off was scored with it).
* The live scorer files must match data/SCORER_FREEZE_v0_2.json. A change means scorer v0.3 and a new freeze.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def test_scorer_v0_1_archive_intact():
    fr = json.loads((ROOT / "archive" / "scorer_v0_1" / "SCORER_FREEZE_v0_1.json").read_text())
    changed = [f for f, s in fr["files"].items() if sha(ROOT / "archive" / "scorer_v0_1" / f) != s]
    assert not changed, f"archived v0.1 files changed: {changed}"


def test_scorer_v0_2_files_unchanged():
    fr = json.loads((ROOT / "data" / "SCORER_FREEZE_v0_2.json").read_text())
    changed = [f for f, s in fr["files"].items() if sha(ROOT / f) != s]
    assert not changed, f"frozen scorer files changed: {changed}; bump to scorer v0.3 and re-freeze"
    from src.evaluation.score_run import SCORER_VERSION
    assert SCORER_VERSION == fr["scorer_version"] == "v0.2"
