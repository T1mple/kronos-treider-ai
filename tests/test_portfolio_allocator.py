from app.research.multi_backtest import run_strategy_suite
from app.research.backtester import BacktestConfig
from app.research.portfolio_allocator import allocate_strategies


def _candles(prices):
    return [{"open": p, "high": p * 1.01, "low": p * .99, "close": p, "volume": 1.0} for p in prices]


def test_allocator_returns_all_strategies_and_bounds_weights():
    candles = _candles([100, 102, 104, 106, 108, 110, 112])
    strategies = {
        "momentum": lambda h: "LONG" if len(h) == 1 else "FLAT",
        "trend": lambda h: "LONG" if len(h) == 2 else "FLAT",
    }
    suite = run_strategy_suite(candles, strategies, BacktestConfig(initial_cash=300))
    results = {x.name: x.result for x in suite}
    allocations = allocate_strategies(results)
    assert {x.strategy for x in allocations} == set(strategies)
    assert sum(x.weight for x in allocations) <= 1.0 + 1e-12
    assert all(0 <= x.weight <= 1 for x in allocations)
