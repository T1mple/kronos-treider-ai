from datetime import datetime, time
from zoneinfo import ZoneInfo
from app.assets.models import MarketSession

US_EASTERN = ZoneInfo("America/New_York")
OPEN, CLOSE = time(9, 30), time(16, 0)
PRE_OPEN, AFTER_CLOSE = time(4, 0), time(20, 0)

def us_equity_session(moment: datetime) -> MarketSession:
    """Approximate NYSE/NASDAQ session; holidays require a full calendar provider."""
    local = moment.astimezone(US_EASTERN)
    if local.weekday() >= 5:
        return MarketSession.CLOSED
    t = local.time()
    if OPEN <= t < CLOSE: return MarketSession.OPEN
    if PRE_OPEN <= t < OPEN: return MarketSession.PRE_MARKET
    if CLOSE <= t < AFTER_CLOSE: return MarketSession.AFTER_HOURS
    return MarketSession.CLOSED
