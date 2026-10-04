import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

from app.paper.session import PaperSession

@dataclass
class PaperTick:
    symbol: str
    price: float
    timestamp: str

class PaperLoop:
    """Continuous research/paper loop. It never submits real exchange orders."""
    def __init__(self, session=None):
        self.session = session or PaperSession()
        self.running = False

    async def run_once(self, symbol, price, signal=0.0):
        self.session.tick()
        if signal:
            self.session.record_signal()
        return PaperTick(symbol=symbol, price=float(price),
                         timestamp=datetime.now(timezone.utc).isoformat())

    async def run(self, source, symbol="BTCUSDT", interval_seconds=60, on_tick=None):
        self.running = True
        while self.running:
            tick = await source(symbol)
            result = await self.run_once(symbol, tick["price"], tick.get("signal", 0.0))
            if on_tick:
                await on_tick(result, self.session.snapshot())
            await asyncio.sleep(max(1, int(interval_seconds)))

    def stop(self):
        self.running = False
        self.session.active = False
