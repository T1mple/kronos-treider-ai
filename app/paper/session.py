from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class PaperSession:
    """Safe paper-session state. Never submits exchange orders."""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: bool = True
    ticks: int = 0
    signals: int = 0
    orders: int = 0
    realized_pnl: float = 0.0

    def tick(self): self.ticks += 1
    def record_signal(self): self.signals += 1
    def record_order(self, pnl=0.0):
        self.orders += 1
        self.realized_pnl += float(pnl)

    def snapshot(self):
        return {"started_at":self.started_at,"active":self.active,"ticks":self.ticks,
                "signals":self.signals,"orders":self.orders,
                "realized_pnl":self.realized_pnl,"mode":"PAPER","live_trading":False}
