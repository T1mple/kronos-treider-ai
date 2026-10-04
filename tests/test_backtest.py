from datetime import datetime, timedelta
from app.backtest import Backtester
from app.market_data import Candle

def test_backtest_has_costs_and_result():
    candles = [Candle(datetime(2026, 1, 1) + timedelta(days=i), 100+i, 101+i, 99+i, 100+i, 1000) for i in range(8)]
    result = Backtester().run(candles, signal_fn=lambda c: 1.0 if c.close < 106 else 0.0)
    assert result.trades >= 2
    assert result.fees_paid > 0
    assert result.ending_balance > 0
    assert 0 <= result.max_drawdown <= 1
