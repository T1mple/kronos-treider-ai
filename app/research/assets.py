from dataclasses import asdict, dataclass
from app.assets.models import Asset, AssetType, MarketSession
from app.data.stocks.calendar import us_equity_session

@dataclass(frozen=True)
class AssetContext:
    symbol: str
    asset_type: str
    exchange: str
    currency: str
    sector: str | None
    session: str

def context(asset: Asset, moment):
    if asset.asset_type in {AssetType.STOCK, AssetType.ETF}:
        session = us_equity_session(moment)
    elif asset.asset_type == AssetType.CRYPTO:
        session = MarketSession.CONTINUOUS
    else:
        session = MarketSession.CLOSED
    return AssetContext(asset.symbol, asset.asset_type.value, asset.exchange, asset.currency, asset.sector, session.value)

def context_dict(asset: Asset, moment):
    return asdict(context(asset, moment))
