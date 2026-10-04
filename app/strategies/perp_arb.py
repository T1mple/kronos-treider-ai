from app.strategies.base import Strategy

class SpotPerpetualArbitrageStrategy(Strategy):
    name = 'spot_perpetual_arbitrage'
    async def generate(self, market):
        return None
