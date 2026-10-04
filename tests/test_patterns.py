from types import SimpleNamespace
from app.research.patterns import aggregate_pattern_score, rsi_signal, rsi_divergence

def candle(o,h,l,c,v=100):
    return SimpleNamespace(open=o, high=h, low=l, close=c, volume=v)

def test_pattern_score_shape():
    candles=[candle(100+i,102+i,99+i,101+i,100+i*5) for i in range(40)]
    result=aggregate_pattern_score(candles)
    assert -1.0 <= result["score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert "rsi" in result and "divergence" in result

def test_rsi_neutral_for_flat_series():
    candles=[candle(100,101,99,100,100) for _ in range(20)]
    assert rsi_signal(candles)["state"] == "NEUTRAL"

def test_divergence_returns_context():
    candles=[candle(100+i,101+i,99+i,100+i,100) for i in range(20)]
    result=rsi_divergence(candles)
    assert "score" in result and "type" in result
