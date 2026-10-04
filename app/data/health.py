from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class FeedHealth:
    exchange: str
    ok: bool
    latency_ms: float
    error: str=""

class FeedHealthMonitor:
    def __init__(self): self.last={}
    async def check(self,feed,symbol="BTCUSDT"):
        start=datetime.now(timezone.utc)
        try:
            await feed.fetch(symbol); result=FeedHealth(feed.exchange,True,(datetime.now(timezone.utc)-start).total_seconds()*1000)
        except Exception as exc:
            result=FeedHealth(feed.exchange,False,(datetime.now(timezone.utc)-start).total_seconds()*1000,str(exc))
        self.last[feed.exchange]=result
        return result

    async def check_all(self, feeds, symbol="BTCUSDT"):
        import asyncio
        results=await asyncio.gather(*(self.check(feed,symbol) for feed in feeds))
        return [r.__dict__.copy() for r in results]
