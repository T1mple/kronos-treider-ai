from dataclasses import dataclass
from statistics import mean

@dataclass
class Regime:
    name: str
    trend: float
    volatility: float
    confidence: float

def detect_regime(candles):
    closes=[float(c.close) for c in candles]
    if len(closes)<30:
        return Regime("UNKNOWN",0.0,0.0,0.0)
    returns=[closes[i]/closes[i-1]-1 for i in range(1,len(closes)) if closes[i-1]]
    recent=returns[-20:]
    avg=mean(recent); vol=(mean([(x-avg)**2 for x in recent])**0.5) if recent else 0.0
    trend=(closes[-1]/closes[-20]-1) if closes[-20] else 0.0
    name="HIGH_VOLATILITY" if vol>0.02 else ("TREND" if abs(trend)>0.03 else "RANGE")
    return Regime(name,max(-1,min(1,trend/0.05)),min(1,vol/0.05),min(1,len(recent)/20))
