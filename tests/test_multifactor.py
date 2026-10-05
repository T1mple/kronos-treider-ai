from dataclasses import dataclass
from app.research.multifactor import MultiFactorEngine
from app.research.scanner import MarketScanner
from app.research.correlation import correlation, concentration

@dataclass
class Candle:
    close: float
    volume: float

def test_multifactor_score_is_bounded():
    candles=[Candle(100+i,1000+i) for i in range(30)]
    result=MultiFactorEngine().evaluate("TEST",candles,kronos_score=.8,sector_score=.6)
    assert -1 <= result.score <= 1
    assert 0 <= result.confidence <= 1

def test_scanner_ranks_assets():
    candles=[Candle(100+i,1000+i) for i in range(30)]
    rows=MarketScanner().rank({"NVDA":{"candles":candles,"kronos":.8},"AAPL":{"candles":candles,"kronos":.2}},limit=2)
    assert len(rows)==2 and rows[0]["symbol"]=="NVDA"

def test_correlation_and_concentration():
    assert correlation([1,2,3,4],[2,4,6,8]) > .99
    assert concentration({"A":100,"B":0}) == 1.0
