from app.strategies.base import Signal, Strategy

class StatisticalArbitrageStrategy(Strategy):
    name = 'statistical_arbitrage'
    async def generate(self, market):
        return None
