import pytest
from app.paper.engine import PaperTradingEngine

def test_paper_round_trip():
    e=PaperTradingEngine(300,0.001)
    e.buy("BTC/USDT",0.5,100)
    assert e.ledger.positions["BTC/USDT"].quantity == 0.5
    e.sell("BTC/USDT",0.5,110)
    assert e.ledger.positions["BTC/USDT"].quantity == 0
    assert e.equity({"BTC/USDT":110}) > 300

def test_paper_rejects_overspend():
    e=PaperTradingEngine(10,0.001)
    with pytest.raises(ValueError): e.buy("BTC/USDT",1,100)
