from dataclasses import dataclass
from math import sqrt

@dataclass
class PerformanceMetrics:
    trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    average_pnl: float
    average_win: float
    average_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_like: float
    expectancy: float

class PerformanceAnalyzer:
    """Research analytics for completed paper/research outcomes."""
    def analyze(self,pnls):
        values=[float(x) for x in pnls]
        wins=[x for x in values if x>0]; losses=[x for x in values if x<0]
        equity=0.0; peak=0.0; max_dd=0.0
        for pnl in values:
            equity+=pnl; peak=max(peak,equity); max_dd=max(max_dd,peak-equity)
        gross_profit=sum(wins); gross_loss=abs(sum(losses))
        profit_factor=gross_profit/gross_loss if gross_loss else (float("inf") if gross_profit else 0.0)
        mean=sum(values)/len(values) if values else 0.0
        variance=sum((x-mean)**2 for x in values)/len(values) if values else 0.0
        std=variance**0.5
        sharpe=(mean/std)*sqrt(len(values)) if std and values else 0.0
        win_rate=len(wins)/len(values) if values else 0.0
        avg_win=sum(wins)/len(wins) if wins else 0.0
        avg_loss=sum(losses)/len(losses) if losses else 0.0
        expectancy=win_rate*avg_win+(1-win_rate)*avg_loss
        return PerformanceMetrics(len(values),len(wins),len(losses),win_rate,sum(values),mean,avg_win,avg_loss,profit_factor,max_dd,sharpe,expectancy)
