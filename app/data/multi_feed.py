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

    async def snapshot(self, symbol="BTCUSDT", max_age_seconds=15):
        rows=await self.fetch_all(symbol)
        result=[]
        for item in rows:
            if not item["ok"]:
                continue
            tick=item["tick"]
            try:
                from app.ops.stale_quotes import is_stale
                if is_stale(tick.timestamp, max_age_seconds):
                    continue
            except Exception:
                continue
            result.append(tick)
        return result
