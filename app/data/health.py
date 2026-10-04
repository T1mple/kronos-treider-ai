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
