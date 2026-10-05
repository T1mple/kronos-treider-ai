from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class StockQuote:
    symbol: str
    price: float
    timestamp: datetime
    currency: str = "USD"
    volume: float = 0.0

class StockDataProvider:
    """Read-only provider boundary for stocks and ETFs."""
    async def quote(self, symbol: str) -> StockQuote:
        raise NotImplementedError
    async def candles(self, symbol: str, interval: str = "1d", limit: int = 250):
        raise NotImplementedError

class StaticStockDataProvider(StockDataProvider):
    """Deterministic provider for tests and local research."""
    def __init__(self, prices=None):
        self.prices = {k.upper(): float(v) for k, v in (prices or {}).items()}
    async def quote(self, symbol: str) -> StockQuote:
        return StockQuote(symbol.upper(), self.prices.get(symbol.upper(), 0.0), datetime.now(timezone.utc))
    async def candles(self, symbol: str, interval: str = "1d", limit: int = 250):
        raise NotImplementedError("Historical stock provider is intentionally not bundled yet")
