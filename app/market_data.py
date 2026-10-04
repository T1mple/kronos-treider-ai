from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class Quote:
    venue: str
    symbol: str
    bid: float
    ask: float
    timestamp: datetime

class MarketDataHub:
    def __init__(self):
        self.quotes: dict[tuple[str,str], Quote] = {}
        self.candles: dict[str, list[Candle]] = {}

    def update_quote(self, quote: Quote):
        self.quotes[(quote.venue, quote.symbol)] = quote

    def best_cross_exchange(self, symbol: str):
        quotes = [q for q in self.quotes.values() if q.symbol == symbol]
        if len(quotes) < 2:
            return None
        buy = min(quotes, key=lambda q: q.ask)
        sell = max(quotes, key=lambda q: q.bid)
        if sell.bid <= buy.ask:
            return None
        return {'buy': buy, 'sell': sell, 'gross_spread': sell.bid / buy.ask - 1}
