from datetime import datetime,timedelta
from app.market_data import Candle
from app.research.selector import StrategySelector

def test_selector_ranks_strategies():
    candles=[]
    for i in range(80):
        close=100+i*0.2
        candles.append(Candle(datetime(2026,1,1)+timedelta(hours=i),close,close,close,close,1000))
    result=StrategySelector().evaluate(candles,{"always":lambda h: 1.0,"never":lambda h: 0.0})
    assert result.selected=="always"
    assert result.reports
