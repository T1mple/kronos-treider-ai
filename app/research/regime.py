from dataclasses import dataclass
from statistics import mean, pstdev

@dataclass
class MarketRegime:
    name: str
    volatility: float
    trend_strength: float

class RegimeDetector:
    """Deterministic research-only market regime classifier."""
    def detect(self,candles,window=20,trend_window=10):
        closes=[float(c.close if hasattr(c,"close") else c["close"]) for c in candles]
        if len(closes)<max(window,trend_window+1):
            return MarketRegime("UNKNOWN",0.0,0.0)
        recent=closes[-window:]
        returns=[b/a-1.0 for a,b in zip(recent,recent[1:]) if a>0]
        volatility=pstdev(returns) if len(returns)>1 else 0.0
        base=closes[-trend_window]
        trend=abs(closes[-1]/base-1.0) if base>0 else 0.0
        trend_strength=min(1.0,trend/0.05)
        if volatility>=0.02:
            name="HIGH_VOLATILITY"
        elif trend_strength>=0.45:
            name="TRENDING"
        else:
            name="RANGING"
        return MarketRegime(name,volatility,trend_strength)
