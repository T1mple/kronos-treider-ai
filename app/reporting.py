from dataclasses import dataclass

@dataclass
class StrategyReport:
    strategy: str
    trades: int
    return_pct: float
    max_drawdown_pct: float
    fees: float
    score: float = 0.0


def summarize_backtest(strategy, result, drawdown_penalty=1.0):
    return_pct=result.total_return*100
    drawdown_pct=result.max_drawdown*100
    score=return_pct-(drawdown_penalty*drawdown_pct)
    return StrategyReport(strategy,result.trades,return_pct,drawdown_pct,result.fees_paid,score)


def rank_reports(reports):
    return sorted(reports,key=lambda x:(x.score,x.return_pct,-x.max_drawdown_pct),reverse=True)
