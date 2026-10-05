from dataclasses import asdict
from app.assets.universe import AssetUniverse
from app.assets.models import AssetType
from app.research.multifactor import MultiFactorEngine

class MarketScanner:
    """Ranks research assets without placing trades."""
    def __init__(self, universe=None, engine=None):
        self.universe=universe or AssetUniverse(); self.engine=engine or MultiFactorEngine()

    def rank(self, datasets, asset_type=None, limit=10):
        rows=[]
        for symbol,data in datasets.items():
            asset=self.universe.get(symbol)
            if asset is None or (asset_type and asset.asset_type != asset_type): continue
            result=self.engine.evaluate(symbol,data.get("candles",[]),data.get("kronos",0.0),data.get("fundamentals",{}),data.get("news",{}),data.get("sector_score",0.0),data.get("risk_score",0.0))
            rows.append(asdict(result)|{"asset_type":asset.asset_type.value,"sector":asset.sector})
        return sorted(rows,key=lambda x:x["score"],reverse=True)[:max(1,int(limit))]

    def stocks(self,datasets,limit=10): return self.rank(datasets,AssetType.STOCK,limit)
    def etfs(self,datasets,limit=10): return self.rank(datasets,AssetType.ETF,limit)
