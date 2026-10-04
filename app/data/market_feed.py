from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class MarketTick:
    exchange: str
    symbol: str
    price: float
    volume: float = 0.0
    timestamp: str = ""

class MarketFeed:
    """Normalized market-data interface. Read-only, no order execution."""
    async def fetch(self, symbol: str) -> MarketTick:
        raise NotImplementedError

class StaticFeed(MarketFeed):
    def __init__(self, exchange="research", price=0.0):
        self.exchange=exchange
        self.price=float(price)

    async def fetch(self, symbol):
        return MarketTick(
            exchange=self.exchange,
            symbol=symbol,
            price=self.price,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
