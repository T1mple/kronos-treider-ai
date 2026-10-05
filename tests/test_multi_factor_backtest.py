from dataclasses import dataclass
from app.research.multi_factor_backtest import MultiFactorBacktester

@dataclass
class Candle:
    close: float

def test_multifactor_backtester_reports_components():
    candles=[Candle(100+i) for i in range(60)]
    report=MultiFactorBacktester(horizons=(1,5)).run(
        "TEST", candles,
        {"kronos":lambda _: .8,"technical":lambda _: .6},
        lambda _: .7,
    )
    assert len(report.components)==2
    assert len(report.composite["horizons"])==2
