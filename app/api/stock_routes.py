from fastapi import APIRouter, HTTPException
from app.assets.universe import AssetUniverse
from app.data.stocks.provider import AlphaVantageStockProvider
from app.research.stock_report import StockResearchReport

router=APIRouter(prefix="/market",tags=["market"])
universe=AssetUniverse()
provider=AlphaVantageStockProvider()
reporter=StockResearchReport(universe)

@router.get("/asset/{symbol}")
async def asset_report(symbol: str):
    asset=universe.get(symbol)
    if asset is None: raise HTTPException(404,"Unknown research asset")
    candles=await provider.candles(symbol,limit=100)
    quote=await provider.quote(symbol)
    result=reporter.build(symbol,candles)
    result["price"]=quote.price
    result["volume"]=quote.volume
    result["timestamp"]=quote.timestamp.isoformat()
    return result
