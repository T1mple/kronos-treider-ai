"""Fast, causal threshold calibration with chronological holdout. Research only; never places orders."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Callable, Sequence

from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal

Signal = Callable[[Sequence], float]


@dataclass(frozen=True)
class CalibrationMetrics:
    start_equity: float
    final_equity: float
    total_return: float
    max_drawdown: float
    trades: int
    win_rate: float
    profit_factor: float
    fees_paid: float


def evaluate_threshold(
    candles: Sequence,
    signal_fn: Signal,
    threshold: float,
    *,
    context: Sequence = (),
    initial_cash: float = 300.0,
    allocation_fraction: float = 0.25,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
) -> CalibrationMetrics:
    """Long/flat test; decisions use candle close and execute no earlier than next open."""
    candles = list(candles)
    context = list(context)
    if len(candles) < 3:
        raise ValueError("At least 3 evaluation candles are required")
    if initial_cash <= 0 or not 0 < allocation_fraction <= 1:
        raise ValueError("Invalid capital or allocation fraction")

    cash = float(initial_cash)
    position = None
    peak = cash
    max_drawdown = 0.0
    equity_values = []
    trade_pnls = []
    fees_paid = 0.0

    def value(candle):
        return float(candle.close if hasattr(candle, "close") else candle["close"])

    def opening(candle):
        return float(candle.open if hasattr(candle, "open") else candle["open"])

    for i, candle in enumerate(candles[:-1]):
        close = value(candle)
        equity = cash + (position["qty"] * close if position else 0.0)
        equity_values.append(equity)
        peak = max(peak, equity)
        if peak > 0:
            max_drawdown = max(max_drawdown, (peak - equity) / peak)

        eval_start = max(0, i - 59)
        needed_context = max(0, 60 - (i + 1))
        history = context[-needed_context:] + candles[eval_start:i + 1] if needed_context else candles[eval_start:i + 1]
        score = float(signal_fn(history))
        want_long = score >= threshold
        fill = opening(candles[i + 1])

        if position and not want_long:
            exit_price = fill * (1.0 - slippage_rate)
            exit_fee = exit_price * position["qty"] * fee_rate
            proceeds = exit_price * position["qty"] - exit_fee
            cash += proceeds
            fees_paid += exit_fee
            trade_pnl = proceeds - position["entry_cost"] - position["notional"]
            trade_pnls.append(trade_pnl)
            position = None

        elif position is None and want_long:
            notional = cash * allocation_fraction
            entry_price = fill * (1.0 + slippage_rate)
            qty = notional / entry_price
            entry_fee = notional * fee_rate
            cash -= notional + entry_fee
            fees_paid += entry_fee
            position = {
                "qty": qty, "entry_price": entry_price,
                "notional": notional, "entry_cost": entry_fee,
            }

    last_close = value(candles[-1])
    if position:
        exit_price = last_close * (1.0 - slippage_rate)
        exit_fee = exit_price * position["qty"] * fee_rate
        proceeds = exit_price * position["qty"] - exit_fee
        cash += proceeds
        fees_paid += exit_fee
        trade_pnls.append(proceeds - position["entry_cost"] - position["notional"])
        position = None

    final_equity = cash
    if not equity_values or equity_values[-1] != final_equity:
        equity_values.append(final_equity)
    running_peak = float(initial_cash)
    max_drawdown = 0.0
    for point in equity_values:
        running_peak = max(running_peak, point)
        if running_peak > 0:
            max_drawdown = max(max_drawdown, (running_peak - point) / running_peak)
    wins = [p for p in trade_pnls if p > 0]
    losses = [-p for p in trade_pnls if p < 0]
    profit_factor = sum(wins) / sum(losses) if losses else (999.0 if wins else 0.0)
    return CalibrationMetrics(
        start_equity=float(initial_cash),
        final_equity=final_equity,
        total_return=final_equity / initial_cash - 1.0,
        max_drawdown=max_drawdown,
        trades=len(trade_pnls),
        win_rate=len(wins) / len(trade_pnls) if trade_pnls else 0.0,
        profit_factor=profit_factor,
        fees_paid=fees_paid,
    )


def calibrate_symbol(candles: Sequence, symbol: str, split_fraction: float = 0.70):
    """Choose thresholds on the first chronological segment and report untouched holdout."""
    candles = list(candles)
    split = int(len(candles) * split_fraction)
    if split < 100 or len(candles) - split < 50:
        raise ValueError(f"Not enough candles for train/holdout split: {len(candles)}")
    train, test = candles[:split], candles[split:]
    strategies = {
        "momentum": momentum_signal,
        "mean_reversion": mean_reversion_signal,
        "trend_filter": trend_filter_signal,
    }
    thresholds = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)
    results = []
    for name, signal_fn in strategies.items():
        candidates = []
        for threshold in thresholds:
            metrics = evaluate_threshold(train, signal_fn, threshold)
            # Prefer return while penalizing deep drawdowns; require some activity.
            objective = metrics.total_return - 0.5 * metrics.max_drawdown
            if metrics.trades < 3:
                objective -= 1.0
            candidates.append((objective, threshold, metrics))
        _, best_threshold, train_metrics = max(candidates, key=lambda item: item[0])
        baseline = evaluate_threshold(test, signal_fn, 0.20, context=train)
        calibrated = evaluate_threshold(test, signal_fn, best_threshold, context=train)
        results.append({
            "symbol": symbol,
            "strategy": name,
            "selected_threshold": best_threshold,
            "train": asdict(train_metrics),
            "holdout_baseline_threshold_0_20": asdict(baseline),
            "holdout_calibrated": asdict(calibrated),
            "holdout_improved": calibrated.total_return > baseline.total_return
                and calibrated.max_drawdown <= baseline.max_drawdown + 0.02,
            "thresholds_tested": list(thresholds),
        })
    return {
        "symbol": symbol,
        "candles": len(candles),
        "train_candles": len(train),
        "holdout_candles": len(test),
        "strategies": results,
    }
