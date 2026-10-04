from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import threading

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
    """Постоянный журнал бумажных решений в JSONL. Не подключается к биржам."""
    def __init__(self, path="/data/decision_journal.jsonl"):
        self.path=Path(path)
        self.records=[]
        self._lock=threading.Lock()
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                for line in self.path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        self.records.append(DecisionRecord(**json.loads(line)))
        except (OSError, ValueError, TypeError):
            self.records=[]

    def _persist(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload="".join(json.dumps(asdict(x),ensure_ascii=False)+"\n" for x in self.records)
        self.path.write_text(payload,encoding="utf-8")

    def record(self,symbol,decision,price=None):
        adaptive=decision.adaptive
        allocation=decision.allocation
        item=DecisionRecord(
            datetime.now(timezone.utc).isoformat(),symbol,adaptive["regime"],
            adaptive["ensemble_score"],adaptive["confidence"],
            allocation["approved"],allocation["notional_usd"],allocation["reason"],price
        )
        with self._lock:
            self.records.append(item)
            self._persist()
        return item

    def close(self,index,pnl):
        with self._lock:
            self.records[index].outcome_pnl=float(pnl)
            self._persist()
            return self.records[index]

    def recent(self,limit=20):
        with self._lock:
            return [asdict(x) for x in self.records[-limit:]]

    def all(self):
        with self._lock:
            return [asdict(x) for x in self.records]
