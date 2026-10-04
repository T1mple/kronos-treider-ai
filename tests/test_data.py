from pathlib import Path
from app.data.csv_loader import load_ohlcv_csv

def test_csv_loader(tmp_path: Path):
    p = tmp_path / "x.csv"
    p.write_text("timestamp,open,high,low,close,volume\\n2026-01-01T00:00:00+00:00,1,2,0.5,1.5,10\\n", encoding="utf-8")
    candles = load_ohlcv_csv(str(p))
    assert len(candles) == 1
    assert candles[0].close == 1.5
