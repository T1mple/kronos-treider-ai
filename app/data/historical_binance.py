"""Paginated public Binance OHLCV history downloader. No exchange keys or orders required."""
from __future__ import annotations

import asyncio
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import httpx

BASE_URL = "https://data-api.binance.vision/api/v3/klines"
INTERVAL_MS = {
    "1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
    "30m": 1_800_000, "1h": 3_600_000, "2h": 7_200_000,
    "4h": 14_400_000, "6h": 21_600_000, "8h": 28_800_000,
    "12h": 43_200_000, "1d": 86_400_000, "3d": 259_200_000,
    "1w": 604_800_000,
}
CSV_FIELDS = ("timestamp", "open", "high", "low", "close", "volume")


def _rows_to_csv(rows: Iterable[list], path: Path) -> int:
    """Sort/deduplicate Binance kline rows by open time and write stable CSV."""
    unique = {int(row[0]): row for row in rows}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for open_ms in sorted(unique):
            row = unique[open_ms]
            ts = datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc).isoformat()
            writer.writerow({
                "timestamp": ts, "open": row[1], "high": row[2],
                "low": row[3], "close": row[4], "volume": row[5],
            })
    return len(unique)


async def download_klines(
    symbol: str,
    interval: str = "1h",
    years: float = 2,
    output_dir: str | Path = "/data/history",
    *,
    client: httpx.AsyncClient | None = None,
    pause_seconds: float = 0.12,
) -> Path:
    """Download all available candles in a date range using paginated requests."""
    if interval not in INTERVAL_MS:
        raise ValueError(f"Unsupported interval: {interval}")
    if years <= 0:
        raise ValueError("years must be positive")
    symbol = symbol.strip().upper()
    if not symbol or not symbol.endswith("USDT"):
        raise ValueError("symbol must be a non-empty USDT pair")

    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = int((datetime.now(timezone.utc) - timedelta(days=365.25 * years)).timestamp() * 1000)
    cursor = start_ms
    all_rows: list[list] = []
    owns_client = client is None
    session = client or httpx.AsyncClient(timeout=30)
    try:
        while cursor < end_ms:
            response = None
            for attempt in range(5):
                response = await session.get(BASE_URL, params={
                    "symbol": symbol, "interval": interval, "startTime": cursor,
                    "endTime": end_ms, "limit": 1000,
                })
                if response.status_code not in (418, 429, 500, 502, 503, 504):
                    break
                if attempt == 4:
                    response.raise_for_status()
                await asyncio.sleep(max(1.0, pause_seconds * 10) * (attempt + 1))
            response.raise_for_status()
            rows = response.json()
            if not rows:
                break
            all_rows.extend(rows)
            next_cursor = int(rows[-1][0]) + INTERVAL_MS[interval]
            if next_cursor <= cursor:
                raise RuntimeError(f"Binance pagination stalled for {symbol} {interval}")
            cursor = next_cursor
            if len(rows) < 1000:
                break
            if pause_seconds:
                await asyncio.sleep(pause_seconds)
    finally:
        if owns_client:
            await session.aclose()

    if len(all_rows) < 100:
        raise RuntimeError(f"Too little history for {symbol} {interval}: {len(all_rows)} candles")
    output = Path(output_dir) / f"{symbol}_{interval}.csv"
    _rows_to_csv(all_rows, output)
    return output
