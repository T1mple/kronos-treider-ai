from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from app.research.backtester import BacktestConfig, BacktestResult, run_ohlc_backtest


@dataclass(frozen=True)
class StrategyBacktestResult:
    name: str
    result: BacktestResult


def run_strategy_suite(
    candles: Sequence,
    strategies: Mapping[str, Callable[[Sequence], str]],
    config: BacktestConfig = BacktestConfig(),
) -> tuple[StrategyBacktestResult, ...]:
    """Research-only comparison of independent strategies on identical data."""
    results = []
    for name, signal_fn in strategies.items():
        results.append(
            StrategyBacktestResult(
                name=name,
                result=run_ohlc_backtest(candles, signal_fn, config),
            )
        )
    return tuple(results)


def rank_strategy_suite(results: Sequence[StrategyBacktestResult]) -> tuple[StrategyBacktestResult, ...]:
    """Rank by risk-adjusted return, then drawdown and total return."""
    return tuple(sorted(
        results,
        key=lambda item: (
            item.result.sharpe,
            -item.result.max_drawdown,
            item.result.total_return,
        ),
        reverse=True,
    ))
