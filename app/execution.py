from app.config import Settings
from app.risk import RiskEngine

class ExecutionEngine:
    def __init__(self, settings: Settings, risk: RiskEngine):
        self.settings, self.risk = settings, risk
    async def submit(self, venue, symbol, side, notional_usd, **kwargs):
        ok, reason = self.risk.approve_order(notional_usd)
        if not ok: return {"status":"rejected","reason":reason}
        if self.settings.trading_mode != "LIVE" or not self.settings.live_trading:
            return {"status":"paper","venue":venue,"symbol":symbol,"side":side,"notional_usd":notional_usd}
        raise NotImplementedError("Live execution adapters are not enabled yet")
