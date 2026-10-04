from dataclasses import dataclass

@dataclass
class Allocation:
    strategy: str
    weight: float
    notional_usd: float

class PortfolioAllocator:
    def __init__(self,total_capital=300.0,max_positions=8):
        self.total_capital=float(total_capital); self.max_positions=int(max_positions)

    def allocate(self,candidates):
        valid=sorted([x for x in candidates if float(x.get("score",0))>0],key=lambda x:float(x["score"]),reverse=True)[:self.max_positions]
        total=sum(float(x["score"]) for x in valid)
        if not total: return []
        return [Allocation(x["name"],float(x["score"])/total,self.total_capital*float(x["score"])/total) for x in valid]
