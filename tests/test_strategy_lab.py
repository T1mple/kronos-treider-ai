from datetime import datetime,timedelta
from app.market_data import Candle
from app.research.strategy_lab import StrategyLab
from app.research.signals import momentum_signal,trend_filter_signal

def test_strategy_lab_runs_multiple_models():
    candles=[]
    for i in range(40):
        price=100+i*0.5
        candles.append(Candle(datetime(2026,1,1)+timedelta(days=i),price,price+1,price-1,price,1000))
    result=StrategyLab().run(candles,{"momentum":momentum_signal,"trend":trend_filter_signal})
    assert len(result.reports)==2
    assert all(hasattr(x,"return_pct") for x in result.reports)
