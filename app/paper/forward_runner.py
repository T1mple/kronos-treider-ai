import asyncio
from dataclasses import asdict
from datetime import datetime, timezone

from app.data.binance_public import fetch_klines
from app.research.system import ResearchSystem

class ForwardPaperRunner:
    """Continuous read-only forward-paper loop. No exchange orders."""
    def __init__(self, symbol="BTCUSDT", interval="1h", limit=200):
        self.symbol=symbol
        self.interval=interval
        self.limit=limit
        self.system=ResearchSystem()
        self.running=False
        self.latest=None

    async def run_once(self):
        candles=await fetch_klines(self.symbol,self.interval,self.limit)
        result=self.system.evaluate(self.symbol,candles)
        self.latest={
            "updated_at":datetime.now(timezone.utc).isoformat(),
            "symbol":self.symbol,
            "interval":self.interval,
            "candles":len(candles),
            "result":result,
        }
        return self.latest

    async def loop(self, interval_seconds=900):
        self.running=True
        while self.running:
            try:
                await self.run_once()
            except Exception as exc:
                self.latest={"updated_at":datetime.now(timezone.utc).isoformat(),"status":"ERROR","error":str(exc)}
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running=False

    def snapshot(self):
        return self.latest or {"status":"WAITING","live_trading":False}
