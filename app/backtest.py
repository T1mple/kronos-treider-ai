from dataclasses import dataclass

@dataclass
class BacktestResult:
    starting_balance: float
    ending_balance: float
    trades: int
    max_drawdown: float
    total_return: float = 0.0
    fees_paid: float = 0.0

class Backtester:
    """Long/flat signal backtester for research only. No live execution."""

    def run(self, candles, starting_balance=300.0, fee_rate=0.001, slippage_rate=0.0005, signal_fn=None):
        balance = float(starting_balance)
        peak = balance
        max_drawdown = 0.0
        fees = 0.0
        trades = 0
        position = False
        entry = None
        entry_notional = 0.0

        for candle in candles:
            close = float(candle.close if hasattr(candle, "close") else candle["close"])
            if close <= 0:
                continue
            signal = float(signal_fn(candle) if signal_fn else 0.0)
            signal = max(-1.0, min(1.0, signal))
            want_long = signal > 0

            if want_long and not position:
                entry = close * (1 + slippage_rate)
                entry_notional = balance * 0.25
                fee = entry_notional * fee_rate
                balance -= fee
                fees += fee
                position = True
                trades += 1
            elif not want_long and position:
                exit_price = close * (1 - slippage_rate)
                pnl = (exit_price / entry - 1.0) * entry_notional
                fee = entry_notional * fee_rate
                balance += pnl - fee
                fees += fee
                position = False
                entry = None
                entry_notional = 0.0
                trades += 1

            equity = balance
            if position and entry:
                equity += entry_notional * (close / entry - 1.0)
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - equity) / peak)

        if position and entry:
            last = candles[-1]
            close = float(last.close if hasattr(last, "close") else last["close"])
            exit_price = close * (1 - slippage_rate)
            pnl = (exit_price / entry - 1.0) * entry_notional
            fee = entry_notional * fee_rate
            balance += pnl - fee
            fees += fee
            trades += 1

        return BacktestResult(
            starting_balance=float(starting_balance),
            ending_balance=float(balance),
            trades=trades,
            max_drawdown=max_drawdown,
            total_return=balance / starting_balance - 1.0 if starting_balance else 0.0,
            fees_paid=fees,
        )
