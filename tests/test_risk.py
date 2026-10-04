from app.config import Settings
from app.risk import RiskEngine

def test_position_limit():
    r=RiskEngine(Settings(max_position_usd=50))
    ok,_=r.approve_order(51)
    assert not ok

def test_pause_blocks():
    r=RiskEngine(Settings())
    r.pause()
    ok,_=r.approve_order(10)
    assert not ok
