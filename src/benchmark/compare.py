"""Deterministic case-state comparison against gold (field semantics: omitted = not scored,
null = must stay unresolved, value = must match). Symptoms are not compared here (Jev)."""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field

from .location_fixture import load_fixture
from .symptoms import extract_features, load_symptom_features, satisfies

FIELDS = ("age", "sex", "state", "lga", "settlement", "symptom")
_PLACE_WORDS = {"village", "town", "community", "lga", "state", "local", "government", "area"}


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).casefold()).strip()


def age_interval(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return (float(v), float(v))
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(v))]
    return (min(nums), max(nums)) if nums else None


def age_matches(gold, model) -> bool:
    g, m = age_interval(gold), age_interval(model)
    return g is not None and m is not None and g[0] <= m[0] and m[1] <= g[1]


@dataclass
class Comparison:
    diffs: list[dict] = field(default_factory=list)
    pairs: list[tuple[int, int]] = field(default_factory=list)  # (gold index, model index) of the best alignment

    @property
    def ok(self) -> bool:
        return not self.diffs


class _Index:
    def __init__(self, fx: dict):
        self.settlements = {_norm(k): v for k, v in fx["settlements"].items()}
        self.partial = {_norm(k): v for k, v in fx["partial"].items()}
        self.ambiguous = {_norm(k): v for k, v in fx["ambiguous"].items()}
        self.lga_state = {_norm(k): v["state"] for k, v in fx["lga_level"].items()}
        self.alias = {_norm(a): _norm(c) for a, c in fx["aliases"].items()}

    def canon(self, s) -> str:
        n = " ".join(w for w in _norm(s).split() if w not in _PLACE_WORDS)
        return self.alias.get(n, n)

    def lga_equal(self, a, b, entry=None) -> bool:
        accepted = {self.canon(a)} | {self.canon(x) for x in (entry or {}).get("lga_aliases", [])}
        return self.canon(b) in accepted or self.canon(a) == self.canon(b)


def _case_diffs(gi: int, g: dict, m: dict, ix: _Index, sf: dict | None = None) -> list[dict]:
    out = []

    def add(kind, f, gold, model):
        out.append({"case": gi, "field": f, "kind": kind, "gold": gold, "model": model})

    for f in ("age", "sex"):
        if f not in g:
            continue
        mv = m.get(f)
        if f == "sex" and mv == "unknown":
            mv = None
        if g[f] is None:
            if mv is not None:
                add("should_be_null", f, None, mv)
        elif mv is None:
            add("missing_value", f, g[f], None)
        elif (f == "age" and not age_matches(g[f], mv)) or (f == "sex" and _norm(g[f]) != _norm(mv)):
            add("wrong_value", f, g[f], mv)

    if sf is not None and g.get("symptom"):
        gf = sf[g["symptom"]]  # KeyError on an unmapped gold symptom is deliberate
        if any(v for v in gf.values()):
            if not m.get("symptom"):
                add("missing_value", "symptom", g["symptom"], None)
            elif not satisfies(gf, extract_features(m["symptom"])):
                add("symptom_mismatch", "symptom", g["symptom"], m["symptom"])

    ref = g.get("settlement") or m.get("settlement")
    ref_n = ix.canon(ref) if ref else None
    entry = ix.settlements.get(ref_n) if ref_n else None
    for f in ("settlement", "lga", "state"):
        mv = m.get(f)
        if f in g:
            if g[f] is None:
                if mv is not None:
                    add("should_be_null", f, None, mv)
            elif mv is None:
                add("missing_value", f, g[f], None)
            elif f == "lga":
                if not ix.lga_equal(g[f], mv, entry):
                    add("wrong_value", f, g[f], mv)
            elif ix.canon(g[f]) != ix.canon(mv):
                add("wrong_value", f, g[f], mv)
            continue
        if f == "settlement" or mv is None:
            continue  # omitted gold: not scored, except fixture checks on non-null values below
        if entry is not None:
            if f == "state" and ix.canon(mv) != ix.canon(entry["state"]):
                add("fabricated", f, entry["state"], mv)
            elif f == "lga" and not ix.lga_equal(entry["lga"], mv, entry):
                add("fabricated", f, entry["lga"], mv)
        elif f == "state" and g.get("lga") and ix.canon(g["lga"]) in ix.lga_state:
            if ix.canon(mv) != ix.canon(ix.lga_state[ix.canon(g["lga"])]):
                add("fabricated", f, ix.lga_state[ix.canon(g["lga"])], mv)
        elif ref_n in ix.partial:
            p = ix.partial[ref_n]
            if (f == "state" and ix.canon(mv) != ix.canon(p["state"])) or f == "lga":
                add("fabricated", f, p["state"] if f == "state" else None, mv)
        elif ref_n in ix.ambiguous:
            add("fabricated", f, None, mv)
    return out


def compare_cases(model_cases, gold_cases, fixture: dict | None = None, symptom_features: dict | None = None,
                  check_symptom: bool = True) -> Comparison:
    ix = _Index(fixture or load_fixture())
    sf = (symptom_features or load_symptom_features()) if check_symptom else None
    model_cases = model_cases or []
    k = min(len(gold_cases), len(model_cases))
    best = None
    for gsel in itertools.combinations(range(len(gold_cases)), k):
        for msel in itertools.permutations(range(len(model_cases)), k):
            d = [x for gi, mi in zip(gsel, msel) for x in _case_diffs(gi, gold_cases[gi], model_cases[mi], ix, sf)]
            if best is None or len(d) < len(best[0]):
                best = (d, set(gsel), list(zip(gsel, msel)))
    diffs, matched, pairs = best
    for gi in range(len(gold_cases)):
        if gi not in matched:
            diffs.append({"case": gi, "field": None, "kind": "missing_case", "gold": gold_cases[gi], "model": None})
    for _ in range(len(model_cases) - len(gold_cases)):
        diffs.append({"case": None, "field": None, "kind": "extra_case", "gold": None, "model": None})
    return Comparison(diffs, pairs)
