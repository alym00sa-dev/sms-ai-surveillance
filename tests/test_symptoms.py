import pytest

from src.benchmark.loader import load_benchmark
from src.benchmark.symptoms import extract_features, load_symptom_features, satisfies

SF = load_symptom_features()
GOLD = sorted({c["symptom"] for s in load_benchmark() for t in s["turns"] for c in t["expected"]["cases"]})


def test_every_gold_symptom_has_frozen_features():
    assert len(GOLD) == 25 and set(GOLD) <= set(SF)


@pytest.mark.parametrize("sym", GOLD)
def test_gold_prose_satisfies_its_own_features(sym):
    """The model-side extractor, run on the gold prose, meets every frozen non-null feature."""
    assert satisfies(SF[sym], extract_features(sym)), (sym, extract_features(sym))


PARAPHRASES = [
    ("sudden inability to use left leg", ["cannot use left leg suddenly", "Left leg suddenly weak, can't use it", "sudden left leg paralysis"]),
    ("sudden weakness in both legs", ["both legs suddenly weak", "legs became weak suddenly", "acute weakness of both legs"]),
    ("sudden weakness in one leg", ["one leg suddenly weak", "sudden weakness in one leg (right)", "abrupt weakness, single leg"]),
    ("sudden one-leg weakness/inability to walk normally", ["woke up this morning with one weak leg"]),
    ("sudden weakness of both hands", ["both arms suddenly weak", "sudden weakness in both hands"]),
    ("sudden leg weakness", ["leg weakness since this morning", "sudden weakness in legs"]),
    ("weak leg", ["leg weakness", "weak leg, onset unknown"]),
]
NEGATIVES = [
    ("sudden inability to use left leg", ["cannot use right leg suddenly", "sudden weakness in one leg", "weak left leg", "cannot use left arm suddenly", "weakness"]),
    ("sudden weakness in both legs", ["sudden weakness in one leg", "weakness in both legs", "sudden weakness in both arms", "sudden weak left leg"]),
    ("sudden weakness in one leg", ["sudden weakness in both legs", "weak leg"]),
    ("sudden weakness of both hands", ["sudden weakness in both legs", "sudden weakness in left hand"]),
    ("sudden leg weakness", ["sudden arm weakness", "leg weakness"]),
]


@pytest.mark.parametrize("gold,texts", PARAPHRASES)
def test_paraphrases_pass(gold, texts):
    for t in texts:
        assert satisfies(SF[gold], extract_features(t)), (gold, t, extract_features(t))


@pytest.mark.parametrize("gold,texts", NEGATIVES)
def test_contradictions_fail(gold, texts):
    for t in texts:
        assert not satisfies(SF[gold], extract_features(t)), (gold, t, extract_features(t))


def test_one_of_legs_is_not_both():
    assert "both" not in extract_features("one of his legs is weak")["laterality"]
