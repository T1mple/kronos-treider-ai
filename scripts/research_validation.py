"""Run research-only walk-forward and shared-capital validation from historical CSVs.

Example:
  python scripts/research_validation.py --data-dir /data/history --interval 1h
The report is informational only and never changes PAPER/live settings or places orders.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.data.csv_loader import load_ohlcv_csv
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.research.validation_suite import run_shared_capital_portfolio, walk_forward_validate


SIGNALS = {
    "momentum": momentum_signal,
    "mean_reversion": mean_reversion_signal,
    "trend_filter": trend_filter_signal,
}


def main():
    parser = argparse.ArgumentParser(description="Walk-forward and portfolio validation (research only)")
    parser.add_argument("--symbols", default="", help="Comma-separated symbols; default is PAPER universe")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--data-dir", default=os.getenv("KRONOS_HISTORY_DIR", "/data/history"))
    parser.add_argument("--report", default=os.getenv("KRONOS_VALIDATION_REPORT", "/data/research_validation.json"))
    parser.add_argument("--train-size", type=int, default=500)
    parser.add_argument("--test-size", type=int, default=100)
    parser.add_argument("--step", type=int, default=100)
    parser.add_argument("--initial-cash", type=float, default=300.0)
    args = parser.parse_args()

    symbols = list(dict.fromkeys(s.strip().upper() for s in (args.symbols or settings.paper_symbols).split(",") if s.strip()))
    if not symbols:
        parser.error("No symbols configured")
    data_dir = Path(args.data_dir)
    loaded = {}
    errors = []
    for symbol in symbols:
        path = data_dir / f"{symbol}_{args.interval}.csv"
        if not path.exists():
            errors.append({"symbol": symbol, "error": f"CSV not found: {path}"})
            continue
        try:
            candles = load_ohlcv_csv(str(path))
            candles.sort(key=lambda c: c.timestamp)
            if len(candles) < args.train_size + args.test_size:
                raise ValueError(f"only {len(candles)} candles; need at least {args.train_size + args.test_size}")
            loaded[symbol] = candles
        except Exception as exc:
            errors.append({"symbol": symbol, "error": str(exc)})

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "RESEARCH_ONLY",
        "real_orders": False,
        "initial_cash": args.initial_cash,
        "interval": args.interval,
        "parameters": {"train_size": args.train_size, "test_size": args.test_size, "step": args.step},
        "per_symbol_walk_forward": {},
        "shared_capital_portfolios": {},
        "errors": errors,
    }

    for symbol, candles in loaded.items():
        try:
            report["per_symbol_walk_forward"][symbol] = walk_forward_validate(
                candles, signal_functions=SIGNALS, train_size=args.train_size,
                test_size=args.test_size, step=args.step, initial_cash=args.initial_cash,
            )
        except Exception as exc:
            report["errors"].append({"symbol": symbol, "error": f"walk-forward: {exc}"})

    if len(loaded) >= 2:
        # Compare only synchronized timestamps; never combine mismatched market bars.
        by_symbol_time = {
            symbol: {c.timestamp: c for c in candles}
            for symbol, candles in loaded.items()
        }
        common_times = sorted(set.intersection(*(set(rows) for rows in by_symbol_time.values())))
        if len(common_times) >= 3:
            aligned = {
                symbol: [rows[ts] for ts in common_times]
                for symbol, rows in by_symbol_time.items()
            }
            for strategy_name, signal_fn in SIGNALS.items():
                try:
                    signal_map = {symbol: signal_fn for symbol in aligned}
                    report["shared_capital_portfolios"][strategy_name] = run_shared_capital_portfolio(
                        aligned, signal_map, initial_cash=args.initial_cash,
                    )
                except Exception as exc:
                    report["errors"].append({"portfolio": strategy_name, "error": str(exc)})
        else:
            report["errors"].append({"portfolio": "shared_capital", "error": "Not enough common timestamps to align symbols"})
    else:
        report["errors"].append({"portfolio": "shared_capital", "error": "At least two symbols with valid data are required"})

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Research validation report saved: {report_path}")
    print(f"Symbols validated: {len(loaded)}/{len(symbols)}; errors: {len(report['errors'])}")
    print("MODE: RESEARCH_ONLY | REAL ORDERS: OFF | PAPER settings unchanged")


if __name__ == "__main__":
    main()
