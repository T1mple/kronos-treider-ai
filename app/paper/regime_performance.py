from collections import defaultdict
from app.paper.performance import PerformanceAnalyzer

class RegimePerformance:
    def __init__(self): self.analyzer=PerformanceAnalyzer()
    def analyze(self,records):
        groups=defaultdict(list)
        for record in records:
            regime=record.get("regime")
            pnl=record.get("outcome_pnl")
            if regime and pnl is not None: groups[regime].append(pnl)
        return {regime:self.analyzer.analyze(pnls) for regime,pnls in groups.items()}
