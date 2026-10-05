from dataclasses import dataclass
from enum import Enum

class AssetType(str, Enum):
    CRYPTO = "crypto"
    STOCK = "stock"
    ETF = "etf"
    POLYMARKET = "polymarket"

class MarketSession(str, Enum):
    OPEN = "MARKET_OPEN"
    CLOSED = "MARKET_CLOSED"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"
    CONTINUOUS = "CONTINUOUS"

@dataclass(frozen=True)
class Asset:
    symbol: str
    asset_type: AssetType
    exchange: str
    currency: str = "USD"
    sector: str | None = None
    country: str | None = None

    @property
    def is_tradable_research_asset(self) -> bool:
        return self.asset_type in {AssetType.CRYPTO, AssetType.STOCK, AssetType.ETF}
