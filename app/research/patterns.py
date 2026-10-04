from dataclasses import dataclass, asdict

@dataclass
class PatternSignal:
    name: str
    direction: float
    confidence: float

def _ohlc(c):
    return (float(c.open), float(c.high), float(c.low), float(c.close), float(c.volume))

def detect_patterns(candles):
    """Research-only deterministic candle-pattern detector."""
    if len(candles) < 3:
        return []
    rows=[_ohlc(c) for c in candles[-5:]]
    o,h,l,c,v=rows[-1]
    po,ph,pl,pc,pv=rows[-2]
    _,_,_,ppc,_=rows[-3]
    body=abs(c-o)
    rng=max(h-l,1e-12)
    upper=h-max(o,c)
    lower=min(o,c)-l
    signals=[]
    avg_volume=sum(row[4] for row in rows[:-1])/max(1,len(rows)-1)
    volume_ratio=v/avg_volume if avg_volume>0 else 1.0

    if body/rng <= 0.10:
        signals.append(PatternSignal("Doji",0.0,0.55))
    if lower >= body*2 and upper <= max(body,rng*0.15) and c > o:
        signals.append(PatternSignal("Hammer",0.70,0.68))
    if upper >= body*2 and lower <= max(body,rng*0.15) and c < o:
        signals.append(PatternSignal("Shooting Star",-0.70,0.68))

    prev_body=abs(pc-po)
    if c > o and pc < po and o <= pc and c >= po and body > prev_body:
        signals.append(PatternSignal("Bullish Engulfing",0.82,0.76))
    if c < o and pc > po and o >= pc and c <= po and body > prev_body:
        signals.append(PatternSignal("Bearish Engulfing",-0.82,0.76))

    if h < ph and l > pl:
        direction=1.0 if c >= (o+ph+pl+pc)/4 else -1.0
        signals.append(PatternSignal("Inside Bar",direction,0.58))

    if c > pc > ppc and o >= po:
        signals.append(PatternSignal("Three Bar Bullish Momentum",0.62,0.60))
    if c < pc < ppc and o <= po:
        signals.append(PatternSignal("Three Bar Bearish Momentum",-0.62,0.60))

    enriched=[]
    for signal in signals:
        confirmation=min(1.0,max(0.0,volume_ratio/1.5))
        if signal["name"] in {"Bullish Engulfing","Hammer","Three Bar Bullish Momentum"}:
            signal["volume_confirmation"]=confirmation
            signal["confidence"]=min(1.0,signal["confidence"]*(0.65+0.35*confirmation))
        elif signal["name"] in {"Bearish Engulfing","Shooting Star","Three Bar Bearish Momentum"}:
            signal["volume_confirmation"]=confirmation
            signal["confidence"]=min(1.0,signal["confidence"]*(0.65+0.35*confirmation))
        else:
            signal["volume_confirmation"]=confirmation
        enriched.append(signal)
    return enriched

def _rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50.0
    changes=[closes[i]-closes[i-1] for i in range(1,len(closes))]
    recent=changes[-period:]
    gains=sum(max(x,0.0) for x in recent)/period
    losses=sum(max(-x,0.0) for x in recent)/period
    if losses == 0:
        return 100.0 if gains > 0 else 50.0
    rs=gains/losses
    return 100.0-(100.0/(1.0+rs))

def rsi_signal(candles):
    """Research-only RSI context, no trading instruction."""
    closes=[float(c.close) for c in candles]
    value=_rsi(closes)
    if value <= 30:
        return {"rsi":value,"score":0.65,"state":"OVERSOLD"}
    if value >= 70:
        return {"rsi":value,"score":-0.65,"state":"OVERBOUGHT"}
    return {"rsi":value,"score":0.0,"state":"NEUTRAL"}

def rsi_divergence(candles, lookback=5):
    """Simple deterministic swing divergence heuristic for research."""
    if len(candles) < lookback*2+2:
        return {"score":0.0,"type":"NONE"}
    closes=[float(c.close) for c in candles]
    rsi_values=[]
    for i in range(len(closes)):
        rsi_values.append(_rsi(closes[:i+1]))
    a=slice(-lookback*2,-lookback)
    b=slice(-lookback,None)
    pa=sum(closes[a])/lookback
    pb=sum(closes[b])/lookback
    ra=sum(rsi_values[a])/lookback
    rb=sum(rsi_values[b])/lookback
    if pb < pa and rb > ra:
        return {"score":0.70,"type":"BULLISH_DIVERGENCE","rsi_delta":rb-ra}
    if pb > pa and rb < ra:
        return {"score":-0.70,"type":"BEARISH_DIVERGENCE","rsi_delta":rb-ra}
    return {"score":0.0,"type":"NONE","rsi_delta":rb-ra}

def aggregate_pattern_score(candles):
    signals=detect_patterns(candles)
    total=sum(x["confidence"] for x in signals)
    candle_score=(sum(x["direction"]*x["confidence"] for x in signals)/total) if total else 0.0
    rsi=rsi_signal(candles)
    divergence=rsi_divergence(candles)
    score=max(-1.0,min(1.0,candle_score*0.60+rsi["score"]*0.15+divergence["score"]*0.25))
    confidence=min(1.0,(total/len(signals) if signals else 0.0)*0.60+(1.0 if divergence["type"]!="NONE" else 0.35)*0.25+0.15)
    return {"score":score,"confidence":confidence,"patterns":signals,"rsi":rsi,"divergence":divergence}
