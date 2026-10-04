from dataclasses import dataclass

@dataclass
class ArbitrageOpportunity:
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    gross_spread_pct: float

def find_opportunity(ticks, symbol="BTCUSDT"):
    if len(ticks)<2:
        return None
    buy=min(ticks,key=lambda x:x.price)
    sell=max(ticks,key=lambda x:x.price)
    spread=(sell.price/buy.price-1.0)*100.0
    if spread <= 0:
        return None
    return ArbitrageOpportunity(symbol,buy.exchange,sell.exchange,buy.price,sell.price,spread)
