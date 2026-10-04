from types import SimpleNamespace
from app.data.arbitrage import find_opportunity

def test_find_cross_exchange_opportunity():
    ticks=[
        SimpleNamespace(exchange="a",symbol="BTCUSDT",price=100.0),
        SimpleNamespace(exchange="b",symbol="BTCUSDT",price=101.0),
    ]
    result=find_opportunity(ticks)
    assert result.buy_exchange=="a"
    assert result.sell_exchange=="b"
    assert result.gross_spread_pct > 0
