from app.data.multi_feed import MultiExchangeReader
from app.data.arbitrage import find_opportunity
from app.market_data import MarketDataHub, Quote
from app.paper.loop import PaperLoop

class MultiExchangePaperLoop:
    """Read-only multi-exchange paper monitor with virtual opportunity detection."""
    def __init__(self, reader=None, hub=None, paper=None):
        self.reader=reader or MultiExchangeReader()
        self.hub=hub or MarketDataHub()
        self.paper=paper or PaperLoop()

    async def tick(self, symbol="BTCUSDT"):
        ticks=await self.reader.snapshot(symbol)
        for tick in ticks:
            self.hub.update_quote(Quote(tick.exchange,tick.symbol,tick.price,tick.price,tick.timestamp))
        opportunity=find_opportunity(ticks,symbol)
        await self.paper.run_once(symbol, ticks[0].price if ticks else 0.0, 1.0 if opportunity else 0.0)
        return {
            "symbol":symbol,
            "exchanges":len(ticks),
            "opportunity":opportunity,
            "session":self.paper.session.snapshot(),
        }
