from dataclasses import asdict
from app.assets.universe import AssetUniverse
from app.research.multifactor import MultiFactorEngine
from app.research.factor_attribution import attribute

class StockResearchReport:
    """Read-only research report for one stock or ETF."""
    def __init__(self, universe=None, engine=None):
        self.universe=universe or AssetUniverse(); self.engine=engine or MultiFactorEngine()

    def build(self, symbol, candles, kronos_score=0.0, fundamentals=None, news=None, sector_score=0.0, risk_score=0.0):
        asset=self.universe.get(symbol)
        result=self.engine.evaluate(symbol,candles,kronos_score,fundamentals or {},news or {},sector_score,risk_score)
        components={
            "kronos":result.kronos,"technical":result.technical,"fundamental":result.fundamental,
            "sentiment":result.sentiment,"sector":result.sector,"risk":result.risk,
        }
        weights={"kronos":.25,"technical":.25,"fundamental":.20,"sentiment":.15,"sector":.10,"risk":.05}
        return {
            "symbol":symbol.upper(),
            "asset_type":asset.asset_type.value if asset else "unknown",
            "sector":asset.sector if asset else None,
            "score":result.score,
            "confidence":result.confidence,
            "components":components,
            "attribution":attribute(components,weights),
        }
