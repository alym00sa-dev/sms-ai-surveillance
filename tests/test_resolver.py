import json

import pytest

from src.benchmark.loader import load_benchmark
from src.benchmark.location_fixture import LocationResolver

SC = {s["id"]: s for s in load_benchmark()}
R = LocationResolver()


def at(sid, turn):  # resolver output after the gold user turns up to `turn` (1-based)
    return R.resolve([t["user"] for t in SC[sid]["turns"][:turn]])


def test_resolved_and_hierarchy():
    r = at("AFP-01", 1)
    assert r["status"] == "RESOLVED" and r["candidates"][0] == {
        "state": "Jigawa", "lga": "Kafin Hausa", "settlement": "Majawa", "listed": True}


def test_typo_normalization():
    assert at("MESSY-14", 1)["mentions"][0]["resolved"]["settlement"] == "Majawa"
    assert at("DUP-28", 1)["status"] == "RESOLVED"


def test_kura_ambiguous_then_resolved():
    for sid in ("CLAR-09", "CLAR-11"):
        r = at(sid, 1)
        assert r["status"] == "AMBIGUOUS" and r["candidates"] == []  # nothing invented, nothing hinted
        assert "kano" not in json.dumps(r).casefold()
        assert r["mentions"][0]["requires"] == ["state", "lga"]
        assert r["mentions"][0]["resolved"] == {"settlement": "Kura"}
        r2 = at(sid, 2)
        assert r2["status"] == "RESOLVED" and r2["candidates"][0]["state"] == "Kano"


def test_kura_state_alone_stays_ambiguous():
    r = R.resolve(["boy in Kura", "Kano State"])
    assert r["status"] == "AMBIGUOUS" and r["mentions"][0]["requires"] == ["state", "lga"]
    assert R.resolve(["boy in Kura", "Jigawa State, Kura LGA"])["status"] == "UNRESOLVED"


def test_unresolved_cases():
    for sid, turns in (("ESC-24", 4), ("ESC-23", 4), ("ESC-25", 2), ("IRR-29", 1), ("CLAR-06", 1)):
        for t in range(1, turns + 1):
            r = at(sid, t) if not (sid == "CLAR-06" and t > 1) else None
            if r:
                assert r["status"] == "UNRESOLVED" and r["candidates"] == [], (sid, t)


def test_proximity_vs_lga_level():
    assert at("ESC-25", 1)["mentions"][0]["notes"]
    r = at("CLAR-13", 1)["mentions"][0]
    assert r["status"] == "RESOLVED" and r["match_level"] == "lga" and "settlement" in r["unresolved_fields"]
    assert at("CLAR-13", 2)["mentions"][0]["resolved"]["settlement"] == "Majawa"


def test_partial_state_only():
    r = at("VPD-20", 1)
    assert r["status"] == "AMBIGUOUS" and r["mentions"][0]["resolved"]["state"] == "Sokoto"
    assert r["mentions"][0]["requires"] == ["lga"]


@pytest.mark.parametrize("sid", sorted(SC))
def test_agrees_with_gold_on_every_turn(sid):
    """Valued gold fields match the resolver; explicit-null gold fields are never resolved."""
    for ti, t in enumerate(SC[sid]["turns"], start=1):
        res = at(sid, ti)
        resolved = {}
        for m in res["mentions"]:
            if m["status"] == "RESOLVED" or m["status"] == "AMBIGUOUS":
                resolved.update(m["resolved"])
        for c in t["expected"]["cases"]:
            for f in ("state", "lga", "settlement"):
                if f not in c:
                    continue
                if c[f] is None:
                    assert f not in resolved, (sid, ti, f)
                elif f in resolved:
                    assert resolved[f].casefold() == c[f].casefold(), (sid, ti, f, resolved[f], c[f])


def test_around_an_age_is_not_a_proximity_reference():
    r = R.resolve(["Boy around 7 in Majawa, both legs suddenly weak."])
    assert r["status"] == "RESOLVED" and r["mentions"][0]["resolved"]["settlement"] == "Majawa"
    assert R.resolve(["somewhere near Majawa"])["status"] == "UNRESOLVED"
    assert R.resolve(["close to Majawa"])["status"] == "UNRESOLVED"
    assert R.resolve(["a village near Kafin Hausa"])["mentions"][0]["match_level"] == "lga"
    assert R.resolve(["around the Majawa market"])["status"] == "UNRESOLVED"  # "around X" still means nearby
