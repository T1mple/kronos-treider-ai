class CapitalAllocator:
    def __init__(self, max_total_exposure: float, max_position: float):
        self.max_total_exposure = max_total_exposure
        self.max_position = max_position
    def allocate(self, score: float, available: float, current_exposure: float = 0.0):
        if score == 0: return 0.0
        raw = available * min(1.0, abs(score)) * 0.10
        return min(self.max_position, max(0.0, self.max_total_exposure-current_exposure), raw)
