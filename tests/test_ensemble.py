from app.ensemble import Forecast, combine

def test_ensemble_bounded():
    value=combine([Forecast('BTC-USDT',1.0,1.0)],1.0)
    assert -1 <= value <= 1
