from dataclasses import dataclass

@dataclass
class BacktestResult:
    starting_balance: float
    ending_balance: float
    trades: int
    max_drawdown: float

class Backtester:
    def run(self, candles, starting_balance=300.0):
        return BacktestResult(starting_balance, starting_balance, 0, 0.0)
