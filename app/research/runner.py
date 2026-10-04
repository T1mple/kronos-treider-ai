from dataclasses import dataclass, asdict
from app.data.binance_public import fetch_klines
from app.kronos_adapter import HeuristicKronosAdapter
from app.research.adaptive import AdaptiveStrategyEngine
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.research.decision import ResearchDecisionEngine
from app.research.system import ResearchSystem

@dataclass
class RunnerResult:
    symbol: str
    interval: str
    candles: int
    strategies: dict
    kronos: dict
    adaptive: dict
    decision: dict

class ResearchRunner:
    """End-to-end read-only research runner. It never submits exchange orders."""
    def __init__(self, kronos=None, adaptive=None, decision=None):
        self.kronos=kronos or HeuristicKronosAdapter()
        self.adaptive=adaptive or AdaptiveStrategyEngine()
        self.decision=decision or ResearchDecisionEngine()
        self.system=ResearchSystem()

    async def run(self,symbol="BTCUSDT",interval="1h",limit=500,train_size=300,test_size=50,step=50):
        candles=await fetch_klines(symbol,interval,limit)
        strategy_functions={"momentum":momentum_signal,"mean_reversion":mean_reversion_signal,"trend_filter":trend_filter_signal}
        strategy_scores={name:float(fn(candles)) for name,fn in strategy_functions.items()}
        prediction=self.kronos.predict(symbol,candles)
        adaptive=self.adaptive.evaluate(candles,symbol,prediction.direction,prediction.confidence,strategy_scores)
        regime_volatility=self.adaptive.regime_selector.detector(candles).volatility
        decision=self.decision.evaluate(adaptive,available=300.0,volatility=regime_volatility)
        return RunnerResult(symbol,interval,len(candles),strategy_scores,{"direction":prediction.direction,"confidence":prediction.confidence},self.adaptive.as_dict(adaptive),asdict(decision))

    async def run_unified(self,symbol="BTCUSDT",interval="1h",limit=500):
        candles=await fetch_klines(symbol,interval,limit)
        return self.system.evaluate(symbol,candles)

    @staticmethod
    def as_dict(result): return asdict(result)
