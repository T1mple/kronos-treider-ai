from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Position:
    symbol: str
    quantity: float
    average_price: float
    realized_pnl: float = 0.0


@dataclass
class Fill:
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float


@dataclass
class PaperLedger:
    cash: float = 300.0
    positions: dict = field(default_factory=dict)
    fills: list = field(default_factory=list)

    def mark_price(self, symbol: str, price: float) -> float:
        pos = self.positions.get(symbol)
        return self.cash + (pos.quantity * price if pos else 0.0)

    def execute(self, symbol: str, side: str, quantity: float, price: float, fee_rate: float = 0.001):
        if quantity <= 0 or price <= 0:
            raise ValueError("quantity and price must be positive")
        side = side.lower()
        if side not in {"buy", "sell"}:
            raise ValueError("side must be 'buy' or 'sell'")
        fee = quantity * price * fee_rate
        pos = self.positions.setdefault(symbol, Position(symbol, 0.0, 0.0))
        if side == "buy":
            cost = quantity * price + fee
            if cost > self.cash:
                raise ValueError("insufficient paper cash")
            total = pos.quantity + quantity
            pos.average_price = ((pos.quantity * pos.average_price) + (quantity * price)) / total if total else 0.0
            pos.quantity = total
            self.cash -= cost
        else:
            if quantity > pos.quantity:
                raise ValueError("insufficient paper position")
            pnl = (price - pos.average_price) * quantity - fee
            pos.quantity -= quantity
            pos.realized_pnl += pnl
            self.cash += quantity * price - fee
            if pos.quantity == 0:
                pos.average_price = 0.0
        self.fills.append(Fill(datetime.now(timezone.utc), symbol, side, quantity, price, fee))
        return self.fills[-1]
