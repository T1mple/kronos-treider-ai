from app.assets.models import Asset, AssetType
from app.assets.profiles import ETFS, STOCKS

class AssetUniverse:
    """Registry of research assets. No order execution is performed here."""
    def __init__(self, assets=None):
        self._assets = dict(assets or {**STOCKS, **ETFS})
    def get(self, symbol: str):
        return self._assets.get(symbol.upper())
    def add(self, asset: Asset):
        self._assets[asset.symbol.upper()] = asset
    def all(self):
        return list(self._assets.values())
    def by_type(self, asset_type: AssetType):
        return [a for a in self._assets.values() if a.asset_type == asset_type]
    def by_sector(self, sector: str):
        wanted = sector.casefold()
        return [a for a in self._assets.values() if (a.sector or "").casefold() == wanted]
    def symbols(self):
        return sorted(self._assets)
