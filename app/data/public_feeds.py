import httpx
from datetime import datetime, timezone
from app.data.market_feed import MarketFeed, MarketTick

def _now():
    return datetime.now(timezone.utc).isoformat()

class HttpMarketFeed(MarketFeed):
    def __init__(self, exchange, timeout=10.0):
        self.exchange=exchange
        self.timeout=timeout

    async def _get(self, url, params=None):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r=await client.get(url, params=params)
            r.raise_for_status()
            return r.json()

class BinanceFeed(HttpMarketFeed):
    def __init__(self): super().__init__("binance")
    async def fetch(self, symbol="BTCUSDT"):
        d=await self._get("https://api.binance.com/api/v3/ticker/bookTicker",{"symbol":symbol.upper()})
        bid=float(d["bidPrice"]); ask=float(d["askPrice"])
        return MarketTick(self.exchange,symbol.upper(),(bid+ask)/2,0.0,_now())

class OKXFeed(HttpMarketFeed):
    def __init__(self): super().__init__("okx")
    async def fetch(self, symbol="BTCUSDT"):
        inst=symbol.upper().replace("USDT","-USDT")
        d=await self._get("https://www.okx.com/api/v5/market/ticker",{"instId":inst})
        row=d["data"][0]; bid=float(row["bidPx"]); ask=float(row["askPx"])
        return MarketTick(self.exchange,symbol.upper(),(bid+ask)/2,float(row.get("vol24h") or 0),_now())

class BybitFeed(HttpMarketFeed):
    def __init__(self): super().__init__("bybit")
    async def fetch(self, symbol="BTCUSDT"):
        d=await self._get("https://api.bybit.com/v5/market/tickers",{"category":"spot","symbol":symbol.upper()})
        row=d["result"]["list"][0]; bid=float(row["bid1Price"]); ask=float(row["ask1Price"])
        return MarketTick(self.exchange,symbol.upper(),(bid+ask)/2,float(row.get("volume24h") or 0),_now())

class BitgetFeed(HttpMarketFeed):
    def __init__(self): super().__init__("bitget")
    async def fetch(self, symbol="BTCUSDT"):
        d=await self._get("https://api.bitget.com/api/v2/spot/market/tickers",{"symbol":symbol.upper()})
        row=d["data"][0]; bid=float(row["bidPr"]); ask=float(row["askPr"])
        return MarketTick(self.exchange,symbol.upper(),(bid+ask)/2,float(row.get("baseVol") or 0),_now())

class GateFeed(HttpMarketFeed):
    def __init__(self): super().__init__("gate")
    async def fetch(self, symbol="BTCUSDT"):
        pair=symbol.upper().replace("USDT","_USDT")
        d=await self._get("https://api.gateio.ws/api/v4/spot/tickers",{"currency_pair":pair})
        row=d[0]; bid=float(row["highest_bid"]); ask=float(row["lowest_ask"])
        return MarketTick(self.exchange,symbol.upper(),(bid+ask)/2,float(row.get("base_volume") or 0),_now())

def default_public_feeds():
    return [BinanceFeed(),OKXFeed(),BybitFeed(),BitgetFeed(),GateFeed()]
