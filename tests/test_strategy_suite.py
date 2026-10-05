from app.research.strategy_suite import directional_suite, grid, market_making, statistical_pair


def _candles(prices):
    return [{"open": p, "high": p * 1.002, "low": p * .998, "close": p, "volume": 1.0} for p in prices]


def test_directional_suite_has_multiple_models():
    signals = directional_suite(_candles([100 + i * .5 for i in range(100)]), "BTCUSDT")
    assert {x.strategy for x in signals} == {"momentum", "trend", "mean_reversion"}


def test_stat_arb_is_causal_shape():
    a = [100 + i * .2 for i in range(100)]
    b = [50 + i * .1 for i in range(100)]
    signal = statistical_pair(_candles(a), _candles(b), "BTCUSDT", "ETHUSDT")
    assert signal is not None
    assert -1.0 <= signal.score <= 1.0


def test_market_making_and_grid_are_research_only():
    candles = _candles([100 + (i % 8) * .1 for i in range(100)])
    assert market_making(candles, "BTCUSDT") is not None
    assert grid(candles, "BTCUSDT") is not None
