from dataclasses import dataclass
from app.research.stock_report import StockResearchReport

@dataclass
class Candle:
    close: float
    volume: float

def test_stock_report_contains_factor_attribution():
    candles=[Candle(100+i,1000+i) for i in range(30)]
    result=StockResearchReport().build("NVDA",candles,kronos_score=.8,sector_score=.4)
    assert result["asset_type"]=="stock"
    assert len(result["attribution"])==6
    assert -1 <= result["score"] <= 1
