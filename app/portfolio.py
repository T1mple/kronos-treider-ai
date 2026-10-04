class CapitalAllocator:
    def __init__(self, max_total_exposure: float):
        self.max_total_exposure = max_total_exposure
    def allocate(self, score: float, available: float):
        weight = min(1.0, max(0.0, abs(score)))
        return min(available, self.max_total_exposure * weight)
