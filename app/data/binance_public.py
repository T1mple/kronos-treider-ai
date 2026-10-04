from datetime import datetime, timezone
import httpx
from app.market_data import Candle

BASE_URL = "https://data-api.binance.vision"

async def fetch_klines(symbol="BTCUSDT", interval="1h", limit=500):
    params={"symbol":symbol.upper(),"interval":interval,"limit":min(int(limit),1000)}
    async with httpx.AsyncClient(timeout=20) as client:
        response=await client.get(f"{BASE_URL}/api/v3/klines",params=params)
        response.raise_for_status()
    candles=[]
    for row in response.json():
        candles.append(Candle(datetime.fromtimestamp(row[0]/1000, tz=timezone.utc),float(row[1]),float(row[2]),float(row[3]),float(row[4]),float(row[5])))
    return candles
