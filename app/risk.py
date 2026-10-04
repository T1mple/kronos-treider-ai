from dataclasses import dataclass
from app.config import Settings

@dataclass
class RiskSnapshot:
    daily_pnl: float = 0.0
    total_exposure: float = 0.0
    open_positions: int = 0
    paused: bool = False
    circuit_breaker: bool = False

class RiskEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state = RiskSnapshot()
    def snapshot(self):
        return self.state.__dict__.copy()
    def pause(self): self.state.paused = True
    def resume(self): self.state.paused = False
    def emergency_stop(self):
        self.state.paused = True
        self.state.circuit_breaker = True
    def approve_order(self, notional_usd: float):
        if self.state.paused or self.state.circuit_breaker: return False, "trading paused"
        if self.state.open_positions >= self.settings.max_concurrent_positions: return False, "position count limit"
        if notional_usd > self.settings.max_position_usd: return False, "position size limit"
        if self.state.total_exposure + notional_usd > self.settings.max_total_exposure_usd: return False, "exposure limit"
        if self.state.daily_pnl <= -self.settings.max_daily_loss_usd:
            self.state.circuit_breaker = True
            return False, "daily loss limit"
        return True, "approved"
