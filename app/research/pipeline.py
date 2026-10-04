from dataclasses import dataclass, asdict
from app.ensemble import Forecast, combine

@dataclass
class ResearchSignal:
    symbol: str
    ensemble_score: float
    kronos_score: float
    strategy_score: float
    confidence: float

class ResearchPipeline:
    """Combines model forecasts and strategy signals without placing orders."""
    def evaluate(self, symbol, kronos_direction=0.0, kronos_confidence=0.0, strategy_score=0.0):
        forecast=Forecast(symbol, max(-1.0,min(1.0,kronos_direction)), max(0.0,min(1.0,kronos_confidence)))
        score=combine([forecast], strategy_score)
        confidence=(forecast.confidence + min(1.0,abs(strategy_score)))/2
        return ResearchSignal(symbol, score, forecast.direction, strategy_score, confidence)

    def to_dict(self, signal):
        return asdict(signal)
