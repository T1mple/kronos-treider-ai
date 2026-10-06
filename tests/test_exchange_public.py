from app.data.exchange_public import ExchangeQuote, best_cross_exchange


def test_best_cross_exchange_finds_positive_net_edge():
    quotes = [
        ExchangeQuote("buy", "BTCUSDT", 100.0, 100.1),
        ExchangeQuote("sell", "BTCUSDT", 101.0, 101.1),
    ]
    opportunity = best_cross_exchange(quotes, fee_rate=0.001, slippage_rate=0.0005)
    assert opportunity is not None
    assert opportunity.buy_venue == "buy"
    assert opportunity.sell_venue == "sell"
    assert opportunity.gross_edge > 0
    assert opportunity.net_edge > 0


def test_cross_exchange_edge_can_be_erased_by_costs():
    quotes = [
        ExchangeQuote("a", "BTCUSDT", 100.0, 100.0),
        ExchangeQuote("b", "BTCUSDT", 100.1, 100.1),
    ]
    opportunity = best_cross_exchange(quotes, fee_rate=0.001, slippage_rate=0.001)
    assert opportunity is not None
    assert opportunity.net_edge < 0


def test_cross_exchange_requires_two_venues():
    assert best_cross_exchange([ExchangeQuote("only", "BTCUSDT", 100.0, 100.1)]) is None

# MVP CI coverage: exchange edge calculations remain research-only.
