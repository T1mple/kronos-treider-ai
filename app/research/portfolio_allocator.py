from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Mapping, Sequence


@dataclass(frozen=True)
class StrategyAllocation:
    strategy: str
    weight: float
    expected_return: float
    volatility: float
    score: float
    reason: str


def _returns(values: Sequence[float]) -> list[float]:
    return [values[i] / values[i - 1] - 1.0 for i in range(1, len(values)) if values[i - 1] > 0]


def _strategy_stats(result) -> tuple[float, float]:
    curve = list(result.equity_curve)
    if len(curve) < 2:
        return 0.0, 0.0
    returns = _returns(curve)
    return (mean(returns) if returns else 0.0, pstdev(returns) if len(returns) > 1 else 0.0)


def allocate_strategies(
    results: Mapping[str, object],
    max_total_weight: float = 1.0,
    min_sharpe: float = 0.0,
    max_drawdown: float = 0.20,
) -> tuple[StrategyAllocation, ...]:
    """
    Research-only strategy allocator.

    Capital is weighted by risk-adjusted historical evidence. Strategies with
    excessive drawdown or insufficient Sharpe receive zero allocation.
    Weights are normalized to max_total_weight.
    """
    if not 0 < max_total_weight <= 1:
        raise ValueError("max_total_weight must be in (0, 1]")
    candidates = []
    for name, result in results.items():
        expected_return, volatility = _strategy_stats(result)
        sharpe = float(result.sharpe)
        drawdown = float(result.max_drawdown)
        if sharpe < min_sharpe or drawdown > max_drawdown or volatility <= 1e-12:
            continue
        # Conservative risk-adjusted score. No leverage and no Kelly sizing.
        score = max(0.0, expected_return) / volatility
        if score > 0:
            candidates.append((name, score, expected_return, volatility))

    total = sum(item[1] for item in candidates)
    if total <= 0:
        return tuple(
            StrategyAllocation(name, 0.0, 0.0, 0.0, 0.0, "filtered_or_no_positive_edge")
            for name in results
        )

    allocations = []
    for name, score, expected_return, volatility in candidates:
        weight = max_total_weight * score / total
        allocations.append(
            StrategyAllocation(
                name,
                weight,
                expected_return,
                volatility,
                score,
                "risk_adjusted_positive_edge",
            )
        )

    included = {item.strategy for item in allocations}
    for name, result in results.items():
        if name not in included:
            allocations.append(
                StrategyAllocation(
                    name, 0.0, 0.0, 0.0, 0.0, "filtered_or_no_positive_edge"
                )
            )
    return tuple(allocations)
