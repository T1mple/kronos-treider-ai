from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.paper.store import PaperDecisionRow, PaperEquityRow, PaperTradeRow, SessionLocal

router = APIRouter(prefix="/paper", tags=["paper-dashboard"])


def _strategy(reason: str) -> str:
    mapping = {
        "strong_paper_signal": "ensemble",
        "signal_reversal": "reversal",
        "stop_loss": "stop_loss",
        "no_entry": "no_entry",
    }
    return mapping.get(reason, "other")


def _iso(value):
    return value.isoformat() if value else None


@router.get("/report")
async def report():
    from app.paper.store import paper_report
    return await paper_report()


@router.get("/equity")
async def equity(limit: int = Query(500, ge=1, le=5000)):
    async with SessionLocal() as session:
        result = await session.execute(
            select(PaperEquityRow)
            .order_by(PaperEquityRow.timestamp.desc(), PaperEquityRow.id.desc())
            .limit(limit)
        )
        rows = list(reversed(result.scalars().all()))
    return {
        "count": len(rows),
        "points": [
            {
                "timestamp": _iso(row.timestamp),
                "equity": float(row.equity),
                "cash": float(row.cash),
                "exposure": float(row.exposure),
                "open_positions": int(row.open_positions),
            }
            for row in rows
        ],
    }


@router.get("/trades")
async def trades(limit: int = Query(200, ge=1, le=2000)):
    async with SessionLocal() as session:
        result = await session.execute(
            select(PaperTradeRow)
            .order_by(PaperTradeRow.timestamp.desc(), PaperTradeRow.id.desc())
            .limit(limit)
        )
        rows = list(reversed(result.scalars().all()))
    return {
        "count": len(rows),
        "trades": [
            {
                "timestamp": _iso(row.timestamp),
                "symbol": row.symbol,
                "side": row.side,
                "quantity": float(row.quantity),
                "price": float(row.price),
                "realized_pnl": float(row.realized_pnl),
                "reason": row.reason,
                "strategy": _strategy(row.reason),
            }
            for row in rows
        ],
    }


@router.get("/decisions")
async def decisions(limit: int = Query(200, ge=1, le=2000)):
    async with SessionLocal() as session:
        result = await session.execute(
            select(PaperDecisionRow)
            .order_by(PaperDecisionRow.timestamp.desc(), PaperDecisionRow.id.desc())
            .limit(limit)
        )
        rows = list(reversed(result.scalars().all()))
    return {
        "count": len(rows),
        "decisions": [
            {
                "timestamp": _iso(row.timestamp),
                "symbol": row.symbol,
                "price": float(row.price),
                "signal": float(row.signal),
                "kronos_direction": float(row.kronos_direction),
                "kronos_confidence": float(row.kronos_confidence),
                "action": row.action,
                "quantity": float(row.quantity),
                "reason": row.reason,
                "strategy": _strategy(row.reason),
            }
            for row in rows
        ],
    }


@router.get("/breakdown")
async def breakdown():
    async with SessionLocal() as session:
        trades_result = await session.execute(
            select(PaperTradeRow).order_by(PaperTradeRow.timestamp.asc(), PaperTradeRow.id.asc())
        )
        equity_result = await session.execute(
            select(PaperEquityRow).order_by(PaperEquityRow.timestamp.asc(), PaperEquityRow.id.asc())
        )
        decisions_result = await session.execute(
            select(PaperDecisionRow).order_by(PaperDecisionRow.timestamp.asc(), PaperDecisionRow.id.asc())
        )
        trades = list(trades_result.scalars().all())
        equity_rows = list(equity_result.scalars().all())
        decisions = list(decisions_result.scalars().all())

    now = datetime.now(timezone.utc)
    day_start = now - timedelta(days=1)
    week_start = now - timedelta(days=7)

    def aggregate(start=None):
        selected_trades = [t for t in trades if start is None or t.timestamp >= start]
        selected_decisions = [d for d in decisions if start is None or d.timestamp >= start]
        closed = [t for t in selected_trades if t.side == "SELL"]
        pnl = sum(float(t.realized_pnl) for t in closed)

        symbols = defaultdict(lambda: {"trades": 0, "closed": 0, "pnl": 0.0, "wins": 0, "losses": 0})
        strategies = defaultdict(lambda: {"trades": 0, "closed": 0, "pnl": 0.0, "wins": 0, "losses": 0})
        for t in selected_trades:
            bucket = symbols[t.symbol]
            bucket["trades"] += 1
            if t.side == "SELL":
                bucket["closed"] += 1
                bucket["pnl"] += float(t.realized_pnl)
                bucket["wins"] += int(t.realized_pnl > 0)
                bucket["losses"] += int(t.realized_pnl < 0)
            strategy = _strategy(t.reason)
            bucket = strategies[strategy]
            bucket["trades"] += 1
            if t.side == "SELL":
                bucket["closed"] += 1
                bucket["pnl"] += float(t.realized_pnl)
                bucket["wins"] += int(t.realized_pnl > 0)
                bucket["losses"] += int(t.realized_pnl < 0)

        actions = defaultdict(int)
        for d in selected_decisions:
            actions[d.action] += 1

        return {
            "trades": len(selected_trades),
            "closed_trades": len(closed),
            "realized_pnl": pnl,
            "winning_trades": sum(x["wins"] for x in symbols.values()),
            "losing_trades": sum(x["losses"] for x in symbols.values()),
            "actions": dict(actions),
            "by_symbol": dict(symbols),
            "by_strategy": dict(strategies),
        }

    latest_equity = float(equity_rows[-1].equity) if equity_rows else 300.0
    return {
        "generated_at": now.isoformat(),
        "latest_equity": latest_equity,
        "all_time": aggregate(),
        "last_24h": aggregate(day_start),
        "last_7d": aggregate(week_start),
    }
