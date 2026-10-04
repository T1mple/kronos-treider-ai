from dataclasses import dataclass
from app.paper.virtual_engine import VirtualPaperEngine
from app.research.fusion import build_forecast
from app.risk import RiskEngine

@dataclass
class PaperDecision:
    symbol: str
    price: float
    score: float
    confidence: float
    action: str
    notional_usd: float
    reason: str

class PaperDecisionLoop:
    """Research/paper-only decision pipeline. No live execution."""
    def __init__(self, engine=None, risk=None, max_notional=50.0, min_score=0.35, min_confidence=0.45):
        self.engine=engine or VirtualPaperEngine()
        self.risk=risk or RiskEngine()
        self.max_notional=float(max_notional)
        self.min_score=float(min_score)
        self.min_confidence=float(min_confidence)
        self.decisions=[]

    def evaluate(self, symbol, price, candles, arbitrage=None):
        fusion=build_forecast(symbol,candles)
        score=float(fusion["score"])
        confidence=float(fusion["confidence"])
        action="HOLD"
        notional=0.0
        reason="ensemble threshold not met"

        if arbitrage is not None and not arbitrage.viable:
            reason="arbitrage net spread below cost threshold"
        elif score >= self.min_score and confidence >= self.min_confidence:
            action="BUY"
            notional=self.max_notional
            if symbol in self.engine.positions:
                action="HOLD"
                notional=0.0
                reason="position already open"
            else:
                approved=self.risk.check_order(symbol, notional, self.engine.cash, 0.0)
                if not approved:
                    action="HOLD"
                    notional=0.0
                    reason="risk limit rejected"
                else:
                    self.engine.open(symbol,"buy",notional,price)
                    reason="ensemble + confidence passed"
        decision=PaperDecision(symbol,float(price),score,confidence,action,notional,reason)
        self.decisions.append(decision)
        return decision, fusion

    def close_if_reversal(self, symbol, price, candles):
        if symbol not in self.engine.positions:
            return None
        fusion=build_forecast(symbol,candles)
        if fusion["score"] <= -self.min_score:
            return self.engine.close(symbol,price)
        return None
