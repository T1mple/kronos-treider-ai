import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Awaitable, Callable

from app.config import settings
from app.data.binance_public import fetch_klines
from app.kronos_adapter import HeuristicKronosAdapter
from app.paper.engine import PaperTradingEngine
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.risk import RiskEngine
from app.paper.store import (
    append_decision,
    append_trade,
    init_paper_store,
    load_state,
    paper_report,
    record_equity,
    save_state,
)


@dataclass
class PaperDecision:
    timestamp: str
    symbol: str
    price: float
    signal: float
    kronos_direction: float
    kronos_confidence: float
    action: str
    quantity: float
    reason: str
    realized_pnl: float = 0.0


class AutonomousPaperEngine:
    """Continuous market-data-driven simulation. It never submits real orders."""

    def __init__(self, symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"), starting_cash=300.0):
        if settings.live_trading:
            raise RuntimeError("AutonomousPaperEngine is paper-only; LIVE_TRADING must remain false")
        self.symbols = tuple(symbols)
        self.starting_cash = float(starting_cash)
        self.paper = PaperTradingEngine(starting_cash=starting_cash)
        self.risk = RiskEngine(settings)
        self.kronos = HeuristicKronosAdapter()
        self.running = False
        self.decisions: list[PaperDecision] = []
        self.last_prices: dict[str, float] = {}
        self.initialized = False

    @staticmethod
    def _signal(symbol, candles):
        if len(candles) < 20:
            return 0.0, 0.0, 0.0
        momentum = float(momentum_signal(candles))
        mean_reversion = float(mean_reversion_signal(candles))
        trend = float(trend_filter_signal(candles))
        prediction = HeuristicKronosAdapter().predict(symbol, candles)
        ensemble = (
            prediction.direction * 0.40
            + momentum * 0.25
            + mean_reversion * 0.15
            + trend * 0.20
        )
        return max(-1.0, min(1.0, ensemble)), prediction.direction, prediction.confidence

    def _record(self, symbol, price, signal, direction, confidence, action, quantity, reason, realized_pnl=0.0):
        item = PaperDecision(
            datetime.now(timezone.utc).isoformat(),
            symbol, price, signal, direction, confidence, action, quantity, reason, realized_pnl,
        )
        self.decisions.append(item)
        self.decisions = self.decisions[-500:]
        return item

    async def step(self, symbol):
        candles = await fetch_klines(symbol, "1h", 200)
        if not candles:
            raise RuntimeError("no market candles")
        price = float(candles[-1].close)
        self.last_prices[symbol] = price
        signal, direction, confidence = self._signal(symbol, candles)
        position = self.paper.ledger.positions.get(symbol)
        quantity = float(position.quantity) if position else 0.0

        if quantity > 0:
            average_price = float(position.average_price)
            stop_price = average_price * (1.0 - settings.stop_loss_pct)
            if price <= stop_price or signal <= -0.35:
                notional = quantity * price
                fill = self.paper.sell(symbol, quantity, price)
                pnl = float((fill.price - average_price) * fill.quantity - fill.fee)
                self.risk.register_close(notional, pnl)
                reason = "stop_loss" if price <= stop_price else "signal_reversal"
                return self._record(symbol, price, signal, direction, confidence, "SELL", quantity, reason, pnl)

        if quantity == 0 and signal >= 0.35 and confidence >= 0.60:
            notional = min(settings.max_position_usd, self.paper.ledger.cash * 0.25)
            approved, reason = self.risk.approve_order(notional)
            if approved and notional > 0:
                qty = notional / price
                self.paper.buy(symbol, qty, price)
                self.risk.register_open(notional)
                return self._record(symbol, price, signal, direction, confidence, "BUY", qty, "strong_paper_signal")

            return self._record(symbol, price, signal, direction, confidence, "HOLD", 0.0, reason)

        return self._record(symbol, price, signal, direction, confidence, "HOLD", 0.0, "no_entry")

    async def initialize(self):
        if self.initialized:
            return
        await init_paper_store()
        await load_state(self.paper, self.risk)
        self.initialized = True

    async def run_once(self):
        if not self.risk.state.service_active:
            await save_state(self.paper, self.risk)
            return []
        events = []
        for symbol in self.symbols:
            try:
                events.append(await self.step(symbol))
            except Exception as exc:
                events.append(self._record(symbol, 0.0, 0.0, 0.0, 0.0, "ERROR", 0.0, str(exc)))
        await save_state(self.paper, self.risk)
        for event in events:
            await append_decision(event)
            await append_trade(event)
        await record_equity(self.paper, self.risk, self.last_prices)
        return events

    def snapshot(self):
        return {
            "mode": "PAPER",
            "live_trading": False,
            "cash": self.paper.ledger.cash,
            "equity": self.paper.equity(self.last_prices),
            "positions": [asdict(p) for p in self.paper.ledger.positions.values() if p.quantity > 0],
            "risk": self.risk.snapshot(),
            "last_decisions": [asdict(x) for x in self.decisions[-20:]],
        }

    async def report(self):
        return await paper_report(self.starting_cash)

    async def loop(self, interval_seconds=900, on_event: Callable[[PaperDecision], Awaitable[None]] | None = None):
        await self.initialize()
        self.running = True
        while self.running:
            for event in await self.run_once():
                if on_event and event.action in {"BUY", "SELL", "ERROR"}:
                    await on_event(event)
            await asyncio.sleep(interval_seconds)

    def pause(self):
        self.risk.pause()

    def start(self):
        self.risk.start()

    def resume(self):
        self.risk.resume()

    def emergency_stop(self):
        self.risk.emergency_stop()

    async def recent_history(self, limit=50):
        from app.paper.store import recent_decisions
        return await recent_decisions(limit)

    def stop(self):
        self.running = False


__all__ = ["AutonomousPaperEngine", "PaperDecision"]
