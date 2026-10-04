import asyncio
import json
from pathlib import Path
from dataclasses import asdict
from datetime import datetime, timezone

from app.data.binance_public import fetch_klines
from app.research.system import ResearchSystem

class ForwardPaperRunner:
    """Continuous read-only forward-paper loop. No exchange orders."""
    def __init__(self, symbol="BTCUSDT", interval="1h", limit=200, state_path="/data/forward_runner.json"):
        self.symbol=symbol
        self.interval=interval
        self.limit=limit
        self.system=ResearchSystem()
        self.running=False
        self.latest=None
        self.state_path=Path(state_path)
        self._load_state()

    def _load_state(self):
        try:
            if self.state_path.exists():
                self.latest=json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            self.latest=None

    def _save_state(self):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(self.latest, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    async def run_once(self):
        candles=await fetch_klines(self.symbol,self.interval,self.limit)
        result=self.system.evaluate(self.symbol,candles)
        self.latest={
            "updated_at":datetime.now(timezone.utc).isoformat(),
            "symbol":self.symbol,
            "interval":self.interval,
            "candles":len(candles),
            "result":result,
            "live_trading":False,
        }
        self._save_state()
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
