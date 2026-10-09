"""Research-only validation tools. These functions never place exchange orders."""
from __future__ import annotations

from statistics import mean, median
from typing import Callable, Mapping, Sequence

from app.research.historical_calibration import evaluate_threshold
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal

Signal = Callable[[Sequence], float]
DEFAULT_SIGNALS = {
    "momentum": momentum_signal,
    "mean_reversion": mean_reversion_signal,
    "trend_filter": trend_filter_signal,
}


def _value(candle, field):
    return float(getattr(candle, field) if hasattr(candle, field) else candle[field])


def _objective(metrics):
    # Prefer return but penalize drawdown; avoid selecting a threshold with no activity.
    return metrics.total_return - 0.5 * metrics.max_drawdown - (1.0 if metrics.trades < 3 else 0.0)


def _summary(metrics):
    return {
        "return": metrics.total_return,
        "max_drawdown": metrics.max_drawdown,
        "trades": metrics.trades,
        "win_rate": metrics.win_rate,
        "profit_factor": metrics.profit_factor,
        "fees_paid": metrics.fees_paid,
        "final_equity": metrics.final_equity,
    }


def walk_forward_validate(
    candles: Sequence,
    *,
    signal_functions: Mapping[str, Signal] | None = None,
    train_size: int = 500,
    test_size: int = 100,
    step: int | None = None,
    thresholds: Sequence[float] = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40),
    initial_cash: float = 300.0,
    allocation_fraction: float = 0.25,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
):
    """Tune only on each training window and score on the following untouched window.

    Returns per-window results and aggregate out-of-sample statistics. Training candles
    are passed only as indicator warm-up context; no test candle enters optimization.
    """
    candles = list(candles)
    signals = dict(signal_functions or DEFAULT_SIGNALS)
    step = test_size if step is None else step
    if not signals:
        raise ValueError("at least one signal function is required")
    if train_size < 100 or test_size < 3 or step < 1:
        raise ValueError("train_size must be >= 100, test_size >= 3 and step >= 1")
    if not thresholds or any(float(t) <= 0 for t in thresholds):
        raise ValueError("thresholds must be positive and non-empty")
    if len(candles) < train_size + test_size:
        raise ValueError("not enough candles for one train/test window")

    windows = []
    start = 0
    while start + train_size + test_size <= len(candles):
        train_end = start + train_size
        test_end = train_end + test_size
        train = candles[start:train_end]
        test = candles[train_end:test_end]
        strategy_rows = {}
        for name, signal_fn in signals.items():
            train_results = [
                (float(threshold), evaluate_threshold(
                    train, signal_fn, float(threshold), initial_cash=initial_cash,
                    allocation_fraction=allocation_fraction, fee_rate=fee_rate,
                    slippage_rate=slippage_rate,
                ))
                for threshold in thresholds
            ]
            best_threshold, _ = max(train_results, key=lambda item: _objective(item[1]))
            baseline = evaluate_threshold(
                test, signal_fn, 0.20, context=train, initial_cash=initial_cash,
                allocation_fraction=allocation_fraction, fee_rate=fee_rate,
                slippage_rate=slippage_rate,
            )
            tuned = evaluate_threshold(
                test, signal_fn, best_threshold, context=train, initial_cash=initial_cash,
                allocation_fraction=allocation_fraction, fee_rate=fee_rate,
                slippage_rate=slippage_rate,
            )
            buy_hold = evaluate_threshold(
                test, lambda _history: 1.0, 0.20, context=train,
                initial_cash=initial_cash, allocation_fraction=1.0,
                fee_rate=fee_rate, slippage_rate=slippage_rate,
            )
            strategy_rows[name] = {
                "selected_threshold": best_threshold,
                "baseline_0_20": _summary(baseline),
                "tuned": _summary(tuned),
                "buy_hold": _summary(buy_hold),
            }
        windows.append({
            "train_start": start, "train_end": train_end,
            "test_start": train_end, "test_end": test_end,
            "strategies": strategy_rows,
        })
        start += step

    aggregate = {}
    for name in signals:
        for variant in ("baseline_0_20", "tuned", "buy_hold"):
            values = [w["strategies"][name][variant]["return"] for w in windows]
            drawdowns = [w["strategies"][name][variant]["max_drawdown"] for w in windows]
            aggregate[f"{name}:{variant}"] = {
                "windows": len(values),
                "mean_return": mean(values),
                "median_return": median(values),
                "positive_windows": sum(value > 0 for value in values),
                "positive_window_rate": sum(value > 0 for value in values) / len(values),
                "mean_max_drawdown": mean(drawdowns),
            }
    return {
        "mode": "RESEARCH_ONLY",
        "real_orders": False,
        "train_size": train_size,
        "test_size": test_size,
        "step": step,
        "windows": windows,
        "aggregate": aggregate,
    }


