from dataclasses import dataclass
from math import sqrt
from random import Random
from statistics import mean, pstdev
from typing import Sequence


@dataclass(frozen=True)
class MonteCarloResult:
    simulations: int
    horizon: int
    terminal_equities: tuple[float, ...]
    percentile_5: float
    percentile_50: float
    percentile_95: float
    probability_of_loss: float
    probability_of_drawdown: float


def run_monte_carlo(
    returns: Sequence[float],
    initial_cash: float = 300.0,
    simulations: int = 2000,
    horizon: int | None = None,
    seed: int = 42,
    drawdown_threshold: float = 0.20,
) -> MonteCarloResult:
    """Bootstrap portfolio returns with replacement. Research/stress analysis only."""
    if initial_cash <= 0 or simulations <= 0 or not returns:
        raise ValueError("initial_cash, simulations and returns must be valid")
    horizon = horizon or len(returns)
    if horizon <= 0 or drawdown_threshold < 0:
        raise ValueError("invalid horizon or drawdown_threshold")

    clean = [float(r) for r in returns if r > -1.0]
    if not clean:
        raise ValueError("returns contain no usable observations")

    rng = Random(seed)
    terminals = []
    dd_events = 0
    for _ in range(simulations):
        equity = initial_cash
        peak = equity
        max_dd = 0.0
        for _ in range(horizon):
            equity *= 1.0 + rng.choice(clean)
            peak = max(peak, equity)
            max_dd = max(max_dd, (peak - equity) / peak if peak else 0.0)
        terminals.append(equity)
        dd_events += max_dd >= drawdown_threshold

    terminals.sort()
    def pct(p):
        return terminals[min(len(terminals) - 1, max(0, int((len(terminals) - 1) * p)))]

    return MonteCarloResult(
        simulations=simulations,
        horizon=horizon,
        terminal_equities=tuple(terminals),
        percentile_5=pct(0.05),
        percentile_50=pct(0.50),
        percentile_95=pct(0.95),
        probability_of_loss=sum(x < initial_cash for x in terminals) / simulations,
        probability_of_drawdown=dd_events / simulations,
    )
