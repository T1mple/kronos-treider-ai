from dataclasses import dataclass

@dataclass
class AdvancedRiskState:
    paused: bool=False
    daily_pnl: float=0.0
    exposure: float=0.0
    open_positions: int=0
    peak_equity: float=0.0

class AdvancedRiskController:
    def __init__(self,max_position=50,max_exposure=200,max_daily_loss=10,max_positions=8,max_drawdown=.10):
        self.max_position=max_position; self.max_exposure=max_exposure; self.max_daily_loss=max_daily_loss
        self.max_positions=max_positions; self.max_drawdown=max_drawdown; self.state=AdvancedRiskState()

    def approve(self,notional,equity=None):
        s=self.state
        if s.paused: return False,"paused"
        if notional<=0: return False,"position_limit"
        if s.exposure+notional>self.max_exposure: return False,"exposure_limit"
        if notional>self.max_position: return False,"position_limit"
        if s.open_positions>=self.max_positions: return False,"position_count"
        if s.daily_pnl<=-self.max_daily_loss: return False,"daily_loss"
        if equity is not None:
            s.peak_equity=max(s.peak_equity,float(equity))
            if s.peak_equity and float(equity)<s.peak_equity*(1-self.max_drawdown):
                s.paused=True; return False,"drawdown_circuit_breaker"
        return True,"approved"

    def opened(self,notional): self.state.exposure+=notional; self.state.open_positions+=1
    def closed(self,notional,pnl):
        self.state.exposure=max(0,self.state.exposure-notional); self.state.open_positions=max(0,self.state.open_positions-1); self.state.daily_pnl+=pnl
    def pause(self): self.state.paused=True
    def resume(self): self.state.paused=False
