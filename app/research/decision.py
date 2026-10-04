from dataclasses import dataclass, asdict
from app.research.adaptive import AdaptiveDecision
from app.research.risk_allocator import ResearchRiskAllocator, AllocationDecision

@dataclass
class ResearchDecision:
    adaptive: dict
    allocation: dict

class ResearchDecisionEngine:
    """Final research decision layer. No live execution."""
    def __init__(self,allocator=None): self.allocator=allocator or ResearchRiskAllocator()
    def evaluate(self,adaptive: AdaptiveDecision,available,current_exposure=0.0,open_positions=0,daily_pnl=0.0,volatility=0.0):
        allocation=self.allocator.allocate(adaptive.ensemble_score,adaptive.confidence,volatility,available,current_exposure,open_positions,daily_pnl)
        return ResearchDecision(asdict(adaptive),asdict(allocation))
