from dataclasses import dataclass


@dataclass
class Allocation:
    strategy: str
    weight: float
    notional_usd: float


class PortfolioAllocator:
    def __init__(self, total_capital=300.0, max_positions=8, max_position=50.0):
        self.total_capital = float(total_capital)
        self.max_positions = int(max_positions)
        self.max_position = float(max_position)

    def allocate(self, candidates, capital=None, current_exposure=0.0, open_positions=0):
        """Allocate positive scores under portfolio, per-position and position-count caps."""
        slots = max(0, self.max_positions - int(open_positions))
        if slots == 0:
            return []
        budget = min(self.total_capital, float(capital) if capital is not None else self.total_capital)
        budget = max(0.0, budget - max(0.0, float(current_exposure)))
        valid = sorted(
            [x for x in candidates if float(x.get("score", 0.0)) > 0],
            key=lambda x: float(x["score"]),
            reverse=True,
        )[:slots]
        if not valid or budget <= 0:
            return []

        remaining = valid[:]
        allocations = {x["name"]: 0.0 for x in valid}
        remaining_budget = budget
        while remaining and remaining_budget > 1e-9:
            total_score = sum(float(x["score"]) for x in remaining)
            if total_score <= 0:
                break
            next_remaining = []
            for candidate in remaining:
                share = remaining_budget * float(candidate["score"]) / total_score
                room = max(0.0, self.max_position - allocations[candidate["name"]])
                amount = min(share, room)
                allocations[candidate["name"]] += amount
                remaining_budget -= amount
                if room - amount > 1e-9:
                    next_remaining.append(candidate)
            if len(next_remaining) == len(remaining):
                break
            remaining = next_remaining

        total_allocated = sum(allocations.values())
        if total_allocated <= 0:
            return []
        return [
            Allocation(
                candidate["name"],
                allocations[candidate["name"]] / total_allocated,
                allocations[candidate["name"]],
            )
            for candidate in valid
            if allocations[candidate["name"]] > 0
        ]
