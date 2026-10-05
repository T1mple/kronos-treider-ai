from datetime import datetime, timezone
from app.assets.models import AssetType, MarketSession
from app.assets.universe import AssetUniverse
from app.data.stocks.calendar import us_equity_session

def test_default_universe_contains_stocks_and_etfs():
    universe = AssetUniverse()
    assert universe.get("AAPL").asset_type == AssetType.STOCK
    assert universe.get("QQQ").asset_type == AssetType.ETF

def test_universe_sector_filter():
    universe = AssetUniverse()
    symbols = {a.symbol for a in universe.by_sector("Semiconductors")}
    assert {"NVDA", "AMD", "AVGO"} <= symbols

def test_us_equity_weekend_is_closed():
    saturday = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)
    assert us_equity_session(saturday) == MarketSession.CLOSED
