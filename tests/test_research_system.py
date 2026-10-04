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
