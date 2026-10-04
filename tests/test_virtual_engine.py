from app.paper.virtual_engine import VirtualPaperEngine

def test_virtual_long_roundtrip():
    engine=VirtualPaperEngine(300.0,fee_rate=0.001,slippage_rate=0.0)
    pos=engine.open("BTCUSDT","buy",50,100)
    assert pos is not None
    trade=engine.close("BTCUSDT",102)
    assert trade is not None
    assert trade.pnl > 0
    assert engine.metrics()["trades"] == 1

def test_virtual_engine_never_opens_duplicate():
    engine=VirtualPaperEngine()
    assert engine.open("BTCUSDT","buy",50,100) is not None
    assert engine.open("BTCUSDT","buy",50,101) is None
