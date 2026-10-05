from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class FactorAttribution:
    factor: str
    weight: float
    score: float
    contribution: float


def attribute(components, weights=None):
    """Explain a composite score without changing or placing orders."""
    weights=weights or {k:1.0 for k in components}
    total=sum(float(v) for v in weights.values()) or 1.0
    rows=[]
    for name,score in components.items():
        w=float(weights.get(name,0.0))/total
        value=float(score)
        rows.append(FactorAttribution(name,w,value,w*value))
    return [asdict(x) for x in rows]


def leave_one_out_score(components, weights=None):
    weights=weights or {k:1.0 for k in components}
    out={}
    for removed in components:
        kept={k:v for k,v in components.items() if k!=removed}
        kept_weights={k:v for k,v in weights.items() if k!=removed}
        total=sum(float(v) for v in kept_weights.values()) or 1.0
        out[removed]=sum(float(kept[k])*float(kept_weights.get(k,0))/total for k in kept)
    return out
