from app.research.backtester import BacktestConfig, run_ohlc_backtest, walk_forward_slices


def _candles(prices):
    return [{"open": p, "high": p * 1.01, "low": p * .99, "close": p, "volume": 1.0} for p in prices]


def test_backtest_uses_next_bar_fill_and_costs():
    candles = _candles([100, 100, 110, 120, 120])
    result = run_ohlc_backtest(
        candles,
        lambda history: "LONG" if len(history) == 1 else "FLAT",
        BacktestConfig(initial_cash=1000, fee_rate=0.001, slippage_rate=0.0005),
    )
    assert result.trades == 1
    assert result.trade_log[0].entry_index == 1
    assert result.trade_log[0].exit_index == 2
    assert result.total_costs > 0
    assert result.final_equity > 0


def test_backtest_is_causal_for_signal():
    candles = _candles([100, 90, 200, 200])
    result = run_ohlc_backtest(
        candles,
        lambda history: "LONG" if history[-1]["close"] < 100 else "FLAT",
        BacktestConfig(initial_cash=1000),
    )
    # The signal sees 90 at index 1, so entry can only occur at index 2.
    assert result.trade_log[0].entry_index == 2


def test_walk_forward_slices_are_ordered():
    slices = list(walk_forward_slices(100, 40, 20, 20))
    assert slices == [(0, 40, 40, 60), (20, 60, 60, 80), (40, 80, 80, 100)]
