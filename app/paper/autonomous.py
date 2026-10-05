import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Awaitable, Callable

from app.config import settings
from app.data.binance_public import fetch_klines
from app.paper.engine import PaperTradingEngine
from app.paper.store import append_decision, append_trade, init_paper_store, load_state, paper_report, record_equity, save_state
from app.risk import RiskEngine


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
    """Continuous quantitative simulation. It never submits real orders."""

    def __init__(self, symbols=("BTCUSDT", "ETHUSDT", "SOLUSDT"), starting_cash=300.0):
        if settings.live_trading:
            raise RuntimeError("AutonomousPaperEngine is paper-only; LIVE_TRADING must remain false")
        self.symbols = tuple(symbols)
        self.starting_cash = float(starting_cash)
        self.paper = PaperTradingEngine(starting_cash=starting_cash)
        self.risk = RiskEngine(settings)
        self.running = False
        self.decisions = []
        self.last_prices = {}
        self.initialized = False

    def _record(self, symbol, price, signal, direction, confidence, action, quantity, reason, realized_pnl=0.0):
        item = PaperDecision(
            datetime.now(timezone.utc).isoformat(),
            symbol,
            price,
            signal,
            direction,
            confidence,
            action,
            quantity,
            reason,
            realized_pnl,
        )
        self.decisions.append(item)
        self.decisions = self.decisions[-500:]
        return item

    async def step(self, symbol, research_result):
        candles = self._cycle_candles[symbol]
        price = float(candles[-1].close)
        self.last_prices[symbol] = price

        adaptive = research_result.get("adaptive", {})
        signal = float(adaptive.get("ensemble_score", 0.0))
        prediction = research_result.get("kronos", {})
        action = research_result.get("action", "HOLD")
        risk_gate = research_result.get("risk_gate", {})
        allocation = research_result.get("portfolio_allocation") or {}
        notional = float(allocation.get("notional_usd", 0.0))
        position = self.paper.ledger.positions.get(symbol)
        quantity = float(position.quantity) if position else 0.0

        if quantity > 0:
            if action == "SELL":
                average_price = float(position.average_price)
                fill = self.paper.sell(symbol, quantity, price)
                pnl = float((fill.price - average_price) * fill.quantity - fill.fee)
                self.risk.register_close(quantity * price, pnl)
                return self._record(
                    symbol, price, signal,
                    float(prediction.get("direction", 0.0)),
                    float(prediction.get("confidence", 0.0)),
                    "SELL", quantity, "research_reversal", pnl,
                )
            return self._record(
                symbol, price, signal,
                float(prediction.get("direction", 0.0)),
                float(prediction.get("confidence", 0.0)),
                "HOLD", 0.0, "position_held",
            )

        if action == "BUY" and risk_gate.get("approved") and notional > 0:
            qty = notional / price
            self.paper.buy(symbol, qty, price)
            self.risk.register_open(notional)
            return self._record(
                symbol, price, signal,
                float(prediction.get("direction", 0.0)),
                float(prediction.get("confidence", 0.0)),
                "BUY", qty,
                f"portfolio_allocation:{notional:.2f}",
            )

        return self._record(
            symbol, price, signal,
            float(prediction.get("direction", 0.0)),
            float(prediction.get("confidence", 0.0)),
            "HOLD", 0.0,
            str(risk_gate.get("reason") or research_result.get("action") or "no_entry"),
        )

    async def initialize(self):
        if self.initialized:
            return
        await init_paper_store()
        restored = await load_state(self.paper, self.risk)
        if not restored:
            self.risk.state.service_active = True
            await save_state(self.paper, self.risk)

        self.initialized = True

    async def run_once(self):
        if not self.risk.state.service_active:
            await save_state(self.paper, self.risk)
            return []

        self._cycle_candles = {}
        for symbol in self.symbols:
            candles = await fetch_klines(symbol, "1h", 200)
            if candles:
                self._cycle_candles[symbol] = candles

        if not self._cycle_candles:
            return []

        from app.research.system import ResearchSystem
        if not hasattr(self, "research"):
            self.research = ResearchSystem()

        for symbol, candles in self._cycle_candles.items():
            self.last_prices[symbol] = float(candles[-1].close)

        # Synchronize the shared research risk gate with persistent PAPER state.
        self.research.risk.state.exposure = self.risk.state.total_exposure
        self.research.risk.state.open_positions = self.risk.state.open_positions
        self.research.risk.state.daily_pnl = self.risk.state.daily_pnl
        self.research.risk.state.paused = self.risk.state.paused

        equity = self.paper.equity(self.last_prices)
        portfolio = self.research.evaluate_portfolio(self._cycle_candles, equity)
        events = []

        for symbol in self.symbols:
            result = portfolio["results"].get(symbol)
            if result is None:
                events.append(self._record(symbol, 0.0, 0.0, 0.0, 0.0, "ERROR", 0.0, "no_research_result"))
                continue
            events.append(await self.step(symbol, result))

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

    async def activate_paper(self):
        """Explicitly activate the persistent PAPER service state."""
        self.risk.state.circuit_breaker = False
        self.risk.state.paused = False
        self.risk.state.service_active = True
        await save_state(self.paper, self.risk)

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
