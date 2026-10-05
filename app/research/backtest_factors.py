from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class HorizonResult:
    horizon: int
    observations: int
    hit_rate: float
    average_return: float
    average_return_long: float
    average_return_short: float

@dataclass(frozen=True)
class FactorBacktestResult:
    symbol: str
    total_observations: int
    horizons: list

def _clip(x): return max(-1.0, min(1.0, float(x)))

def run_factor_backtest(symbol, candles, score_fn, horizons=(1,5,20), min_score=0.20, step=1):
    """Historical research backtest. Signals are evaluated only against future closes."""
    rows=[]
    closes=[float(c.close) for c in candles]
    for i in range(0, max(0,len(closes)-max(horizons)), max(1,int(step))):
        score=float(score_fn(candles[:i+1]))
        if abs(score)<float(min_score) or closes[i] <= 0: continue
        rows.append((i, _clip(score)))
    results=[]
    for horizon in horizons:
        returns=[]; long=[]; short=[]; hits=0
        for i,score in rows:
            j=i+int(horizon)
            if j>=len(closes): continue
            ret=closes[j]/closes[i]-1.0
            signed=ret if score>0 else -ret
            returns.append(signed)
            (long if score>0 else short).append(ret)
            if signed>0: hits+=1
        n=len(returns)
        results.append(HorizonResult(int(horizon),n,hits/n if n else 0.0,sum(returns)/n if n else 0.0,sum(long)/len(long) if long else 0.0,sum(short)/len(short) if short else 0.0))
    return FactorBacktestResult(symbol,len(rows),[asdict(x) for x in results])
