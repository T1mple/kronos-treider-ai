from dataclasses import dataclass, asdict
from app.backtest import Backtester
from app.reporting import rank_reports, summarize_backtest

@dataclass
class SelectionResult:
    selected: str | None
    reports: list

class StrategySelector:
    """Selects a research candidate using out-of-sample score only."""
    def __init__(self, backtester=None, drawdown_penalty=1.0):
        self.backtester=backtester or Backtester()
        self.drawdown_penalty=drawdown_penalty

    def evaluate(self,candles,strategies,starting_balance=300.0,fee_rate=0.001,slippage_rate=0.0005):
        reports=[]
        for name,fn in strategies.items():
            result=self.backtester.run(candles,starting_balance,fee_rate,slippage_rate,fn)
            reports.append(summarize_backtest(name,result,self.drawdown_penalty))
        ranked=rank_reports(reports)
        return SelectionResult(ranked[0].strategy if ranked else None,[asdict(x) for x in ranked])
