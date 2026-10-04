from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from app.kronos_adapter import HeuristicKronosAdapter
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.paper.portfolio import PaperPortfolio

@dataclass
class ForwardSnapshot:
    timestamp: str
    symbol: str
    price: float
    signal: float
    action: str
    cash: float
    equity: float
    realized_pnl: float
    trades: int

class ForwardPaperEngine:
    """Stateful forward paper engine. It processes one newly closed candle at a time."""
    def __init__(self, symbol="BTCUSDT", starting_cash=300.0):
        self.symbol=symbol
        self.portfolio=PaperPortfolio(starting_cash)
        self.kronos=HeuristicKronosAdapter()
        self.history=[]
        self.last_timestamp=None
        self.realized_pnl=0.0
        self.trades=0
        self.snapshots=[]

    def process(self, candles):
        if not candles:
            return None
        candle=candles[-1]
        timestamp=getattr(candle,"timestamp",None)
        if timestamp and self.last_timestamp == timestamp:
            return None
        self.history.append(candle)
        self.last_timestamp=timestamp
        price=float(candle.close)
        if len(self.history)<10:
            action="WAIT"
            signal=0.0
        else:
            momentum=float(momentum_signal(self.history))
            mean_reversion=float(mean_reversion_signal(self.history))
            trend=float(trend_filter_signal(self.history))
            prediction=self.kronos.predict(self.symbol,self.history)
            signal=max(-1.0,min(1.0,prediction.direction*0.35+momentum*0.25+mean_reversion*0.20+trend*0.20))
            action="HOLD"
            if signal>0.35 and self.symbol not in self.portfolio.positions:
                notional=min(30.0,self.portfolio.cash*0.10)
                if notional>0:
                    self.portfolio.open(self.symbol,"long",notional,price)
                    self.trades+=1
                    action="BUY"
            elif signal< -0.35 and self.symbol in self.portfolio.positions:
                result=self.portfolio.close(self.symbol,price)
                self.realized_pnl+=float(result["pnl"])
                self.trades+=1
                action="SELL"
        equity=self.portfolio.cash
        if self.symbol in self.portfolio.positions:
            equity+=self.portfolio.positions[self.symbol].quantity*price
        snapshot=ForwardSnapshot(datetime.now(timezone.utc).isoformat(),self.symbol,price,signal,action,self.portfolio.cash,equity,self.realized_pnl,self.trades)
        self.snapshots.append(snapshot)
        return snapshot

    def snapshot(self):
        if not self.snapshots:
            return {"status":"ОЖИДАНИЕ_ДАННЫХ"}
        return asdict(self.snapshots[-1])
