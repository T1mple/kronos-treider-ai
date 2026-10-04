from types import SimpleNamespace
from app.research.fusion import build_forecast

def candle(o,h,l,c,v=100):
    return SimpleNamespace(open=o,high=h,low=l,close=c,volume=v)

def test_forecast_fusion_shape():
    candles=[candle(100+i,102+i,99+i,101+i,100+i) for i in range(40)]
    result=build_forecast("BTCUSDT",candles)
    assert -1.0 <= result["score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0
    assert "kronos" in result and "pattern" in result
