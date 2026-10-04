from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class VirtualPosition:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    entry_time: str

@dataclass
class VirtualTrade:
    symbol: str
    side: str
    quantity: float
    entry_price: float
    exit_price: float
    pnl: float
    fee: float
    opened_at: str
    closed_at: str

class VirtualPaperEngine:
    """Simulation-only engine. It never submits exchange orders."""
    def __init__(self, starting_cash=300.0, fee_rate=0.001, slippage_rate=0.0005):
        self.cash=float(starting_cash)
        self.starting_cash=float(starting_cash)
        self.fee_rate=float(fee_rate)
        self.slippage_rate=float(slippage_rate)
        self.positions={}
        self.trades=[]

    def _now(self):
        return datetime.now(timezone.utc).isoformat()

    def open(self, symbol, side, notional_usd, price):
        if symbol in self.positions or notional_usd <= 0 or price <= 0:
            return None
        qty=float(notional_usd)/float(price)
        fill=price*(1+self.slippage_rate if side=="buy" else 1-self.slippage_rate)
        fee=notional_usd*self.fee_rate
        if self.cash < notional_usd+fee:
            return None
        self.cash -= notional_usd+fee
        self.positions[symbol]=VirtualPosition(symbol,side,qty,fill,self._now())
        return self.positions[symbol]

    def close(self, symbol, price):
        pos=self.positions.pop(symbol,None)
        if not pos or price <= 0:
            return None
        exit_price=price*(1-self.slippage_rate if pos.side=="buy" else 1+self.slippage_rate)
        gross=(exit_price-pos.entry_price)*pos.quantity
        if pos.side=="sell":
            gross=-gross
        notional=abs(exit_price*pos.quantity)
        fee=notional*self.fee_rate
        pnl=gross-fee
        self.cash += notional + gross - fee
        trade=VirtualTrade(pos.symbol,pos.side,pos.quantity,pos.entry_price,exit_price,pnl,fee,pos.entry_time,self._now())
        self.trades.append(trade)
        return trade

    def mark_equity(self, prices):
        equity=self.cash
        for symbol,pos in self.positions.items():
            price=float(prices.get(symbol,pos.entry_price))
            gross=(price-pos.entry_price)*pos.quantity
            if pos.side=="sell":
                gross=-gross
            equity += abs(pos.entry_price*pos.quantity)+gross
        return equity

    def metrics(self, prices=None):
        prices=prices or {}
        equity=self.mark_equity(prices)
        pnls=[t.pnl for t in self.trades]
        wins=[x for x in pnls if x>0]
        losses=[x for x in pnls if x<0]
        return {
            "starting_cash":self.starting_cash,
            "cash":self.cash,
            "equity":equity,
            "trades":len(pnls),
            "wins":len(wins),
            "losses":len(losses),
            "win_rate":(len(wins)/len(pnls)*100) if pnls else 0.0,
            "total_pnl":sum(pnls),
            "average_pnl":(sum(pnls)/len(pnls)) if pnls else 0.0,
            "profit_factor":(sum(wins)/abs(sum(losses))) if losses else None,
            "open_positions":len(self.positions),
        }
