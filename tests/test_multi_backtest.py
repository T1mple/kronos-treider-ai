from app.research.backtester import BacktestConfig
from app.research.multi_backtest import rank_strategy_suite, run_strategy_suite


def _candles(prices):
    return [{"open": p, "high": p * 1.01, "low": p * .99, "close": p, "volume": 1.0} for p in prices]


def test_all_strategies_are_executed():
    candles = _candles([100, 101, 102, 101, 104, 106, 105, 108])
    strategies = {
        "momentum": lambda history: "LONG" if len(history) >= 3 else "FLAT",
        "mean_reversion": lambda history: "LONG" if history[-1]["close"] < 102 else "FLAT",
        "trend": lambda history: "LONG" if len(history) >= 5 else "FLAT",
    }
    results = run_strategy_suite(candles, strategies, BacktestConfig(initial_cash=300))
    assert [x.name for x in results] == ["momentum", "mean_reversion", "trend"]
    assert all(x.result.final_equity > 0 for x in results)


def test_ranking_prefers_higher_sharpe():
    candles = _candles([100, 101, 102, 103, 104, 105])
    strategies = {
        "early": lambda history: "LONG" if len(history) == 1 else "FLAT",
        "late": lambda history: "LONG" if len(history) == 2 else "FLAT",
    }
    results = run_strategy_suite(candles, strategies, BacktestConfig(initial_cash=300))
    ranked = rank_strategy_suite(results)
    assert len(ranked) == 2
    assert ranked[0].result.sharpe >= ranked[1].result.sharpe
