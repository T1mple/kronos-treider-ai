from dataclasses import asdict, dataclass
from app.research.technical_factors import calculate as technical
from app.research.fundamentals import score_overview
from app.research.sentiment import score_news

@dataclass(frozen=True)
class MultiFactorScore:
    symbol: str
    technical: float
    fundamental: float
    sentiment: float
    kronos: float
    sector: float
    risk: float
    score: float
    confidence: float

class MultiFactorEngine:
    """Research-only factor fusion. It never creates exchange orders."""
    def evaluate(self, symbol, candles, kronos_score=0.0, fundamentals=None, news=None, sector_score=0.0, risk_score=0.0):
        tech=technical(candles).score
        fund=score_overview(fundamentals or {}).score
        sent=score_news(news or {}).score
        values=[tech,fund,sent,float(kronos_score),float(sector_score),float(risk_score)]
        score=max(-1.0,min(1.0,0.25*tech+0.20*fund+0.15*sent+0.25*float(kronos_score)+0.10*float(sector_score)+0.05*float(risk_score)))
        confidence=min(1.0,0.5+0.5*(sum(abs(x) for x in values)/len(values)))
        return MultiFactorScore(symbol,tech,fund,sent,float(kronos_score),float(sector_score),float(risk_score),score,confidence)

    @staticmethod
    def as_dict(result): return asdict(result)
