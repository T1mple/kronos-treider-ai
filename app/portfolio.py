class CapitalAllocator:
    """Conservative paper/backtest capital allocator."""

    def __init__(self, max_total_exposure: float, max_position: float = float("inf")):
        self.max_total_exposure = max(0.0, max_total_exposure)
        self.max_position = max(0.0, max_position)

    def allocate(self, score: float, available: float, current_exposure: float = 0.0) -> float:
        if available <= 0 or current_exposure >= self.max_total_exposure:
            return 0.0
        strength = min(1.0, max(0.0, abs(score)))
        desired = available * strength * 0.10
        room = self.max_total_exposure - max(0.0, current_exposure)
        return min(desired, self.max_position, room)
