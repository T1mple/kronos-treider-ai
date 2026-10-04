import csv
from datetime import datetime
from app.market_data import Candle

def load_ohlcv_csv(path: str):
    """Load timestamp,open,high,low,close,volume CSV into Candle objects."""
    candles = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            timestamp = row.get("timestamp") or row.get("time")
            if timestamp is None:
                raise ValueError("CSV requires timestamp or time column")
            try:
                ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.fromtimestamp(float(timestamp))
            candles.append(Candle(ts, float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"]), float(row["volume"])))
    return candles
