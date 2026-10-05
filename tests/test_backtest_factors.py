from dataclasses import dataclass
from app.research.backtest_factors import run_factor_backtest

@dataclass
class Candle:
    close: float

def test_factor_backtest_detects_uptrend():
    candles=[Candle(100+i) for i in range(40)]
    result=run_factor_backtest("TEST",candles,lambda _: .8,horizons=(1,5),min_score=.2)
    assert result.total_observations > 0
    assert result.horizons[0]["hit_rate"] == 1.0
    assert result.horizons[1]["hit_rate"] == 1.0
