from app.research.backtester import BacktestConfig
from app.research.portfolio_backtester import run_portfolio_backtest


def _candles(prices):
    return [
        {"open": p, "high": p * 1.01, "low": p * .99, "close": p, "volume": 1.0}
        for p in prices
    ]


def test_portfolio_backtester_is_causal_and_returns_metrics():
    prices = [100, 101, 103, 102, 105, 107, 106, 110, 112, 111, 115, 118]
    strategies = {
        "trend": lambda h: "LONG" if len(h) >= 2 and h[-1]["close"] > h[-2]["close"] else "FLAT",
        "mean_reversion": lambda h: "LONG" if len(h) >= 3 and h[-1]["close"] < h[-2]["close"] else "FLAT",
    }
    result = run_portfolio_backtest(
        _candles(prices),
        strategies,
        BacktestConfig(initial_cash=300.0),
        lookback=5,
    )
    assert result.initial_cash == 300.0
    assert len(result.equity_curve) == len(prices)
    assert result.final_equity > 0
    assert result.max_drawdown >= 0
    assert result.volatility >= 0
    assert set(result.final_allocations) == set(strategies)


def test_portfolio_allocator_caps_total_exposure():
    prices = list(range(100, 120))
    strategies = {
        "a": lambda h: "LONG",
        "b": lambda h: "LONG",
        "c": lambda h: "LONG",
    }
    result = run_portfolio_backtest(
        _candles(prices),
        strategies,
        BacktestConfig(initial_cash=300.0),
        lookback=5,
        max_total_weight=0.8,
    )
    assert all(point.exposure <= 0.8000001 for point in result.points)
