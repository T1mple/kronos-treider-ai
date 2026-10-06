import asyncio

from app.market_data import Candle
from app.paper.autonomous import AutonomousPaperEngine
from datetime import datetime, timezone


def _candle(price):
    return Candle(
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        price,
        price,
        price,
        price,
        1.0,
    )


def test_autonomous_paper_step_opens_and_closes_position():
    engine = AutonomousPaperEngine(symbols=("BTCUSDT",), starting_cash=300.0)
    engine._cycle_candles = {"BTCUSDT": [_candle(100.0)]}

    buy_result = {
        "adaptive": {"ensemble_score": 0.6},
        "kronos": {"direction": 1.0, "confidence": 0.8},
        "action": "BUY",
        "risk_gate": {"approved": True},
        "portfolio_allocation": {"notional_usd": 50.0},
    }
    event = asyncio.run(engine.step("BTCUSDT", buy_result))
    assert event.action == "BUY"
    assert engine.paper.ledger.positions["BTCUSDT"].quantity > 0
    assert engine.risk.state.open_positions == 1

    engine._cycle_candles = {"BTCUSDT": [_candle(110.0)]}
    sell_result = {
        "adaptive": {"ensemble_score": -0.6},
        "kronos": {"direction": -1.0, "confidence": 0.8},
        "action": "SELL",
        "risk_gate": {"approved": True},
        "portfolio_allocation": None,
    }
    event = asyncio.run(engine.step("BTCUSDT", sell_result))
    assert event.action == "SELL"
    assert engine.paper.ledger.positions["BTCUSDT"].quantity == 0
    assert engine.risk.state.open_positions == 0
    assert event.realized_pnl > 0
