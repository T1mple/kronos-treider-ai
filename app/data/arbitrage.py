from dataclasses import dataclass

@dataclass
class ArbitrageOpportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    gross_spread_pct: float
    estimated_fees_pct: float
    estimated_slippage_pct: float
    safety_margin_pct: float
    net_spread_pct: float
    viable: bool

def _pct(value):
    return float(value) * 100.0

def find_opportunity(
    ticks,
    symbol="BTCUSDT",
    fee_by_exchange=None,
    slippage_pct=0.05,
    safety_margin_pct=0.03,
):
    """Research-only cross-exchange spread estimator. Never submits orders."""
    if len(ticks) < 2:
        return None
    buy = min(ticks, key=lambda x: x.price)
    sell = max(ticks, key=lambda x: x.price)
    if buy.price <= 0 or sell.price <= buy.price:
        return None

    fee_by_exchange = fee_by_exchange or {}
    buy_fee = float(fee_by_exchange.get(buy.exchange, 0.10))
    sell_fee = float(fee_by_exchange.get(sell.exchange, 0.10))
    gross = _pct(sell.price / buy.price - 1.0)
    fees = buy_fee + sell_fee
    net = gross - fees - float(slippage_pct) - float(safety_margin_pct)

    return ArbitrageOpportunity(
        symbol=symbol,
        buy_exchange=buy.exchange,
        sell_exchange=sell.exchange,
        buy_price=float(buy.price),
        sell_price=float(sell.price),
        gross_spread_pct=gross,
        estimated_fees_pct=fees,
        estimated_slippage_pct=float(slippage_pct),
        safety_margin_pct=float(safety_margin_pct),
        net_spread_pct=net,
        viable=net > 0.0,
    )
