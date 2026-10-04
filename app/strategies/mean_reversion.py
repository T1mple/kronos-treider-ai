from app.strategies.base import Strategy

class MeanReversionStrategy(Strategy):
    name = 'mean_reversion'
    async def generate(self, market):
        return None
