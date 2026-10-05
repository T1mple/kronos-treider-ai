from dataclasses import dataclass, asdict
from app.research.backtest_factors import run_factor_backtest

@dataclass(frozen=True)
class ComponentReport:
    name: str
    horizons: list

@dataclass(frozen=True)
class MultiFactorBacktestReport:
    symbol: str
    components: list
    composite: dict

class MultiFactorBacktester:
    """Research-only comparison of factor families over future horizons."""
    def __init__(self, horizons=(1,5,20), min_score=.20):
        self.horizons=tuple(horizons); self.min_score=float(min_score)

    def run(self, symbol, candles, factor_functions, composite_function):
        components=[]
        for name,fn in factor_functions.items():
            result=run_factor_backtest(symbol,candles,fn,self.horizons,self.min_score)
            components.append(asdict(ComponentReport(name,result.horizons)))
        composite=run_factor_backtest(symbol,candles,composite_function,self.horizons,self.min_score)
        return MultiFactorBacktestReport(symbol,components,asdict(composite))
