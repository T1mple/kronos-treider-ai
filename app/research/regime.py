from dataclasses import dataclass
from math import log, sqrt
from statistics import pstdev

@dataclass(frozen=True)
class Regime:
    name: str
    trend: float
    volatility: float
    confidence: float
    momentum: float = 0.0

def _close(c):
    return float(c.close if hasattr(c, "close") else c["close"])

def detect_regime(candles):
    closes = [_close(c) for c in candles]
    if len(closes) < 30:
        return Regime("UNKNOWN", 0.0, 0.0, 0.0, 0.0)
    returns = [log(closes[i] / closes[i-1]) for i in range(1, len(closes)) if closes[i-1] > 0]
    recent = returns[-20:]
    vol = pstdev(recent) if len(recent) > 1 else 0.0
    momentum = closes[-1] / closes[-min(10, len(closes)-1)] - 1.0
    trend = closes[-1] / closes[-20] - 1.0
    annualized_vol = vol * sqrt(24.0 * 365.0)
    if annualized_vol > 0.90:
        name = "HIGH_VOLATILITY"
    elif abs(trend) > 0.03:
        name = "TREND"
    else:
        name = "RANGE"
    confidence = min(1.0, max(abs(trend) / 0.05, abs(momentum) / 0.05))
    return Regime(name, max(-1.0, min(1.0, trend / 0.05)), min(1.0, annualized_vol / 0.90), confidence, momentum)
