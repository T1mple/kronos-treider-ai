from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Callable, Mapping, Sequence

from app.research.backtester import BacktestConfig, BacktestResult, run_ohlc_backtest
from app.research.correlation import correlation
from app.research.regime import detect_regime


@dataclass(frozen=True)
class PortfolioPoint:
    index: int
    equity: float
    portfolio_return: float
    regime: str
    exposure: float
    allocations: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class PortfolioBacktestResult:
    initial_cash: float
    final_equity: float
    total_return: float
    sharpe: float
    sortino: float
    max_drawdown: float
    volatility: float
    turnover: float
    equity_curve: tuple[float, ...]
    points: tuple[PortfolioPoint, ...]
    strategy_results: Mapping[str, BacktestResult]
    final_allocations: Mapping[str, float]


def _returns(values):
    return [
        values[i] / values[i - 1] - 1.0
        for i in range(1, len(values))
        if values[i - 1] > 0
    ]


def _score(curve, lookback):
    values = list(curve)[-lookback:]
    rets = _returns(values)
    if len(rets) < 2:
        return 0.0, 0.0, 0.0
    mu = mean(rets)
    vol = pstdev(rets)
    sharpe = mu / vol if vol > 1e-12 else 0.0
    peak = values[0]
    dd = 0.0
    for value in values:
        peak = max(peak, value)
        dd = max(dd, (peak - value) / peak if peak else 0.0)
    return mu, vol, sharpe * max(0.0, 1.0 - dd)


def _regime_multiplier(name, regime):
    name = name.lower()
    table = {
        "TREND": {"trend": 1.20, "momentum": 1.20, "mean_reversion": 0.80},
        "RANGE": {"mean_reversion": 1.20, "grid": 1.10, "trend": 0.80},
        "HIGH_VOLATILITY": {"market_making": 0.65, "grid": 0.70, "momentum": 1.05},
    }
    for key, value in table.get(regime, {}).items():
        if key in name:
            return value
    return 1.0


def _weights(curves, index, lookback, regime, max_weight):
    names = list(curves)
    if index < 2:
        equal = min(max_weight, 1.0 / max(1, len(names)))
        return {name: equal for name in names}

    scores = {}
    selected = []
    for name in names:
        mu, vol, quality = _score(curves[name][:index], lookback)
        if vol <= 1e-12 or mu <= 0:
            continue
        scores[name] = (mu / vol) * max(0.0, quality) * _regime_multiplier(name, regime)

    for name in sorted(scores, key=scores.get, reverse=True):
        if not selected:
            selected.append(name)
            continue
        too_correlated = False
        for other in selected:
            a = curves[name][max(0, index - lookback):index]
            b = curves[other][max(0, index - lookback):index]
            if abs(correlation(a, b)) > 0.85:
                too_correlated = True
                break
        if not too_correlated:
            selected.append(name)

    if not selected:
        equal = min(max_weight, 1.0 / max(1, len(names)))
        return {name: equal for name in names}

    total = sum(scores[name] for name in selected)
    weights = {name: 0.0 for name in names}
    for name in selected:
        weights[name] = max_weight * scores[name] / total
    return weights


def run_portfolio_backtest(
    candles: Sequence,
    strategies: Mapping[str, Callable[[Sequence], str]],
    config: BacktestConfig = BacktestConfig(),
    lookback: int = 50,
    rebalance_every: int = 1,
    max_total_weight: float = 1.0,
) -> PortfolioBacktestResult:
    """Combine causal strategy equity curves into a portfolio-level research backtest.

    Individual strategies are first backtested independently. Portfolio weights are
    then chosen only from information available before each portfolio period. This
    avoids using future strategy performance when allocating capital.
    """
    if len(candles) < 3:
        raise ValueError("at least 3 candles are required")
    if not strategies:
        raise ValueError("at least one strategy is required")
    if lookback < 5 or rebalance_every <= 0:
        raise ValueError("invalid lookback or rebalance_every")
    if not 0 < max_total_weight <= 1:
        raise ValueError("max_total_weight must be in (0, 1]")

    results = {
        name: run_ohlc_backtest(candles, signal_fn, config)
        for name, signal_fn in strategies.items()
    }
    curves = {name: list(result.equity_curve) for name, result in results.items()}
    length = min(len(curve) for curve in curves.values())
    if length < 2:
        raise ValueError("strategy equity curves are too short")

    equity = float(config.initial_cash)
    portfolio_curve = [equity]
    points = []
    previous_weights = {name: 0.0 for name in curves}
    turnover = 0.0

    for index in range(1, length):
        if (index - 1) % rebalance_every == 0:
            regime = detect_regime(candles[:min(index, len(candles))]).name
            weights = _weights(curves, index, lookback, regime, max_total_weight)
            turnover += sum(abs(weights[name] - previous_weights.get(name, 0.0)) for name in curves)
            previous_weights = weights
        else:
            weights = previous_weights
            regime = detect_regime(candles[:min(index, len(candles))]).name

        period_returns = {
            name: curves[name][index] / curves[name][index - 1] - 1.0
            if curves[name][index - 1] > 0 else 0.0
            for name in curves
        }
        portfolio_return = sum(weights[name] * period_returns[name] for name in curves)
        equity *= 1.0 + portfolio_return
        exposure = sum(abs(weight) for weight in weights.values())
        portfolio_curve.append(equity)
        points.append(
            PortfolioPoint(
                index=index,
                equity=equity,
                portfolio_return=portfolio_return,
                regime=regime,
                exposure=exposure,
                allocations=tuple(sorted(weights.items())),
            )
        )

    rets = _returns(portfolio_curve)
    vol = pstdev(rets) * sqrt(config.annualization) if len(rets) > 1 else 0.0
    mean_r = mean(rets) if rets else 0.0
    sharpe = mean_r / pstdev(rets) * sqrt(config.annualization) if len(rets) > 1 and pstdev(rets) > 1e-12 else 0.0
    downside = [min(0.0, value) for value in rets]
    downside_dev = sqrt(mean([value * value for value in downside])) if downside else 0.0
    sortino = mean_r / downside_dev * sqrt(config.annualization) if downside_dev > 1e-12 else 0.0

    peak = portfolio_curve[0]
    max_dd = 0.0
    for value in portfolio_curve:
        peak = max(peak, value)
        max_dd = max(max_dd, (peak - value) / peak if peak else 0.0)

    final_allocations = dict(points[-1].allocations) if points else previous_weights
    return PortfolioBacktestResult(
        initial_cash=config.initial_cash,
        final_equity=equity,
        total_return=equity / config.initial_cash - 1.0,
        sharpe=sharpe,
        sortino=sortino,
        max_drawdown=max_dd,
        volatility=vol,
        turnover=turnover,
        equity_curve=tuple(portfolio_curve),
        points=tuple(points),
        strategy_results=results,
        final_allocations=final_allocations,
    )
