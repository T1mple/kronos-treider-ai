from dataclasses import dataclass,asdict
from datetime import datetime,timezone

@dataclass
class DecisionRecord:
    timestamp: str
    symbol: str
    regime: str
    ensemble_score: float
    confidence: float
    approved: bool
    notional_usd: float
    reason: str
    price: float | None = None
    outcome_pnl: float | None = None

class DecisionJournal:
    """In-memory research journal. No exchange connectivity."""
    def __init__(self): self.records=[]
    def record(self,symbol,decision,price=None):
        adaptive=decision.adaptive; allocation=decision.allocation
        item=DecisionRecord(datetime.now(timezone.utc).isoformat(),symbol,adaptive["regime"],adaptive["ensemble_score"],adaptive["confidence"],allocation["approved"],allocation["notional_usd"],allocation["reason"],price)
        self.records.append(item); return item
    def close(self,index,pnl):
        self.records[index].outcome_pnl=float(pnl); return self.records[index]
    def recent(self,limit=20): return [asdict(x) for x in self.records[-limit:]]
