from ml.rules import RuleBasedCategorizer


def test_rule_uber_transport() -> None:
    r = RuleBasedCategorizer().predict(label_norm="UBER TRIP PARIS", merchant=None)
    assert r is not None
    assert r.category == "transport"
    assert r.confidence >= 0.9


def test_rule_salary() -> None:
    r = RuleBasedCategorizer().predict(label_norm="VIR SALAIRE ACME SAS", merchant=None)
    assert r is not None
    assert r.category == "salary"
