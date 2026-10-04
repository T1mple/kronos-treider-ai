from app.data.multi_feed import MultiExchangeReader
from app.data.arbitrage import find_opportunity
from app.market_data import MarketDataHub, Quote
from app.paper.loop import PaperLoop
from app.data.binance_public import fetch_klines
from app.research.fusion import build_forecast

class MultiExchangePaperLoop:
    """Read-only multi-exchange paper monitor with virtual opportunity detection."""
    def __init__(self, reader=None, hub=None, paper=None):
        self.reader=reader or MultiExchangeReader()
        self.hub=hub or MarketDataHub()
        self.paper=paper or PaperLoop()

    async def tick(self, symbol="BTCUSDT", interval="1h", limit=100):
        ticks=await self.reader.snapshot(symbol)
        for tick in ticks:
            self.hub.update_quote(Quote(tick.exchange,tick.symbol,tick.price,tick.price,tick.timestamp))
        opportunity=find_opportunity(ticks,symbol)
        candles=await fetch_klines(symbol,interval,limit) if ticks else []
        fusion=build_forecast(symbol,candles) if candles else {"score":0.0,"confidence":0.0}
        paper_signal=opportunity is not None and opportunity.viable and fusion["score"] > 0
        await self.paper.run_once(symbol, ticks[0].price if ticks else 0.0, 1.0 if paper_signal else 0.0)
        return {
            "symbol":symbol,
            "exchanges":len(ticks),
            "opportunity":opportunity,
            "fusion":fusion,
            "paper_signal":paper_signal,
            "session":self.paper.session.snapshot(),
        }
