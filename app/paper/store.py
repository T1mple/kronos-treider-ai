from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text, JSON, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


class Base(DeclarativeBase):
    pass


class PaperStateRow(Base):
    __tablename__ = "paper_state"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    cash: Mapped[float] = mapped_column(Float, nullable=False)
    positions: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    risk: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PaperDecisionRow(Base):
    __tablename__ = "paper_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    signal: Mapped[float] = mapped_column(Float, nullable=False)
    kronos_direction: Mapped[float] = mapped_column(Float, nullable=False)
    kronos_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class PaperTradeRow(Base):
    __tablename__ = "paper_trades"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reason: Mapped[str] = mapped_column(Text, nullable=False)


class PaperEquityRow(Base):
    __tablename__ = "paper_equity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    cash: Mapped[float] = mapped_column(Float, nullable=False)
    exposure: Mapped[float] = mapped_column(Float, nullable=False)
    open_positions: Mapped[int] = mapped_column(Integer, nullable=False)


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_paper_store():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _positions_payload(positions):
    return {
        symbol: {
            "symbol": pos.symbol,
            "quantity": pos.quantity,
            "average_price": pos.average_price,
            "realized_pnl": pos.realized_pnl,
        }
        for symbol, pos in positions.items()
        if pos.quantity != 0
    }


async def save_state(paper, risk):
    async with SessionLocal() as session:
        row = await session.get(PaperStateRow, 1)
        payload = _positions_payload(paper.ledger.positions)
        if row is None:
            row = PaperStateRow(
                id=1,
                cash=paper.ledger.cash,
                positions=payload,
                risk=risk.snapshot(),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(row)
        else:
            row.cash = paper.ledger.cash
            row.positions = payload
            row.risk = risk.snapshot()
            row.updated_at = datetime.now(timezone.utc)
        await session.commit()


async def load_state(paper, risk):
    from app.paper.ledger import Position

    async with SessionLocal() as session:
        row = await session.get(PaperStateRow, 1)
        if row is None:
            return False
        paper.ledger.cash = float(row.cash)
        paper.ledger.positions = {
            symbol: Position(
                symbol=value["symbol"],
                quantity=float(value["quantity"]),
                average_price=float(value["average_price"]),
                realized_pnl=float(value.get("realized_pnl", 0.0)),
            )
            for symbol, value in (row.positions or {}).items()
        }
        for key, value in (row.risk or {}).items():
            if hasattr(risk.state, key):
                setattr(risk.state, key, value)
        return True


async def append_decision(event):
    timestamp = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
    async with SessionLocal() as session:
        session.add(PaperDecisionRow(
            timestamp=timestamp,
            symbol=event.symbol,
            price=event.price,
            signal=event.signal,
            kronos_direction=event.kronos_direction,
            kronos_confidence=event.kronos_confidence,
            action=event.action,
            quantity=event.quantity,
            reason=event.reason,
        ))
        await session.commit()


async def append_trade(event):
    if event.action not in {"BUY", "SELL"}:
        return
    timestamp = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
    async with SessionLocal() as session:
        session.add(PaperTradeRow(
            timestamp=timestamp,
            symbol=event.symbol,
            side=event.action,
            quantity=event.quantity,
            price=event.price,
            realized_pnl=event.realized_pnl,
            reason=event.reason,
        ))
        await session.commit()


async def record_equity(paper, risk, marks):
    equity = float(paper.equity(marks))
    async with SessionLocal() as session:
        session.add(PaperEquityRow(
            timestamp=datetime.now(timezone.utc),
            equity=equity,
            cash=float(paper.ledger.cash),
            exposure=float(risk.state.total_exposure),
            open_positions=int(risk.state.open_positions),
        ))
        await session.commit()
    return equity


async def recent_decisions(limit=50):
    async with SessionLocal() as session:
        result = await session.execute(
            select(PaperDecisionRow).order_by(PaperDecisionRow.id.desc()).limit(limit)
        )
        rows = list(reversed(result.scalars().all()))
        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "symbol": row.symbol,
                "price": row.price,
                "signal": row.signal,
                "kronos_direction": row.kronos_direction,
                "kronos_confidence": row.kronos_confidence,
                "action": row.action,
                "quantity": row.quantity,
                "reason": row.reason,
            }
            for row in rows
        ]


async def paper_report(initial_equity=300.0):
    async with SessionLocal() as session:
        trades_result = await session.execute(
            select(PaperTradeRow).order_by(PaperTradeRow.timestamp.asc(), PaperTradeRow.id.asc())
        )
        equity_result = await session.execute(
            select(PaperEquityRow).order_by(PaperEquityRow.timestamp.asc(), PaperEquityRow.id.asc())
        )
        trades = list(trades_result.scalars().all())
        equity_rows = list(equity_result.scalars().all())

    latest_equity = float(equity_rows[-1].equity) if equity_rows else float(initial_equity)
    peak = float(initial_equity)
    max_drawdown = 0.0
    for row in equity_rows:
        peak = max(peak, float(row.equity))
        if peak:
            max_drawdown = max(max_drawdown, (peak - float(row.equity)) / peak)

    closed = [t for t in trades if t.side == "SELL"]
    wins = [t for t in closed if t.realized_pnl > 0]
    losses = [t for t in closed if t.realized_pnl < 0]
    realized = sum(float(t.realized_pnl) for t in closed)

    return {
        "equity": latest_equity,
        "total_pnl": latest_equity - initial_equity,
        "realized_pnl": realized,
        "closed_trades": len(closed),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": (len(wins) / len(closed)) if closed else 0.0,
        "max_drawdown": max_drawdown,
        "snapshots": len(equity_rows),
    }


async def close_database():
    await engine.dispose()
