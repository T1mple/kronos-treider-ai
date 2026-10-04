from app.strategies.base import Strategy

class MarketMakingStrategy(Strategy):
    name = 'market_making'
    async def generate(self, market):
        return None
