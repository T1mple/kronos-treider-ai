from app.backtest import Backtester

def test_backtester_empty_history():
    result=Backtester().run([], 300.0, 0.001, 0.0005, lambda _: 0.0)
    assert result.trades == 0
    assert result.total_return == 0.0
