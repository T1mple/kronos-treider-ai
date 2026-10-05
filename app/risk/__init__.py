from dataclasses import dataclass

from app.config import Settings


@dataclass
class RiskSnapshot:
    daily_pnl: float = 0.0
    total_exposure: float = 0.0
    open_positions: int = 0
    paused: bool = False
    circuit_breaker: bool = False
    service_active: bool = False


class RiskEngine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.state = RiskSnapshot()

    def snapshot(self):
        return self.state.__dict__.copy()

    def start(self):
        if not self.state.circuit_breaker:
            self.state.service_active = True
            self.state.paused = False

    def pause(self):
        self.state.service_active = False
        self.state.paused = True

    def resume(self):
        if not self.state.circuit_breaker:
            self.state.service_active = True
            self.state.paused = False

    def emergency_stop(self):
        self.state.service_active = False
        self.state.paused = True
        self.state.circuit_breaker = True

    def approve_order(self, notional_usd: float):
        if self.state.paused or self.state.circuit_breaker:
            return False, "trading paused"
        if notional_usd <= 0:
            return False, "invalid notional"
        if self.state.open_positions >= self.settings.max_concurrent_positions:
            return False, "position count limit"
        if notional_usd > self.settings.max_position_usd:
            return False, "position size limit"
        if self.state.total_exposure + notional_usd > self.settings.max_total_exposure_usd:
            return False, "exposure limit"
        if self.state.daily_pnl <= -self.settings.max_daily_loss_usd:
            self.emergency_stop()
            return False, "daily loss limit"
        return True, "approved"

    def register_open(self, notional_usd: float):
        self.state.total_exposure += notional_usd
        self.state.open_positions += 1

    def register_close(self, notional_usd: float, pnl: float):
        self.state.total_exposure = max(0.0, self.state.total_exposure - notional_usd)
        self.state.open_positions = max(0, self.state.open_positions - 1)
        self.state.daily_pnl += pnl
        if self.state.daily_pnl <= -self.settings.max_daily_loss_usd:
            self.emergency_stop()


__all__ = ["RiskEngine", "RiskSnapshot"]
