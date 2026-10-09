from datetime import datetime, timedelta, timezone

from app.data.csv_loader import load_ohlcv_csv
from app.data.historical_binance import _rows_to_csv
from app.research.historical_calibration import calibrate_symbol, evaluate_threshold


def _candles(n=320):
    rows = []
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    price = 100.0
    for i in range(n):
        price *= 1.002 if (i // 8) % 2 == 0 else 0.998
        rows.append({
            "timestamp": start + timedelta(hours=i),
            "open": price * 0.999,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": 100.0,
        })
    return rows


def test_historical_binance_writer_deduplicates_and_csv_loads(tmp_path):
    row_a = [1735689600000, "100", "102", "99", "101", "12"]
    row_b = [1735689600000, "100", "102", "99", "101", "12"]
    path = tmp_path / "BTCUSDT_1h.csv"
    count = _rows_to_csv([row_a, row_b], path)
    candles = load_ohlcv_csv(str(path))
    assert count == 1
    assert len(candles) == 1
    assert candles[0].close == 101.0


def test_threshold_evaluation_accounts_for_costs_and_drawdown():
    candles = _candles()
    def signal(history):
        if len(history) < 2:
            return 0.0
        a = history[-1]["close"]
        b = history[-2]["close"]
        return 0.5 if a > b else -0.5

    result = evaluate_threshold(candles, signal, 0.2)
    assert result.start_equity == 300.0
    assert result.trades > 0
    assert result.fees_paid > 0
    assert result.max_drawdown >= 0
    assert result.final_equity > 0


def test_calibration_uses_chronological_holdout():
    candles = _candles()
    result = calibrate_symbol(candles, "BTCUSDT")
    assert result["candles"] == len(candles)
    assert result["train_candles"] + result["holdout_candles"] == len(candles)
    assert {row["strategy"] for row in result["strategies"]} == {
        "momentum", "mean_reversion", "trend_filter"
    }
    for row in result["strategies"]:
        assert row["selected_threshold"] in row["thresholds_tested"]
        assert "holdout_calibrated" in row
        assert "holdout_baseline_threshold_0_20" in row
