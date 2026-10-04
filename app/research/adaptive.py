from dataclasses import dataclass, asdict
from app.research.regime_selector import RegimeStrategySelector
from app.research.pipeline import ResearchPipeline

@dataclass
class AdaptiveDecision:
    regime: str
    ordered_strategies: list
    strategy_score: float
    kronos_score: float
    ensemble_score: float
    confidence: float

class AdaptiveStrategyEngine:
    """Research-only adaptive layer. Produces scores, never exchange orders."""
    def __init__(self, regime_selector=None, pipeline=None):
        self.regime_selector=regime_selector or RegimeStrategySelector()
        self.pipeline=pipeline or ResearchPipeline()

    def evaluate(self,candles,symbol,kronos_direction=0.0,kronos_confidence=0.0,strategy_signals=None):
        strategy_signals=strategy_signals or {}
        selection=self.regime_selector.select(candles,set(strategy_signals))
        ordered=selection["ordered_strategies"]
        weights={name:max(0.0,1.0-i*0.25) for i,name in enumerate(ordered)}
        total=sum(weights.values())
        strategy_score=sum(float(strategy_signals[name])*weights[name] for name in ordered)/total if total else 0.0
        signal=self.pipeline.evaluate(symbol,kronos_direction,kronos_confidence,strategy_score)
        return AdaptiveDecision(selection["regime"].name,ordered,strategy_score,signal.kronos_score,signal.ensemble_score,signal.confidence)

    @staticmethod
    def as_dict(decision):
        return asdict(decision)
