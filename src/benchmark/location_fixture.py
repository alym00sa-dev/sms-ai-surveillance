"""Deterministic benchmark location resolver.

Its output is sent to every candidate model as `location_resolver` in the input
envelope and is also the scoring reference. It scans sender messages only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RESOLVER_VERSION = "v0.2"  # v0.2: proximity words must directly precede the place name ("around 7 in Majawa" is not proximity)
DEFAULT_FIXTURE = Path(__file__).resolve().parents[2] / "data" / "location_fixture_v0_1.json"

_TOKEN = re.compile(r"[A-Za-z]+")
_PROXIMITY = {"near", "nearby", "around", "beside", "close"}
_SETTLEMENT_NOUNS = {"village", "town", "community"}
_FILLER = {"to", "the", "by", "of"}
FIELDS = ("state", "lga", "settlement")


def load_fixture(path: Path | str | None = None) -> dict:
    with open(path or DEFAULT_FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def _tokens(text: str) -> list[tuple[str, int, int]]:
    return [(m.group().lower(), m.start(), m.end()) for m in _TOKEN.finditer(text)]


class LocationResolver:
    def __init__(self, fixture: dict | None = None):
        self.fx = fixture or load_fixture()
        self._kinds: dict[str, set[str]] = {}
        self._patterns: dict[tuple[str, ...], str] = {}
        for name in (*self.fx["settlements"], *self.fx["partial"], *self.fx["ambiguous"]):
            self._add(name, "S")
        for name in self.fx["lga_level"]:
            self._add(name, "L")
        for name in self.fx["states"]:
            self._add(name, "T")
        for alias, canonical in self.fx["aliases"].items():
            if canonical not in self._kinds:
                raise ValueError(f"alias {alias!r} points to unknown name {canonical!r}")
            self._patterns[tuple(t for t, _, _ in _tokens(alias))] = canonical
        self._max_len = max(len(k) for k in self._patterns)

    def _add(self, name: str, kind: str) -> None:
        self._kinds.setdefault(name, set()).add(kind)
        self._patterns[tuple(t for t, _, _ in _tokens(name))] = name

    # ---- scanning -------------------------------------------------------
    def _scan(self, text: str) -> list[dict]:
        toks = _tokens(text)
        found, i = [], 0
        while i < len(toks):
            for n in range(min(self._max_len, len(toks) - i), 0, -1):
                canonical = self._patterns.get(tuple(t for t, _, _ in toks[i:i + n]))
                if canonical:
                    break
            else:
                i += 1
                continue
            j = i + n
            kinds = self._kinds[canonical]
            nxt = toks[j][0] if j < len(toks) else ""
            nxt2 = toks[j + 1][0] if j + 1 < len(toks) else ""
            level = None
            if (nxt == "lga" or (nxt == "local" and nxt2 == "government")) and "L" in kinds:
                level = "L"
            elif nxt == "state" and "T" in kinds:
                level = "T"
            elif nxt in _SETTLEMENT_NOUNS and "S" in kinds:
                level = "S"
            if level is None:
                level = next(k for k in "SLT" if k in kinds)
            k = i - 1  # a proximity word counts only when it directly precedes the name ("near X", "close to X")
            while k >= 0 and toks[k][0] in _FILLER:
                k -= 1
            found.append({
                "raw": text[toks[i][1]:toks[j - 1][2]],
                "canonical": canonical,
                "level": level,
                "proximity": k >= 0 and toks[k][0] in _PROXIMITY,
            })
            i = j
        return found

    # ---- resolution -----------------------------------------------------
    def resolve(self, user_messages: list[str]) -> dict:
        ments, seen = [], set()
        for msg in user_messages:
            for m in self._scan(msg):
                key = (m["canonical"], m["level"], m["proximity"])
                if key not in seen:
                    seen.add(key)
                    ments.append(m)
        lgas = [m["canonical"] for m in ments if m["level"] == "L"]
        stated = {m["canonical"] for m in ments if m["level"] == "T"}
        states = stated or {self.fx["lga_level"][l]["state"] for l in lgas}  # explicit state wins over LGA-implied

        results = []
        direct = [m for m in ments if m["level"] == "S" and not m["proximity"]]
        for m in direct:
            results.append(self._settlement(m, states, set(lgas)))
        for m in ments:
            if m["level"] == "S" and m["proximity"] and not any(d["canonical"] == m["canonical"] for d in direct):
                results.append(self._result(
                    m["raw"], "UNRESOLVED", "none", {}, [], [],
                    [f"'{m['raw']}' is only a nearby reference, not the specific location"]))
        if not direct:
            for l in dict.fromkeys(lgas):
                prox = any(m["canonical"] == l and m["level"] == "L" and m["proximity"] for m in ments)
                results.append(self._result(
                    l, "RESOLVED", "lga", {"state": self.fx["lga_level"][l]["state"], "lga": l},
                    [{"state": self.fx["lga_level"][l]["state"], "lga": l, "settlement": None}], [],
                    ["nearby reference at LGA level"] if prox else []))
            if not lgas:
                for m in ments:
                    if m["level"] == "T":
                        results.append(self._result(m["raw"], "RESOLVED", "state", {"state": m["canonical"]},
                                                    [{"state": m["canonical"], "lga": None, "settlement": None}], []))
        statuses = {r["status"] for r in results}
        overall = "AMBIGUOUS" if "AMBIGUOUS" in statuses else "RESOLVED" if "RESOLVED" in statuses else "UNRESOLVED"
        lead = next((r for r in results if r["status"] == overall), None)
        return {
            "resolver_version": RESOLVER_VERSION,
            "status": overall,
            "candidates": lead["candidates"] if lead and overall != "UNRESOLVED" else [],
            "mentions": results,
        }

    def _settlement(self, m: dict, states: set, lgas: set) -> dict:
        name = m["canonical"]

        def fits(c):
            return (not states or c["state"] in states) and (not lgas or c["lga"] in lgas)

        if name in self.fx["ambiguous"]:
            e = self.fx["ambiguous"][name]
            requires = e["requires"]
            given = {"state": bool(states), "lga": bool(lgas)}
            if all(given[r] for r in requires):
                kept = [{**c, "settlement": name, "listed": True} for c in e["resolves_to"] if fits(c)]
                if not kept:
                    return self._result(m["raw"], "UNRESOLVED", "none", {}, [], [],
                                        ["stated location conflicts with the benchmark fixture"])
                return self._result(m["raw"], "RESOLVED", "settlement",
                                    {f: kept[0][f] for f in FIELDS if kept[0].get(f)}, kept[:1], [])
            listed = [{**c, "settlement": name, "listed": True} for c in e["candidates"] if fits(c)]
            return self._result(
                m["raw"], "AMBIGUOUS", "settlement", {"settlement": name}, listed, list(requires),
                ["more than one place has this name; the benchmark does not list them"])

        if name in self.fx["settlements"]:
            e = self.fx["settlements"][name]
            cands = [{"state": e["state"], "lga": e["lga"], "settlement": name, "listed": True}]
        else:
            e = self.fx["partial"][name]
            cands = [{"state": e["state"], "lga": l, "settlement": name, "listed": True} for l in e["lga_candidates"]]
        kept = [c for c in cands if fits(c)]
        if not kept:
            return self._result(m["raw"], "UNRESOLVED", "none", {}, [], [],
                                ["stated location conflicts with the benchmark fixture"])
        status = "RESOLVED" if len(kept) == 1 else "AMBIGUOUS"
        resolved = {}
        for f in FIELDS:
            vals = {c[f] for c in kept}
            if len(vals) == 1 and None not in vals:
                resolved[f] = vals.pop()
        differing = [f for f in ("state", "lga") if len({c[f] for c in kept}) > 1] if status == "AMBIGUOUS" else []
        return self._result(m["raw"], status, "settlement", resolved, kept, differing)

    @staticmethod
    def _result(raw, status, level, resolved, candidates, requires, notes=None) -> dict:
        return {
            "raw_text": raw,
            "status": status,
            "match_level": level,
            "resolved": resolved,
            "candidates": candidates,
            "unresolved_fields": [f for f in FIELDS if f not in resolved],
            "requires": requires,
            "notes": notes or [],
        }
