from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class StressScenario:
    name: str
    return_shock: float = 0.0
    volatility_multiplier: float = 1.0
    fee_multiplier: float = 1.0


@dataclass(frozen=True)
class StressResult:
    scenario: str
    initial_cash: float
    final_equity: float
    total_return: float
    max_drawdown: float


def run_stress_test(
    returns: Sequence[float],
    scenarios: Sequence[StressScenario],
    initial_cash: float = 300.0,
) -> tuple[StressResult, ...]:
    """Apply deterministic return/volatility shocks to an existing portfolio return series."""
    if initial_cash <= 0 or not returns:
        raise ValueError("initial_cash and returns must be valid")
    results = []
    for scenario in scenarios:
        equity = initial_cash
        peak = equity
        max_dd = 0.0
        for raw in returns:
            shocked = float(raw) * scenario.volatility_multiplier + scenario.return_shock
            shocked = max(shocked, -0.999)
            equity *= 1.0 + shocked
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak if peak else 0.0)
        results.append(
            StressResult(
                scenario=scenario.name,
                initial_cash=initial_cash,
                final_equity=equity,
                total_return=equity / initial_cash - 1.0,
                max_drawdown=max_dd,
            )
        )
    return tuple(results)
