from dataclasses import dataclass

@dataclass
class KronosPrediction:
    symbol: str
    horizon: str
    direction: float
    confidence: float

class KronosAdapter:
    """Adapter boundary for shiyu-coder/Kronos. Kronos is a forecast layer."""
    def predict(self, symbol: str, ohlcv) -> KronosPrediction:
        raise NotImplementedError("Kronos integration is pending")
