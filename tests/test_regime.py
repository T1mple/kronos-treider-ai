from types import SimpleNamespace
from app.research.regime import detect_regime
def c(i): return SimpleNamespace(close=100+i,open=100+i,high=101+i,low=99+i,volume=100)
def test_regime_shape():
    r=detect_regime([c(i) for i in range(50)])
    assert r.name in {"TREND","RANGE","HIGH_VOLATILITY"}
    assert 0<=r.confidence<=1
