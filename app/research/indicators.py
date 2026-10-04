from statistics import mean, pstdev

def returns(closes):
    closes=list(closes)
    return [(b/a)-1.0 for a,b in zip(closes,closes[1:]) if a]

def sma(closes, window):
    values=list(closes)
    if len(values)<window: return None
    return mean(values[-window:])

def zscore(closes, window=20):
    values=list(closes)[-window:]
    if len(values)<window: return None
    sd=pstdev(values)
    return 0.0 if sd==0 else (values[-1]-mean(values))/sd
