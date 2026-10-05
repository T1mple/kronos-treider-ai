from dataclasses import dataclass

@dataclass
class Allocation:
    strategy: str
    weight: float
    notional_usd: float

class PortfolioAllocator:
    def __init__(self, total_capital=300.0, max_positions=8, max_position=50.0):
        self.total_capital=float(total_capital)
        self.max_positions=int(max_positions)
        self.max_position=float(max_position)

    def allocate(self, candidates, capital=None, current_exposure=0.0, open_positions=0):
        slots=max(0, self.max_positions-int(open_positions))
        budget=min(self.total_capital, float(capital) if capital is not None else self.total_capital)
        budget=max(0.0, budget-max(0.0, float(current_exposure)))
        valid=sorted([x for x in candidates if float(x.get("score",0))>0], key=lambda x:float(x["score"]), reverse=True)[:slots]
        if not valid or budget<=0: return []
        allocations={x["name"]:0.0 for x in valid}
        remaining=valid[:]
        left=budget
        while remaining and left>1e-9:
            total=sum(float(x["score"]) for x in remaining)
            if total<=0: break
            nxt=[]
            for x in remaining:
                room=max(0.0, self.max_position-allocations[x["name"]])
                amount=min(left*float(x["score"])/total, room)
                allocations[x["name"]]+=amount
                left-=amount
                if room-amount>1e-9: nxt.append(x)
            if len(nxt)==len(remaining): break
            remaining=nxt
        total_allocated=sum(allocations.values())
        if total_allocated<=0: return []
        return [Allocation(x["name"], allocations[x["name"]]/total_allocated, allocations[x["name"]]) for x in valid if allocations[x["name"]]>0]
