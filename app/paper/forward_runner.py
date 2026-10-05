import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from app.data.binance_public import fetch_klines
from app.research.system import ResearchSystem


_INTERVAL_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
}


class ForwardPaperRunner:
    """Continuous read-only forward-paper loop. No exchange orders."""

    def __init__(self, symbol="BTCUSDT", interval="1h", limit=200, state_path="/data/forward_runner.json"):
        if interval not in _INTERVAL_SECONDS:
            raise ValueError(f"Unsupported candle interval: {interval}")
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.system = ResearchSystem()
        self.running = False
        self.latest = None
        self.state_path = Path(state_path)
        self._load_state()

    def _load_state(self):
        try:
            if self.state_path.exists():
                self.latest = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            self.latest = None

    def _save_state(self):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(
                json.dumps(self.latest, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _closed_candles(self, candles, now=None):
        """Return only candles whose close time has already passed."""
        now = now or datetime.now(timezone.utc)
        interval = timedelta(seconds=_INTERVAL_SECONDS[self.interval])
        return [
            candle
            for candle in candles
            if candle.timestamp + interval <= now
        ]

    async def run_once(self):
        candles = await fetch_klines(self.symbol, self.interval, self.limit)
        closed = self._closed_candles(candles)
        if not closed:
            self.latest = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "status": "WAITING_FOR_CLOSED_CANDLE",
                "symbol": self.symbol,
                "interval": self.interval,
                "candles": len(candles),
                "live_trading": False,
            }
            self._save_state()
            return self.latest

        candle = closed[-1]
        candle_timestamp = candle.timestamp.isoformat()

        if self.latest and self.latest.get("candle_timestamp") == candle_timestamp:
            self.latest = {
                **self.latest,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "status": "NO_NEW_CLOSED_CANDLE",
            }
            self._save_state()
            return self.latest

        result = self.system.evaluate(self.symbol, closed)
        self.latest = {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "candle_timestamp": candle_timestamp,
            "symbol": self.symbol,
            "interval": self.interval,
            "candles": len(closed),
            "result": result,
            "live_trading": False,
            "status": "PROCESSED",
        }
        self._save_state()
        return self.latest

    async def loop(self, interval_seconds=900):
        self.running = True
        while self.running:
            try:
                await self.run_once()
            except Exception as exc:
                self.latest = {
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "status": "ERROR",
                    "error": str(exc),
                    "live_trading": False,
                }
                self._save_state()
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running = False

    def snapshot(self):
        return self.latest or {"status": "WAITING", "live_trading": False}
