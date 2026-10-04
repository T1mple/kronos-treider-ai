from types import SimpleNamespace
from app.data.arbitrage import find_opportunity

def test_find_cross_exchange_opportunity():
    ticks=[
        SimpleNamespace(exchange="a",symbol="BTCUSDT",price=100.0),
        SimpleNamespace(exchange="b",symbol="BTCUSDT",price=101.0),
    ]
    result=find_opportunity(ticks, fee_by_exchange={"a":0.10,"b":0.10})
    assert result.buy_exchange=="a"
    assert result.sell_exchange=="b"
    assert result.gross_spread_pct > 0
    assert result.net_spread_pct < result.gross_spread_pct

def test_unprofitable_after_costs():
    ticks=[
        SimpleNamespace(exchange="a",symbol="BTCUSDT",price=100.0),
        SimpleNamespace(exchange="b",symbol="100",price=100.1),
    ]
    result=find_opportunity(ticks, fee_by_exchange={"a":0.10,"100":0.10})
    assert result.viable is False
