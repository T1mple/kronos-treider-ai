"""Download historical Binance candles and calibrate PAPER strategy thresholds.

Example in Docker:
  docker compose run --rm app python scripts/historical_calibration.py --years 2 --interval 1h
Data and JSON report are written under /data/history and /data respectively.
This tool is research-only and never sends orders.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

# Make the repository root importable when this file is run directly as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.csv_loader import load_ohlcv_csv
from app.data.historical_binance import download_klines
from app.config import settings
from app.research.historical_calibration import calibrate_symbol


async def download_all(symbols, interval, years, data_dir):
    paths = {}
    errors = []
    for index, symbol in enumerate(symbols, start=1):
        print(f"[{index}/{len(symbols)}] Downloading {symbol} {interval}, {years:g} year(s)...", flush=True)
        try:
            path = await download_klines(symbol, interval, years, data_dir)
            paths[symbol] = path
            print(f"  saved {path}", flush=True)
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})
            print(f"  ERROR: {exc}; continuing with remaining symbols", flush=True)
    return paths, errors


def main():
    parser = argparse.ArgumentParser(description="Download history and calibrate Kronos research signals")
    parser.add_argument("--symbols", default="", help="Comma-separated symbols; default is PAPER universe from settings")
    parser.add_argument("--years", type=float, default=2.0, help="Historical years to download (default: 2)")
    parser.add_argument("--interval", default="1h", help="Binance candle interval (default: 1h)")
    parser.add_argument("--data-dir", default=os.getenv("KRONOS_HISTORY_DIR", "/data/history"))
    parser.add_argument("--report", default=os.getenv("KRONOS_CALIBRATION_REPORT", "/data/historical_calibration.json"))
    parser.add_argument("--skip-download", action="store_true", help="Calibrate from existing CSV files")
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in (args.symbols or settings.paper_symbols).split(",") if s.strip()]
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        parser.error("No symbols configured")
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    download_errors = []
    if not args.skip_download:
        _, download_errors = asyncio.run(download_all(symbols, args.interval, args.years, data_dir))

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "RESEARCH_ONLY",
        "real_orders": False,
        "interval": args.interval,
        "requested_years": args.years,
        "symbols_requested": symbols,
        "results": [],
        "errors": list(download_errors),
    }
    for symbol in symbols:
        path = data_dir / f"{symbol}_{args.interval}.csv"
        if not path.exists():
            report["errors"].append({"symbol": symbol, "error": f"CSV not found: {path}"})
            continue
        try:
            candles = load_ohlcv_csv(str(path))
            candles.sort(key=lambda candle: candle.timestamp)
            result = calibrate_symbol(candles, symbol)
            report["results"].append(result)
            print(
                f"{symbol}: {len(candles)} candles; "
                f"{len(result['strategies'])} strategies evaluated",
                flush=True,
            )
        except Exception as exc:
            report["errors"].append({"symbol": symbol, "error": str(exc)})
            print(f"{symbol}: ERROR: {exc}", flush=True)

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report saved: {report_path}")
    print(f"Completed: {len(report['results'])}/{len(symbols)} symbols; errors: {len(report['errors'])}")
    for item in report["results"]:
        for strategy in item["strategies"]:
            baseline = strategy["holdout_baseline_threshold_0_20"]
            calibrated = strategy["holdout_calibrated"]
            print(
                f"{item['symbol']} {strategy['strategy']}: "
                f"holdout return {baseline['total_return']:.2%} -> "
                f"{calibrated['total_return']:.2%}; "
                f"drawdown {calibrated['max_drawdown']:.2%}; "
                f"threshold={strategy['selected_threshold']:.2f}; "
                f"trades={calibrated['trades']}"
            )
    if report["errors"]:
        print("Download/data errors:")
        for error in report["errors"]:
            print(f"  {error['symbol']}: {error['error']}")
    print("This report does not change the running PAPER bot's settings.")


if __name__ == "__main__":
    main()
