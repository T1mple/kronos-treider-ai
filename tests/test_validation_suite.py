from datetime import datetime, timedelta, timezone

import pytest

from app.research.validation_suite import run_shared_capital_portfolio, walk_forward_validate


def _candles(prices):
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    rows = []
    for i, price in enumerate(prices):
        rows.append({
            "timestamp": start + timedelta(hours=i),
            "open": price,
            "high": price * 1.01,
            "low": price * 0.99,
            "close": price,
            "volume": 1.0,
        })
    return rows


def test_walk_forward_uses_sequential_disjoint_test_windows_and_reports_benchmarks():
    candles = _candles([100 + i * 0.1 for i in range(220)])
    report = walk_forward_validate(
        candles, signal_functions={"test": lambda history: 0.5},
        train_size=100, test_size=30, step=30,
    )
    assert report["mode"] == "RESEARCH_ONLY"
    assert report["real_orders"] is False
    assert len(report["windows"]) == 3
    assert report["windows"][0]["test_start"] == 100
    assert report["windows"][1]["test_start"] == 130
    row = report["windows"][0]["strategies"]["test"]
    assert set(row) == {"selected_threshold", "baseline_0_20", "tuned", "buy_hold"}
    assert "positive_window_rate" in report["aggregate"]["test:tuned"]


def test_walk_forward_rejects_too_short_data():
    with pytest.raises(ValueError):
        walk_forward_validate(_candles([100, 101, 102]), train_size=100, test_size=30)


def test_shared_portfolio_respects_cap_and_uses_one_initial_cash_pool():
    prices_a = [100 + i for i in range(30)]
    prices_b = [200 + i * 2 for i in range(30)]
    candles = {"A": _candles(prices_a), "B": _candles(prices_b)}
    signals = {"A": lambda history: 1.0, "B": lambda history: 1.0}
    result = run_shared_capital_portfolio(
        candles, signals, initial_cash=300, threshold=0.2,
        per_position_fraction=0.4, max_total_exposure=0.7,
    )
    assert result["initial_cash"] == 300
    assert result["final_equity"] > 0
    assert result["max_observed_exposure"] <= 0.700001
    assert result["real_orders"] is False
    assert len(result["equity_curve"]) == 30
