from dataclasses import dataclass, asdict
from datetime import datetime, timezone

@dataclass
class ForwardState:
    symbol: str
    last_timestamp: str = ""
    processed: int = 0
    skipped: int = 0

@dataclass
class ForwardObservation:
    symbol: str
    candle_timestamp: str
    price: float
    score: float
    confidence: float
    action: str
    created_at: str

class ForwardPaperMonitor:
    """Stateful forward-paper observation layer. Research only, no exchange orders."""

    def __init__(self):
        self.states = {}
        self.observations = []

    def accept(self, symbol, candle_timestamp):
        state = self.states.setdefault(symbol, ForwardState(symbol))
        stamp = str(candle_timestamp)
        if state.last_timestamp and stamp <= state.last_timestamp:
            state.skipped += 1
            return False
        state.last_timestamp = stamp
        state.processed += 1
        return True

    def observe(self, symbol, candle_timestamp, price, score, confidence, action="HOLD"):
        if not self.accept(symbol, candle_timestamp):
            return None
        item = ForwardObservation(
            symbol=symbol,
            candle_timestamp=str(candle_timestamp),
            price=float(price),
            score=float(score),
            confidence=float(confidence),
            action=str(action),
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.observations.append(item)
        return item

    def evaluate(self, current_price):
        price=float(current_price)
        if price <= 0: return []
        done=[]
        for item in self.observations:
            if item.evaluated or item.action not in {'BUY','SELL'}: continue
            outcome=(price/item.price-1.0)*100.0
            if item.action == 'SELL': outcome=-outcome
            item.outcome_pct=outcome; item.correct=outcome > 0.0; item.evaluated=True
            done.append(asdict(item))
        return done

    def performance_by_regime(self):
        groups={}
        for item in self.observations:
            regime=getattr(item, 'regime', None) or 'UNKNOWN'
            groups.setdefault(regime, []).append(item)
        result={}
        for regime, items in groups.items():
            outcomes=[float(x.outcome_pct) for x in items if x.evaluated and x.outcome_pct is not None]
            wins=[x for x in outcomes if x>0]
            result[regime]={'evaluated':len(outcomes),'wins':len(wins),'accuracy_pct':len(wins)/len(outcomes)*100 if outcomes else 0.0,'average_outcome_pct':sum(outcomes)/len(outcomes) if outcomes else 0.0}
        return result

    def performance(self):
        outcomes=[float(x.outcome_pct) for x in self.observations if x.evaluated and x.outcome_pct is not None]
        wins=[x for x in outcomes if x>0]
        return {'evaluated':len(outcomes),'wins':len(wins),'accuracy_pct':len(wins)/len(outcomes)*100 if outcomes else 0.0,'average_outcome_pct':sum(outcomes)/len(outcomes) if outcomes else 0.0,'total_outcome_pct':sum(outcomes)}

    def snapshot(self):
        return {
            "states": {k: asdict(v) for k, v in self.states.items()},
            "observations": [asdict(x) for x in self.observations[-100:]],
            "mode": "FORWARD_PAPER",
            "live_trading": False,
        }
