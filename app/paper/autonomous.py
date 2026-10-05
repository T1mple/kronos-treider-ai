import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Awaitable, Callable

from app.config import settings
from app.data.binance_public import fetch_klines
from app.kronos_adapter import HeuristicKronosAdapter
from app.paper.engine import PaperTradingEngine
from app.paper.store import append_decision, append_trade, init_paper_store, load_state, paper_report, record_equity, save_state
from app.research.quant_engine import evaluate_quant
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
        self.kronos = HeuristicKronosAdapter()
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

    async def step(self, symbol):
        candles = await fetch_klines(symbol, "1h", 200)
        if not candles:
            raise RuntimeError("no market candles")

        price = float(candles[-1].close)
        self.last_prices[symbol] = price

        prediction = self.kronos.predict(symbol, candles)
        quant = evaluate_quant(
            candles,
            equity=self.paper.equity(self.last_prices),
            max_position_usd=settings.max_position_usd,
            risk_fraction=0.005,
            fee_rate=0.001,
            slippage_rate=0.0005,
            kronos_direction=prediction.direction,
            kronos_confidence=prediction.confidence,
        )
        if quant is None:
            return self._record(symbol, price, 0.0, prediction.direction, prediction.confidence, "HOLD", 0.0, "quant_not_ready")

        signal = quant.alpha
        position = self.paper.ledger.positions.get(symbol)
        quantity = float(position.quantity) if position else 0.0

        if quantity > 0:
            average_price = float(position.average_price)
            stop_distance = max(quant.stop_distance, average_price * settings.stop_loss_pct)
            stop_price = average_price - stop_distance
            if price <= stop_price or quant.action == "SHORT":
                notional = quantity * price
                fill = self.paper.sell(symbol, quantity, price)
                pnl = float((fill.price - average_price) * fill.quantity - fill.fee)
                self.risk.register_close(notional, pnl)
                reason = "atr_stop" if price <= stop_price else "quant_reversal"
                return self._record(symbol, price, signal, prediction.direction, prediction.confidence, "SELL", quantity, reason, pnl)

            return self._record(symbol, price, signal, prediction.direction, prediction.confidence, "HOLD", 0.0, "position_held")

        if quant.action == "LONG" and quant.position_usd > 0:
            approved, reason = self.risk.approve_order(quant.position_usd)
            if approved:
                qty = quant.position_usd / price
                self.paper.buy(symbol, qty, price)
                self.risk.register_open(quant.position_usd)
                return self._record(
                    symbol,
                    price,
                    signal,
                    prediction.direction,
                    prediction.confidence,
                    "BUY",
                    qty,
                    f"positive_ev:{quant.expected_return:.5f}:p={quant.win_probability:.3f}",
                )
            return self._record(symbol, price, signal, prediction.direction, prediction.confidence, "HOLD", 0.0, reason)

        return self._record(
            symbol,
            price,
            signal,
            prediction.direction,
            prediction.confidence,
            "HOLD",
            0.0,
            quant.reason,
        )

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
