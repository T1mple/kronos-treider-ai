from dataclasses import dataclass
from math import sqrt
from statistics import mean, pstdev
from typing import Callable, Sequence


@dataclass(frozen=True)
class BacktestConfig:
    initial_cash: float = 300.0
    fee_rate: float = 0.001
    slippage_rate: float = 0.0005
    annualization: float = 24.0 * 365.0
    allow_short: bool = False


@dataclass(frozen=True)
class TradeRecord:
    entry_index: int
    exit_index: int
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    gross_pnl: float
    costs: float
    net_pnl: float


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: float
    final_equity: float
    total_return: float
    sharpe: float
    sortino: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    trades: int
    avg_trade: float
    total_costs: float
    exposure: float
    equity_curve: tuple
    trade_log: tuple


def _close(candle):
    return float(candle.close if hasattr(candle, "close") else candle["close"])


def _open(candle):
    return float(candle.open if hasattr(candle, "open") else candle["open"])


def _returns(values):
    return [values[i] / values[i - 1] - 1.0 for i in range(1, len(values)) if values[i - 1] > 0]


def _fill(price, side, fee_rate, slippage_rate):
    # Conservative market-fill model: pay slippage on entry and exit.
    slip = fee_rate + slippage_rate
    return price * (1.0 + slip) if side == "LONG" else price * (1.0 - slip)


def _metrics(equity_curve, trades, config):
    if not equity_curve:
        return 0.0, 0.0, 0.0, 0.0
    rets = _returns(equity_curve)
    mean_r = mean(rets) if rets else 0.0
    sd = pstdev(rets) if len(rets) > 1 else 0.0
    sharpe = sqrt(config.annualization) * mean_r / sd if sd > 1e-12 else 0.0
    downside = [min(0.0, r) for r in rets]
    downside_sd = sqrt(mean([r * r for r in downside])) if downside else 0.0
    sortino = sqrt(config.annualization) * mean_r / downside_sd if downside_sd > 1e-12 else 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        max_dd = max(max_dd, (peak - value) / peak if peak else 0.0)
    return sharpe, sortino, max_dd, (equity_curve[-1] / equity_curve[0] - 1.0)


def run_ohlc_backtest(
    candles: Sequence,
    signal_fn: Callable[[Sequence], str],
    config: BacktestConfig = BacktestConfig(),
) -> BacktestResult:
    """
    Research-only causal OHLC backtest.

    signal_fn receives candles through t and returns LONG, SHORT or FLAT.
    A signal observed at t is filled at t+1 open, preventing same-bar look-ahead.
    Position size is 100% of available equity for long/short, with no leverage.
    """
    if len(candles) < 3:
        raise ValueError("at least 3 candles are required")
    if config.initial_cash <= 0:
        raise ValueError("initial_cash must be positive")

    cash = config.initial_cash
    equity_curve = []
    trades = []
    position = None
    total_costs = 0.0

    for t in range(len(candles) - 1):
        mark = _close(candles[t])
        equity = cash if position is None else cash + position["qty"] * mark
        equity_curve.append(equity)

        desired = str(signal_fn(candles[: t + 1]) or "FLAT").upper()
        if desired not in {"LONG", "SHORT", "FLAT"}:
            raise ValueError(f"unsupported signal: {desired}")
        if desired == "SHORT" and not config.allow_short:
            desired = "FLAT"

        current = position["side"] if position else "FLAT"
        if desired == current:
            continue

        fill_price = _open(candles[t + 1])
        if position is not None:
            exit_side = position["side"]
            exit_price = _fill(fill_price, exit_side, config.fee_rate, config.slippage_rate)
            qty = position["qty"]
            gross = (exit_price - position["entry_price"]) * qty if exit_side == "LONG" else (position["entry_price"] - exit_price) * qty
            entry_cost = position["entry_cost"]
            exit_cost = fill_price * qty * (config.fee_rate + config.slippage_rate)
            costs = entry_cost + exit_cost
            net = gross - costs
            cash += net
            total_costs += costs
            trades.append(TradeRecord(position["entry_index"], t + 1, exit_side,
                                      position["entry_price"], exit_price, qty, gross, costs, net))
            position = None

        if desired in {"LONG", "SHORT"}:
            qty = cash / fill_price if desired == "LONG" else cash / fill_price
            entry_price = _fill(fill_price, desired, config.fee_rate, config.slippage_rate)
            entry_cost = fill_price * qty * (config.fee_rate + config.slippage_rate)
            if desired == "LONG":
                cash -= entry_price * qty
            else:
                cash -= entry_cost
            position = {"side": desired, "qty": qty, "entry_price": entry_price,
                        "entry_index": t + 1, "entry_cost": entry_cost}

    if position is not None:
        fill_price = _close(candles[-1])
        exit_price = _fill(fill_price, position["side"], config.fee_rate, config.slippage_rate)
        qty = position["qty"]
        gross = (exit_price - position["entry_price"]) * qty if position["side"] == "LONG" else (position["entry_price"] - exit_price) * qty
        entry_cost = position["entry_cost"]
        exit_cost = fill_price * qty * (config.fee_rate + config.slippage_rate)
        costs = entry_cost + exit_cost
        net = gross - costs
        cash += net
        total_costs += costs
        trades.append(TradeRecord(position["entry_index"], len(candles) - 1, position["side"],
                                  position["entry_price"], exit_price, qty, gross, costs, net))
        position = None

    equity_curve.append(cash)
    sharpe, sortino, max_dd, total_return = _metrics(equity_curve, trades, config)
    wins = [t.net_pnl for t in trades if t.net_pnl > 0]
    losses = [-t.net_pnl for t in trades if t.net_pnl < 0]
    profit_factor = sum(wins) / sum(losses) if losses else (float("inf") if wins else 0.0)
    exposure = sum(abs(t.entry_price * t.quantity) for t in trades) / max(config.initial_cash, 1e-12)
    return BacktestResult(
        config.initial_cash, cash, total_return, sharpe, sortino, max_dd,
        len(wins) / len(trades) if trades else 0.0,
        profit_factor, len(trades), mean([t.net_pnl for t in trades]) if trades else 0.0,
        total_costs, exposure / max(len(candles), 1), tuple(equity_curve), tuple(trades),
    )


def walk_forward_slices(length: int, train_size: int, test_size: int, step: int = None):
    if min(length, train_size, test_size) <= 0:
        raise ValueError("length and window sizes must be positive")
    step = test_size if step is None else step
    if step <= 0:
        raise ValueError("step must be positive")
    start = 0
    while start + train_size + test_size <= length:
        yield (start, start + train_size, start + train_size, start + train_size + test_size)
        start += step
