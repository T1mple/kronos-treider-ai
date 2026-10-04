import asyncio
from app.data.health import FeedHealthMonitor
class Feed:
    exchange="test"
    async def fetch(self,symbol): return type("Tick",(),{"price":100})()
def test_health_monitor():
    r=asyncio.run(FeedHealthMonitor().check(Feed()))
    assert r.ok and r.exchange=="test"
