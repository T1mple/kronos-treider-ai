from app.research.system import ResearchSystem
from types import SimpleNamespace

def candle(i):
    return SimpleNamespace(open=100+i,high=102+i,low=99+i,close=101+i,volume=100)

def test_unified_research_shape():
    result=ResearchSystem().evaluate("BTCUSDT",[candle(i) for i in range(50)])
    assert result["mode"]=="RESEARCH_PAPER"
    assert "kronos" in result and "regime" in result
    assert "risk_gate" in result
    assert result["risk_gate"]["approved"] in {True,False}


def test_research_runner_uses_regime_detector(monkeypatch):
    from app.research.runner import ResearchRunner
    import app.research.runner as runner_module
    from app.market_data import Candle
    from datetime import datetime, timezone

    candles=[Candle(datetime.now(timezone.utc),1,1.1,0.9,1,10) for _ in range(40)]
    monkeypatch.setattr(runner_module, "fetch_klines", lambda *args, **kwargs: candles)
    monkeypatch.setattr(runner_module, "detect_regime", lambda xs: type("R", (), {"volatility":0.01})())
    result=runner_module.ResearchRunner()
    assert result.adaptive.regime_selector.detector(candles).volatility == 0.01