def run_shared_capital_portfolio(
    candles_by_symbol: Mapping[str, Sequence],
    signal_functions: Mapping[str, Signal],
    *,
    initial_cash: float = 300.0,
    threshold: float = 0.20,
    per_position_fraction: float = 0.20,
    max_total_exposure: float = 0.80,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
):
    """Simple synchronized long/flat portfolio simulation with one shared cash balance."""
    if not candles_by_symbol or set(candles_by_symbol) != set(signal_functions):
        raise ValueError("candles and signal_functions must contain the same non-empty symbols")
    lengths = {len(values) for values in candles_by_symbol.values()}
    if len(lengths) != 1 or next(iter(lengths)) < 3:
        raise ValueError("all symbols must have the same candle count (at least 3)")
    if initial_cash <= 0 or not 0 < per_position_fraction <= 1:
        raise ValueError("invalid initial cash or per-position fraction")
    if not 0 < max_total_exposure <= 1 or threshold <= 0:
        raise ValueError("exposure must be in (0, 1] and threshold must be positive")

    symbols = list(candles_by_symbol)
    length = next(iter(lengths))
    cash = float(initial_cash)
    positions = {}
    curve = []
    trades = 0
    fees_paid = 0.0
    exposure_curve = []

    for i in range(length - 1):
        equity = cash + sum(pos["qty"] * _value(candles_by_symbol[s][i], "close") for s, pos in positions.items())
        curve.append(equity)
        peak_exposure = sum(pos["qty"] * _value(candles_by_symbol[s][i], "close") for s, pos in positions.items())
        exposure_curve.append(peak_exposure / equity if equity > 0 else 0.0)

        # Decisions use candle i; all fills occur at candle i+1 open.
        scores = {}
        for symbol in symbols:
            # Signals use recent indicator history; bound the slice to keep long histories O(N), not O(N²).
            history = list(candles_by_symbol[symbol][max(0, i - 59):i + 1])
            scores[symbol] = float(signal_functions[symbol](history))

        for symbol in symbols:
            position = positions.get(symbol)
            wants_long = scores[symbol] >= threshold
            if position and not wants_long:
                fill = _value(candles_by_symbol[symbol][i + 1], "open") * (1.0 - slippage_rate)
                gross_proceeds = fill * position["qty"]
                fee = gross_proceeds * fee_rate
                cash += gross_proceeds - fee
                fees_paid += fee
                trades += 1
                del positions[symbol]

        for symbol in symbols:
            if symbol in positions or scores[symbol] < threshold:
                continue
            equity_now = cash + sum(pos["qty"] * _value(candles_by_symbol[s][i], "close") for s, pos in positions.items())
            exposure_now = sum(pos["qty"] * _value(candles_by_symbol[s][i], "close") for s, pos in positions.items())
            room = max(0.0, max_total_exposure * equity_now - exposure_now)
            notional = min(equity_now * per_position_fraction, room, cash / (1.0 + fee_rate))
            if notional <= 0:
                continue
            fill = _value(candles_by_symbol[symbol][i + 1], "open") * (1.0 + slippage_rate)
            qty = notional / fill
            fee = notional * fee_rate
            cash -= notional + fee
            fees_paid += fee
            positions[symbol] = {"qty": qty, "entry_price": fill}

    final_equity = cash
    for symbol, position in list(positions.items()):
        fill = _value(candles_by_symbol[symbol][-1], "close") * (1.0 - slippage_rate)
        proceeds = fill * position["qty"]
        fee = proceeds * fee_rate
        cash += proceeds - fee
        fees_paid += fee
        trades += 1
    final_equity = cash
    curve.append(final_equity)
    peak = float(initial_cash)
    max_drawdown = 0.0
    for point in curve:
        peak = max(peak, point)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - point) / peak)
    return {
        "mode": "RESEARCH_ONLY",
        "real_orders": False,
        "initial_cash": initial_cash,
        "final_equity": final_equity,
        "total_return": final_equity / initial_cash - 1.0,
        "max_drawdown": max_drawdown,
        "trades": trades,
        "fees_paid": fees_paid,
        "equity_curve": curve,
        "max_observed_exposure": max(exposure_curve, default=0.0),
        "max_total_exposure_limit": max_total_exposure,
    }
