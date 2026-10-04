from dataclasses import dataclass

@dataclass
class KronosPrediction:
    symbol: str
    horizon: str
    direction: float
    confidence: float

class KronosAdapter:
    """Forecast-only boundary for shiyu-coder/Kronos.

    The adapter intentionally never emits orders or trade instructions.
    """
    def predict(self, symbol: str, ohlcv) -> KronosPrediction:
        raise NotImplementedError("Kronos model backend is not configured")

class HeuristicKronosAdapter(KronosAdapter):
    """Deterministic fallback for tests/research when the model is unavailable."""
    def predict(self, symbol: str, ohlcv) -> KronosPrediction:
        closes=[float(x.close if hasattr(x, "close") else x["close"]) for x in ohlcv]
        if len(closes)<3 or closes[-3] <= 0:
            return KronosPrediction(symbol, "short", 0.0, 0.0)
        momentum=closes[-1]/closes[-3]-1.0
        direction=max(-1.0,min(1.0,momentum/0.02))
        confidence=min(1.0,abs(momentum)/0.01)
        return KronosPrediction(symbol, "short", direction, confidence)
