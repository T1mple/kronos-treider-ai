import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from app.backtest import Backtester
from app.data.binance_public import fetch_klines
from app.kronos_adapter import HeuristicKronosAdapter
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal


@dataclass
class AutoTestResult:
    symbol: str
    interval: str
    candles: int
    updated_at: str
    return_pct: float
    max_drawdown_pct: float
    trades: int
    fees: float
    strategy_scores: dict
    kronos_direction: float
    kronos_confidence: float
    status: str = "PAPER_RESEARCH"


class PaperAutoTester:
    """Continuous historical paper test. It never submits exchange orders."""

    def __init__(self, symbol="BTCUSDT", interval="1h", limit=500):
        self.symbol = symbol
        self.interval = interval
        self.limit = limit
        self.backtester = Backtester()
        self.kronos = HeuristicKronosAdapter()
        self.latest = None
        self.running = False

    @staticmethod
    def _robot_signal(history):
        if len(history) < 10:
            return 0.0
        momentum = float(momentum_signal(history))
        mean_reversion = float(mean_reversion_signal(history))
        trend = float(trend_filter_signal(history))
        prediction = HeuristicKronosAdapter().predict("BTCUSDT", history)
        score = (prediction.direction * 0.35 + momentum * 0.25 + mean_reversion * 0.20 + trend * 0.20)
        return max(-1.0, min(1.0, score))

    async def run_once(self):
        candles = await fetch_klines(self.symbol, self.interval, self.limit)
        result = self.backtester.run(candles, 300.0, 0.001, 0.0005, self._robot_signal)
        prediction = self.kronos.predict(self.symbol, candles)
        scores = {
            "momentum": float(momentum_signal(candles)),
            "mean_reversion": float(mean_reversion_signal(candles)),
            "trend_filter": float(trend_filter_signal(candles)),
        }
        self.latest = AutoTestResult(self.symbol, self.interval, len(candles),
            datetime.now(timezone.utc).isoformat(), result.total_return * 100.0,
            result.max_drawdown * 100.0, result.trades, result.fees_paid, scores,
            prediction.direction, prediction.confidence)
        return self.latest

    def snapshot(self):
        return asdict(self.latest) if self.latest else {"status": "WAITING_FOR_FIRST_TEST"}

    async def loop(self, interval_seconds=900, on_result=None):
        self.running = True
        while self.running:
            try:
                result = await self.run_once()
                if on_result:
                    await on_result(result)
            except Exception as exc:
                self.latest = {"status": "ERROR", "error": str(exc), "updated_at": datetime.now(timezone.utc).isoformat()}
            await asyncio.sleep(interval_seconds)

    def stop(self):
        self.running = False
