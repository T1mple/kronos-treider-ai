from dataclasses import asdict
from statistics import mean

def calculate_performance(trades, starting_equity=300.0):
    pnls=[float(t.pnl if hasattr(t,"pnl") else t.get("pnl",0.0)) for t in trades]
    wins=[x for x in pnls if x>0]
    losses=[x for x in pnls if x<0]
    equity=starting_equity
    peak=equity
    max_dd=0.0
    for pnl in pnls:
        equity += pnl
        peak=max(peak,equity)
        max_dd=max(max_dd,peak-equity)
    return {
        "trades":len(pnls),
        "wins":len(wins),
        "losses":len(losses),
        "win_rate":len(wins)/len(pnls)*100 if pnls else 0.0,
        "total_pnl":sum(pnls),
        "average_pnl":mean(pnls) if pnls else 0.0,
        "max_drawdown":max_dd,
        "profit_factor":sum(wins)/abs(sum(losses)) if losses else None,
    }
