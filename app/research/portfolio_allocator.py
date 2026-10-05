from dataclasses import dataclass
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


def _regime_multiplier(strategy: str, regime: str | None) -> float:
    if not regime:
        return 1.0
    regime = regime.upper()
    preferred = {
        "TREND": {"momentum": 1.25, "trend": 1.25, "mean_reversion": 0.75},
        "HIGH_VOLATILITY": {"market_making": 0.65, "grid": 0.75, "momentum": 1.05},
        "RANGE": {"mean_reversion": 1.20, "grid": 1.10, "trend": 0.80},
    }.get(regime, {})
    for key, multiplier in preferred.items():
        if key in strategy.lower():
            return multiplier
    return 1.0


def allocate_strategies(
    results: Mapping[str, object],
    max_total_weight: float = 1.0,
    min_sharpe: float = 0.0,
    max_drawdown: float = 0.20,
    correlation_matrix: Mapping[str, Mapping[str, float]] | None = None,
    max_correlation: float = 0.85,
    regime: str | None = None,
) -> tuple[StrategyAllocation, ...]:
    """
    Research-only allocator using historical edge, volatility, diversification
    and an optional market-regime multiplier. No leverage and no Kelly sizing.
    """
    if not 0 < max_total_weight <= 1:
        raise ValueError("max_total_weight must be in (0, 1]")
    if not 0 <= max_correlation <= 1:
        raise ValueError("max_correlation must be in [0, 1]")

    candidates = []
    for name, result in results.items():
        expected_return, volatility = _strategy_stats(result)
        sharpe = float(result.sharpe)
        drawdown = float(result.max_drawdown)
        if sharpe < min_sharpe or drawdown > max_drawdown or volatility <= 1e-12:
            continue
        score = max(0.0, expected_return) / volatility
        score *= _regime_multiplier(name, regime)
        if score > 0:
            candidates.append((name, score, expected_return, volatility))

    candidates.sort(key=lambda item: item[1], reverse=True)
    selected = []
    allocations = []
    for name, score, expected_return, volatility in candidates:
        if correlation_matrix:
            correlations = [
                abs(float(correlation_matrix.get(name, {}).get(other, 0.0)))
                for other in selected
            ]
            if correlations and max(correlations) > max_correlation:
                continue
        selected.append(name)
        allocations.append((name, score, expected_return, volatility))

    total = sum(item[1] for item in allocations)
    if total <= 0:
        return tuple(
            StrategyAllocation(name, 0.0, 0.0, 0.0, 0.0, "filtered_or_no_positive_edge")
            for name in results
        )

    result_allocations = []
    included = set()
    for name, score, expected_return, volatility in allocations:
        weight = max_total_weight * score / total
        result_allocations.append(
            StrategyAllocation(
                name, weight, expected_return, volatility, score,
                "risk_adjusted_diversified_regime_aware",
            )
        )
        included.add(name)

    for name in results:
        if name not in included:
            result_allocations.append(
                StrategyAllocation(name, 0.0, 0.0, 0.0, 0.0, "filtered_or_correlated")
            )
    return tuple(result_allocations)
