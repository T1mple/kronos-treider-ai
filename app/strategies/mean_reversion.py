from statistics import mean
from app.strategies.base import Signal, Strategy

class MeanReversionStrategy(Strategy):
    name = "mean_reversion"

    async def generate(self, market):
        closes = list(getattr(market, "closes", []))
        if len(closes) < 5:
            return None
        window = closes[-5:]
        avg = mean(window)
        if avg <= 0:
            return None
        deviation = closes[-1] / avg - 1.0
        score = max(-1.0, min(1.0, -deviation / 0.02))
        confidence = min(1.0, abs(deviation) / 0.01)
        return Signal(market.symbol, score, confidence, self.name)
