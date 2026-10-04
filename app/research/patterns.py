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

def aggregate_pattern_score(candles):
    signals=detect_patterns(candles)
    if not signals:
        return {"score":0.0,"confidence":0.0,"patterns":[]}
    total=sum(x["confidence"] for x in signals)
    score=max(-1.0,min(1.0,sum(x["direction"]*x["confidence"] for x in signals)/total))
    return {"score":score,"confidence":total/len(signals),"patterns":signals}
