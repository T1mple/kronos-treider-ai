from app.strategies.base import Strategy

class CrossExchangeArbitrageStrategy(Strategy):
    name = 'cross_exchange_arbitrage'
    async def generate(self, market):
        return None
