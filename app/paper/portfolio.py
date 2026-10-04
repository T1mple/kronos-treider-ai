from dataclasses import dataclass,asdict

@dataclass
class VirtualPosition:
    symbol: str
    side: str
    notional_usd: float
    entry_price: float
    quantity: float

class PaperPortfolio:
    """Virtual portfolio wrapper for research decisions."""
    def __init__(self,cash=300.0): self.cash=float(cash); self.positions={}
    def open(self,symbol,side,notional,price):
        if notional<=0 or price<=0: raise ValueError("notional and price must be positive")
        if notional>self.cash: raise ValueError("insufficient virtual cash")
        if symbol in self.positions: raise ValueError("position already exists")
        qty=notional/price
        self.cash-=notional
        self.positions[symbol]=VirtualPosition(symbol,side,notional,price,qty)
        return self.positions[symbol]
    def close(self,symbol,price):
        pos=self.positions.pop(symbol)
        pnl=(price-pos.entry_price)*pos.quantity if pos.side=="long" else (pos.entry_price-price)*pos.quantity
        self.cash+=pos.notional_usd+pnl
        return {"symbol":symbol,"pnl":pnl,"cash":self.cash}
    def snapshot(self): return {"cash":self.cash,"positions":[asdict(x) for x in self.positions.values()]}
