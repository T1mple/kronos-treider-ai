from types import SimpleNamespace
from app.paper.decision_loop import PaperDecisionLoop

def candle(i):
    return SimpleNamespace(open=100+i,high=102+i,low=99+i,close=101+i,volume=100+i)

def test_decision_loop_is_paper_only():
    loop=PaperDecisionLoop()
    decision,_=loop.evaluate("BTCUSDT",140,[candle(i) for i in range(40)])
    assert decision.action in {"BUY","HOLD"}
    assert not hasattr(loop,"live_exchange")
