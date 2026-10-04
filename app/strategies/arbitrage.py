from app.strategies.base import Signal, Strategy

class CrossExchangeArbitrageStrategy(Strategy):
    name = "cross_exchange_arbitrage"

    async def generate(self, market):
        cross = market.best_cross_exchange(market.symbol) if hasattr(market, "best_cross_exchange") else None
        if not cross:
            return None
        spread = float(cross["gross_spread"])
        if spread <= 0:
            return None
        confidence = min(1.0, spread / 0.005)
        return Signal(market.symbol, min(1.0, spread / 0.01), confidence, self.name)
