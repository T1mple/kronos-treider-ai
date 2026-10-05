from statistics import mean, pstdev


def _closes(candles):
    return [float(c.close if hasattr(c, "close") else c["close"]) for c in candles]


def _ema(values, period):
    values=list(values)
    if len(values)<period: return None
    alpha=2.0/(period+1.0)
    value=mean(values[:period])
    for x in values[period:]: value=alpha*x+(1-alpha)*value
    return value


def _rsi(closes, period=14):
    if len(closes)<period+1: return None
    changes=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    gains=[max(x,0.0) for x in changes[-period:]]
    losses=[max(-x,0.0) for x in changes[-period:]]
    avg_gain=mean(gains); avg_loss=mean(losses)
    if avg_loss==0: return 100.0 if avg_gain>0 else 50.0
    return 100.0-(100.0/(1.0+avg_gain/avg_loss))


def _zscore(values, window=20):
    values=list(values)[-window:]
    if len(values)<window: return None
    sd=pstdev(values)
    return 0.0 if sd==0 else (values[-1]-mean(values))/sd


def _clip(x): return max(-1.0,min(1.0,float(x)))


def indicator_snapshot(candles):
    closes=_closes(candles)
    if len(closes)<30: return {"ready":False}
    price=closes[-1]
    ema9=_ema(closes,9); ema21=_ema(closes,21)
    rsi=_rsi(closes,14)
    z=_zscore(closes,20)
    # Each indicator is a vote in [-1, +1]. Neutral conditions stay near zero.
    momentum=_clip((closes[-1]/closes[-4]-1.0)/0.015)
    trend=_clip(((ema9/ema21)-1.0)/0.008) if ema9 and ema21 else 0.0
    rsi_vote=_clip((rsi-50.0)/20.0) if rsi is not None else 0.0
    mean_reversion=_clip(-z/2.5) if z is not None else 0.0
    # A consensus score, not a hard gate on any single indicator.
    score=(momentum*0.25 + trend*0.30 + rsi_vote*0.20 + mean_reversion*0.25)
    agreement=sum(1 for v in (momentum,trend,rsi_vote,mean_reversion) if v>0.15) - sum(1 for v in (momentum,trend,rsi_vote,mean_reversion) if v<-0.15)
    return {"ready":True,"price":price,"momentum":momentum,"trend":trend,"rsi_vote":rsi_vote,"mean_reversion":mean_reversion,"rsi":rsi,"zscore":z,"score":_clip(score),"agreement":agreement}


def momentum_signal(candles):
    return indicator_snapshot(candles).get("momentum",0.0)


def mean_reversion_signal(candles):
    return indicator_snapshot(candles).get("mean_reversion",0.0)


def trend_filter_signal(candles):
    return indicator_snapshot(candles).get("trend",0.0)
