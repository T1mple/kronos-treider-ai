from datetime import datetime,timedelta
from app.market_data import Candle
from app.research.regime import RegimeDetector
from app.research.regime_selector import RegimeStrategySelector

def candles(values):
    return [Candle(datetime(2026,1,1)+timedelta(hours=i),v,v,v,v,1000) for i,v in enumerate(values)]

def test_regime_trending():
    result=RegimeDetector().detect(candles([100+i for i in range(30)]))
    assert result.name=="TRENDING"

def test_regime_selector():
    result=RegimeStrategySelector().select(candles([100+i for i in range(30)]),{"momentum":1,"mean_reversion":1})
    assert result["regime"].name=="TRENDING"
    assert result["ordered_strategies"][0]=="momentum"
