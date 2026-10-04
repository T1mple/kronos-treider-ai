from dataclasses import dataclass, asdict

@dataclass
class PatternSignal:
    name: str
    direction: float
    confidence: float

def _ohlc(c):
    return (float(c.open), float(c.high), float(c.low), float(c.close))

def detect_patterns(candles):
    """Research-only deterministic candle-pattern detector."""
    if len(candles) < 3:
        return []
    rows=[_ohlc(c) for c in candles[-5:]]
    o,h,l,c=rows[-1]
    po,ph,pl,pc=rows[-2]
    _,_,_,ppc=rows[-3]
    body=abs(c-o)
    rng=max(h-l,1e-12)
    upper=h-max(o,c)
    lower=min(o,c)-l
    signals=[]

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

    return [asdict(x) for x in signals]

def aggregate_pattern_score(candles):
    signals=detect_patterns(candles)
    if not signals:
        return {"score":0.0,"confidence":0.0,"patterns":[]}
    total=sum(x["confidence"] for x in signals)
    score=max(-1.0,min(1.0,sum(x["direction"]*x["confidence"] for x in signals)/total))
    return {"score":score,"confidence":total/len(signals),"patterns":signals}
