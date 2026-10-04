from app.research.regime import RegimeDetector

class RegimeStrategySelector:
    """Maps detected market regimes to research strategy preferences."""
    PREFERENCES={
        "TRENDING":["momentum","trend_filter"],
        "RANGING":["mean_reversion","stat_arb","grid"],
        "HIGH_VOLATILITY":["mean_reversion","arbitrage"],
        "UNKNOWN":["mean_reversion"],
    }
    def __init__(self,detector=None):
        self.detector=detector or RegimeDetector()
    def select(self,candles,available):
        regime=self.detector.detect(candles)
        preferred=self.PREFERENCES.get(regime.name,[])
        ordered=[x for x in preferred if x in available]
        ordered += [x for x in available if x not in ordered]
        return {"regime":regime,"ordered_strategies":ordered}
