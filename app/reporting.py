from dataclasses import dataclass

@dataclass
class StrategyReport:
    strategy: str
    trades: int
    return_pct: float
    max_drawdown_pct: float
    fees: float


def summarize_backtest(strategy, result):
    return StrategyReport(strategy, result.trades, result.total_return*100, result.max_drawdown*100, result.fees_paid)


def rank_reports(reports):
    return sorted(reports, key=lambda x: (x.return_pct, -x.max_drawdown_pct), reverse=True)
