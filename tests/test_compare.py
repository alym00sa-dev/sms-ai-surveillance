from src.benchmark.compare import age_matches, compare_cases


def kinds(d):
    return sorted((x["kind"], x["field"]) for x in d.diffs)


def test_age_ranges():
    assert age_matches("about 10-11", 10) and age_matches("about 10-11", "about 10-11")
    assert not age_matches("about 10-11", 12) and age_matches(7, "7") and not age_matches(7, 8)
    assert age_matches("about 9", "about 9")


def test_omitted_null_value_semantics():
    gold = [{"age": 7, "sex": "male", "settlement": "Majawa", "state": None}]
    assert compare_cases([{"age": 7, "sex": "male", "settlement": "Majawa"}], gold).ok
    assert kinds(compare_cases([{"age": 7, "sex": "male", "settlement": "Majawa", "state": "Jigawa"}], gold)) == [
        ("should_be_null", "state")]
    assert kinds(compare_cases([{"age": 7, "sex": "female", "settlement": "Majawa"}], gold)) == [("wrong_value", "sex")]
    assert kinds(compare_cases([{"sex": "male", "settlement": "Majawa"}], gold)) == [("missing_value", "age")]


def test_fixture_check_on_omitted_fields():
    gold = [{"settlement": "Majawa"}]
    assert compare_cases([{"settlement": "Majawa", "state": "Jigawa", "lga": "Kafin-Hausa"}], gold).ok
    assert kinds(compare_cases([{"settlement": "Majawa", "state": "Kano"}], gold)) == [("fabricated", "state")]
    assert kinds(compare_cases([{"settlement": "Kura", "state": "Kano"}], [{"settlement": "Kura"}])) == [
        ("fabricated", "state")]


def test_multi_case_alignment_and_merge():
    gold = [{"age": 5, "sex": "male"}, {"age": "about 9", "sex": "female"}]
    assert compare_cases([{"age": 9, "sex": "female"}, {"age": 5, "sex": "male"}], gold).ok  # order-insensitive
    assert kinds(compare_cases([{"age": 5, "sex": "male"}], gold)) == [("missing_case", None)]
    assert kinds(compare_cases([{"age": 5, "sex": "male"}, {"age": 8, "sex": "female"}], gold)) == [
        ("wrong_value", "age")]
