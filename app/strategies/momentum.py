from app.strategies.base import Signal, Strategy

class MomentumStrategy(Strategy):
    name = "momentum"

    async def generate(self, market):
        closes = list(getattr(market, "closes", []))
        if len(closes) < 3 or closes[-3] <= 0:
            return None
        score = (closes[-1] / closes[-3]) - 1.0
        bounded = max(-1.0, min(1.0, score / 0.02))
        confidence = min(1.0, abs(score) / 0.01)
        return Signal(market.symbol, bounded, confidence, self.name)
