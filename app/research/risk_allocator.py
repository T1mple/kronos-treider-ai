from dataclasses import dataclass, asdict

@dataclass
class AllocationDecision:
    approved: bool
    notional_usd: float
    reason: str
    risk_multiplier: float

class ResearchRiskAllocator:
    """Research/paper capital allocator. Never submits exchange orders."""
    def __init__(self,max_position=50.0,max_exposure=200.0,max_daily_loss=10.0,max_positions=8):
        self.max_position=max(0.0,max_position); self.max_exposure=max(0.0,max_exposure)
        self.max_daily_loss=max(0.0,max_daily_loss); self.max_positions=max(0,max_positions)

    def allocate(self,score,confidence,volatility,available,current_exposure=0.0,open_positions=0,daily_pnl=0.0):
        if daily_pnl <= -self.max_daily_loss: return AllocationDecision(False,0.0,"daily loss limit",0.0)
        if open_positions >= self.max_positions: return AllocationDecision(False,0.0,"position count limit",0.0)
        room=max(0.0,self.max_exposure-current_exposure)
        if room<=0 or available<=0: return AllocationDecision(False,0.0,"exposure limit",0.0)
        conviction=min(1.0,max(0.0,abs(score)))*min(1.0,max(0.0,confidence))
        volatility_penalty=1.0/(1.0+max(0.0,volatility)*25.0)
        multiplier=conviction*volatility_penalty
        notional=min(self.max_position,room,available*0.10*multiplier)
        if notional<=0: return AllocationDecision(False,0.0,"insufficient conviction",multiplier)
        return AllocationDecision(True,notional,"approved for research/paper",multiplier)

    @staticmethod
    def as_dict(decision): return asdict(decision)
