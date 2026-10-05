from types import SimpleNamespace
from app.research.correlation import strategy_correlation, diversification_penalty

def r(curve):
    return SimpleNamespace(equity_curve=tuple(curve))

def test_strategy_correlation_matrix():
    m = strategy_correlation({"a": r([100,101,102,103]), "b": r([100,99,98,97])})
    assert m["a"]["a"] == 1.0
    assert m["a"]["b"] == m["b"]["a"]
    assert m["a"]["b"] < 0

def test_diversification_penalty():
    m = {"a":{"a":1.0,"b":0.8}, "b":{"a":0.8,"b":1.0}}
    assert diversification_penalty("b", ["a"], m) == 0.8
