from dataclasses import dataclass

@dataclass
class Forecast:
    symbol: str
    direction: float
    confidence: float

def combine(forecasts: list[Forecast], strategy_score: float = 0.0) -> float:
    if not forecasts: return max(-1.0, min(1.0, strategy_score))
    weights = [max(0.0, min(1.0, x.confidence)) for x in forecasts]
    total = sum(weights)
    model_score = sum(x.direction*w for x,w in zip(forecasts, weights))/total if total else 0.0
    return max(-1.0, min(1.0, 0.7*model_score + 0.3*strategy_score))
