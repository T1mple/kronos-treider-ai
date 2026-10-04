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
    """Long/flat research backtester. signal_fn receives candles available up to now."""
    def run(self,candles,starting_balance=300.0,fee_rate=0.001,slippage_rate=0.0005,signal_fn=None):
        candles=list(candles)
        balance=float(starting_balance); peak=balance; max_drawdown=0.0; fees=0.0; trades=0
        position=False; entry=None; entry_notional=0.0; history=[]
        for candle in candles:
            close=float(candle.close if hasattr(candle,"close") else candle["close"])
            if close<=0: continue
            history.append(candle)
            signal=float(signal_fn(history) if signal_fn else 0.0)
            signal=max(-1.0,min(1.0,signal)); want_long=signal>0
            if want_long and not position:
                entry=close*(1+slippage_rate); entry_notional=balance*0.25
                fee=entry_notional*fee_rate; balance-=fee; fees+=fee; position=True; trades+=1
            elif not want_long and position:
                exit_price=close*(1-slippage_rate); pnl=(exit_price/entry-1.0)*entry_notional
                fee=entry_notional*fee_rate; balance+=pnl-fee; fees+=fee
                position=False; entry=None; entry_notional=0.0; trades+=1
            equity=balance
            if position and entry: equity+=entry_notional*(close/entry-1.0)
            peak=max(peak,equity)
            if peak>0: max_drawdown=max(max_drawdown,(peak-equity)/peak)
        if position and entry and history:
            close=float(history[-1].close if hasattr(history[-1],"close") else history[-1]["close"])
            exit_price=close*(1-slippage_rate); pnl=(exit_price/entry-1.0)*entry_notional
            fee=entry_notional*fee_rate; balance+=pnl-fee; fees+=fee; trades+=1
        return BacktestResult(float(starting_balance),float(balance),trades,max_drawdown,balance/starting_balance-1.0 if starting_balance else 0.0,fees)
