from dataclasses import dataclass
from app.backtest import Backtester

@dataclass
class WindowResult:
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    test_return: float
    test_drawdown: float
    trades: int

class WalkForwardValidator:
    """Rolling out-of-sample validation. No optimization or order execution."""
    def __init__(self, backtester=None):
        self.backtester=backtester or Backtester()

    def run(self, candles, signal_fn, train_size=200, test_size=50, step=50, starting_balance=300.0):
        results=[]
        start=0
        # Require a full following test window before opening the next validation
        # anchor. This preserves the original non-overlapping validation contract.
        while start+train_size+test_size <= len(candles):
            train_end=start+train_size
            test_end=train_end+test_size
            test=candles[train_end:test_end]
            result=self.backtester.run(test, starting_balance=starting_balance, signal_fn=signal_fn)
            results.append(WindowResult(start,train_end,train_end,test_end,result.total_return,result.max_drawdown,result.trades))
            if start+train_size+2*test_size > len(candles):
                break
            start += step
        return results
