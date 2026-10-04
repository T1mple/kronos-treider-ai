from app.modes import TradingMode

def test_modes_exist():
    assert TradingMode.BACKTEST.value == 'BACKTEST'
    assert TradingMode.LIVE.value == 'LIVE'
