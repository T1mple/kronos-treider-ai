from datetime import datetime,timedelta
from app.market_data import Candle
from app.research.adaptive import AdaptiveStrategyEngine

def test_adaptive_engine_prefers_regime_strategy():
    candles=[Candle(datetime(2026,1,1)+timedelta(hours=i),100+i,100+i,100+i,100+i,1000) for i in range(30)]
    result=AdaptiveStrategyEngine().evaluate(candles,"BTCUSDT",0.5,0.8,{"momentum":1.0,"mean_reversion":-1.0})
    assert result.regime=="TREND"
    assert result.ordered_strategies[0]=="momentum"
    assert result.ensemble_score>0
