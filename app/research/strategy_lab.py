from dataclasses import dataclass, asdict
from app.backtest import Backtester
from app.reporting import StrategyReport, summarize_backtest, rank_reports

@dataclass
class LabResult:
    reports: list

class StrategyLab:
    """Runs deterministic research backtests across multiple signal functions."""
    def __init__(self, backtester=None):
        self.backtester=backtester or Backtester()

    def run(self, candles, strategies, starting_balance=300.0, fee_rate=0.001, slippage_rate=0.0005):
        reports=[]
        for name, signal_fn in strategies.items():
            result=self.backtester.run(candles, starting_balance, fee_rate, slippage_rate, signal_fn)
            reports.append(summarize_backtest(name,result))
        return LabResult(rank_reports(reports))

    def as_dicts(self, result):
        return [asdict(x) for x in result.reports]
