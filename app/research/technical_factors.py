from dataclasses import dataclass
from math import sqrt

@dataclass(frozen=True)
class TechnicalFactors:
    momentum: float
    trend: float
    rsi: float
    volatility: float
    volume: float
    score: float

def _clip(x): return max(-1.0, min(1.0, float(x)))
def _returns(closes): return [closes[i]/closes[i-1]-1 for i in range(1,len(closes)) if closes[i-1]]
def _sma(values,n): return sum(values[-n:])/n if len(values)>=n else None

def calculate(candles):
    closes=[float(x.close) for x in candles]; volumes=[float(getattr(x,'volume',0)) for x in candles]
    if len(closes)<20: return TechnicalFactors(0,0,0,0,0,0)
    ret=_returns(closes); momentum=_clip((closes[-1]/closes[-11]-1)/0.10)
    fast=_sma(closes,10); slow=_sma(closes,20); trend=_clip(((fast/slow)-1)/0.05) if slow else 0
    gains=[max(0,x) for x in ret[-14:]]; losses=[max(0,-x) for x in ret[-14:]]
    avg_gain=sum(gains)/14; avg_loss=sum(losses)/14
    rsi_value=100 if avg_loss==0 else 100-(100/(1+avg_gain/avg_loss)); rsi=_clip((rsi_value-50)/25)
    mean=sum(ret[-20:])/20; vol=sqrt(sum((x-mean)**2 for x in ret[-20:])/20); volatility=_clip(vol/0.03)
    vol_fast=_sma(volumes,5); vol_slow=_sma(volumes,20); volume=_clip((vol_fast/vol_slow-1)/0.50) if vol_slow else 0
    score=_clip(0.30*momentum+0.30*trend+0.15*rsi+0.10*volume-0.15*volatility)
    return TechnicalFactors(momentum,trend,rsi,volatility,volume,score)
