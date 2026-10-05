from dataclasses import dataclass
from statistics import mean
from typing import Any, Iterable


@dataclass(frozen=True)
class PerformanceMetrics:
    trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    average_pnl: float
    max_drawdown: float
    profit_factor: float | None


def _pnl_values(trades: Iterable[Any]) -> list[float]:
    values: list[float] = []
    for trade in trades:
        if hasattr(trade, "pnl"):
            value = trade.pnl
        elif isinstance(trade, dict):
            value = trade.get("pnl", trade.get("outcome_pnl", 0.0))
        else:
            value = trade
        if value is not None:
            values.append(float(value))
    return values


def calculate_performance(trades: Iterable[Any], starting_equity: float = 300.0) -> dict:
    pnls = _pnl_values(trades)
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    equity = float(starting_equity)
    peak = equity
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        max_dd = max(max_dd, peak - equity)
    return {
        "trades": len(pnls),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(pnls) * 100 if pnls else 0.0,
        "total_pnl": sum(pnls),
        "average_pnl": mean(pnls) if pnls else 0.0,
        "max_drawdown": max_dd,
        "profit_factor": sum(wins) / abs(sum(losses)) if losses else None,
    }


class PerformanceAnalyzer:
    """Read-only performance analytics for paper/research results."""

    def __init__(self, starting_equity: float = 300.0):
        self.starting_equity = float(starting_equity)

    def analyze(self, trades: Iterable[Any]) -> PerformanceMetrics:
        result = calculate_performance(trades, self.starting_equity)
        return PerformanceMetrics(**result)

    def as_dict(self, trades: Iterable[Any]) -> dict:
        return self.analyze(trades).__dict__.copy()


__all__ = ["PerformanceMetrics", "PerformanceAnalyzer", "calculate_performance"]
