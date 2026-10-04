from dataclasses import dataclass, asdict
from app.data.binance_public import fetch_klines
from app.kronos_adapter import HeuristicKronosAdapter
from app.research.pipeline import ResearchPipeline
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.research.walk_forward import WalkForwardValidator

@dataclass
class RunnerResult:
    symbol: str
    interval: str
    candles: int
    strategies: list
    kronos: dict

class ResearchRunner:
    """End-to-end, read-only research runner. It never submits exchange orders."""
    def __init__(self, validator=None, kronos=None):
        self.validator=validator or WalkForwardValidator()
        self.kronos=kronos or HeuristicKronosAdapter()

    async def run(self, symbol="BTCUSDT", interval="1h", limit=500, train_size=300, test_size=50, step=50):
        candles=await fetch_klines(symbol,interval,limit)
        strategies={
            "momentum": momentum_signal,
            "mean_reversion": mean_reversion_signal,
            "trend_filter": trend_filter_signal,
        }
        reports={}
        for name,fn in strategies.items():
            windows=self.validator.run(candles,fn,train_size,test_size,step)
            reports[name]={
                "windows":len(windows),
                "test_return_pct":sum(x.test_return for x in windows)/len(windows)*100 if windows else 0.0,
                "worst_drawdown_pct":max((x.test_drawdown for x in windows),default=0.0)*100,
                "trades":sum(x.trades for x in windows),
            }
        prediction=self.kronos.predict(symbol,candles)
        ensemble=ResearchPipeline().evaluate(symbol,prediction.direction,prediction.confidence,momentum_signal(candles))
        return RunnerResult(symbol,interval,len(candles),reports,{
            "direction":prediction.direction,
            "confidence":prediction.confidence,
            "ensemble_score":ensemble.ensemble_score,
        })

    @staticmethod
    def as_dict(result):
        return asdict(result)
