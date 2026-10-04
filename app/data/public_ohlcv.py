import csv
from datetime import datetime
from io import StringIO
import httpx
from app.market_data import Candle

async def fetch_csv(url: str, timeout: float = 15.0):
    async with httpx.AsyncClient(timeout=timeout) as client:
        response=await client.get(url)
        response.raise_for_status()
    rows=csv.DictReader(StringIO(response.text))
    candles=[]
    for row in rows:
        ts=row.get("timestamp") or row.get("time")
        if not ts: continue
        try: stamp=datetime.fromisoformat(ts.replace("Z","+00:00"))
        except ValueError: stamp=datetime.fromtimestamp(float(ts))
        candles.append(Candle(stamp,float(row["open"]),float(row["high"]),float(row["low"]),float(row["close"]),float(row["volume"])))
    return candles
