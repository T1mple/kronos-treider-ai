from app.research.indicators import sma, zscore

def momentum_signal(candles):
    closes=[c.close for c in candles[-3:]]
    if len(closes)<3 or closes[0]<=0: return 0.0
    return max(-1.0,min(1.0,(closes[-1]/closes[0]-1)/0.02))

def mean_reversion_signal(candles):
    closes=[c.close for c in candles]
    z=zscore(closes,20)
    if z is None: return 0.0
    return max(-1.0,min(1.0,-z/3.0))

def trend_filter_signal(candles):
    closes=[c.close for c in candles]
    fast=sma(closes,5); slow=sma(closes,20)
    if fast is None or slow is None or slow==0: return 0.0
    return max(-1.0,min(1.0,(fast/slow-1)/0.01))
