from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
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
    from app.paper.ledger import Position

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


async def close_database():
    await engine.dispose()
