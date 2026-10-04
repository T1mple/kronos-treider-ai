import asyncio
from app.data.public_feeds import default_public_feeds

class MultiExchangeReader:
    """Concurrent read-only market-data collector."""
    def __init__(self, feeds=None):
        self.feeds=feeds or default_public_feeds()

    async def fetch_all(self, symbol="BTCUSDT"):
        async def one(feed):
            try:
                tick=await feed.fetch(symbol)
                return {"ok":True,"tick":tick}
            except Exception as exc:
                return {"ok":False,"exchange":feed.exchange,"error":str(exc)}
        return await asyncio.gather(*(one(feed) for feed in self.feeds))

    async def snapshot(self, symbol="BTCUSDT"):
        rows=await self.fetch_all(symbol)
        return [x["tick"] for x in rows if x["ok"]]
