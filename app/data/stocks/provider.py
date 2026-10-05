from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.config import settings


@dataclass(frozen=True)
class StockQuote:
    symbol: str
    price: float
    timestamp: datetime
    currency: str = "USD"
    volume: float = 0.0


@dataclass(frozen=True)
class StockCandle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class StockDataProvider:
    """Read-only provider boundary for stocks and ETFs."""
    async def quote(self, symbol: str) -> StockQuote:
        raise NotImplementedError

    async def candles(self, symbol: str, interval: str = "1d", limit: int = 250) -> list[StockCandle]:
        raise NotImplementedError


class StaticStockDataProvider(StockDataProvider):
    """Deterministic provider for tests and local research."""
    def __init__(self, prices=None):
        self.prices = {k.upper(): float(v) for k, v in (prices or {}).items()}

    async def quote(self, symbol: str) -> StockQuote:
        return StockQuote(symbol.upper(), self.prices.get(symbol.upper(), 0.0), datetime.now(timezone.utc))

    async def candles(self, symbol: str, interval: str = "1d", limit: int = 250) -> list[StockCandle]:
        raise NotImplementedError("Historical stock provider is intentionally not bundled yet")


class AlphaVantageStockProvider(StockDataProvider):
    """Read-only Alpha Vantage adapter for daily stock/ETF research."""
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str | None = None, timeout: float = 20.0):
        self.api_key = api_key or settings.alpha_vantage_api_key
        self.timeout = timeout

    def _require_key(self) -> None:
        if not self.api_key:
            raise RuntimeError("ALPHA_VANTAGE_API_KEY is not configured")

    async def _get(self, params: dict) -> dict:
        self._require_key()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.BASE_URL, params={**params, "apikey": self.api_key})
            response.raise_for_status()
            payload = response.json()
        if "Error Message" in payload:
            raise RuntimeError(payload["Error Message"])
        if "Note" in payload:
            raise RuntimeError(payload["Note"])
        return payload

    async def quote(self, symbol: str) -> StockQuote:
        payload = await self._get({"function": "GLOBAL_QUOTE", "symbol": symbol.upper()})
        row = payload.get("Global Quote", {})
        price = float(row.get("05. price", 0.0))
        volume = float(row.get("06. volume", 0.0) or 0.0)
        timestamp = datetime.now(timezone.utc)
        return StockQuote(symbol.upper(), price, timestamp, "USD", volume)

    async def candles(self, symbol: str, interval: str = "1d", limit: int = 100) -> list[StockCandle]:
        if interval not in {"1d", "daily"}:
            raise ValueError("AlphaVantageStockProvider currently supports daily candles only")
        payload = await self._get({"function": "TIME_SERIES_DAILY", "symbol": symbol.upper(), "outputsize": "compact"})
        series = payload.get("Time Series (Daily)", {})
        rows = []
        for date_text, values in series.items():
            rows.append(StockCandle(
                timestamp=datetime.fromisoformat(date_text).replace(tzinfo=timezone.utc),
                open=float(values["1. open"]), high=float(values["2. high"]),
                low=float(values["3. low"]), close=float(values["4. close"]),
                volume=float(values["5. volume"]),
            ))
        rows.sort(key=lambda x: x.timestamp)
        return rows[-min(max(int(limit), 1), 100):]
