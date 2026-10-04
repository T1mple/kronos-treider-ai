from dataclasses import dataclass, asdict
from app.backtest import Backtester
from app.kronos_adapter import HeuristicKronosAdapter
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal

@dataclass
class RobotScore:
    name: str
    return_pct: float
    max_drawdown_pct: float
    trades: int
    fees: float
    score: float

class RobotCompetition:
    """Research-only competition under identical fees and slippage."""
    def __init__(self, starting_balance=300.0):
        self.starting_balance=starting_balance
        self.backtester=Backtester()

    def _signals(self, name, history):
        kronos=HeuristicKronosAdapter().predict("BTCUSDT",history).direction
        momentum=float(momentum_signal(history))
        mean_reversion=float(mean_reversion_signal(history))
        trend=float(trend_filter_signal(history))
        if name=="Kronos + Momentum":
            return kronos*0.6+momentum*0.4
        if name=="Kronos + Mean Reversion":
            return kronos*0.6+mean_reversion*0.4
        if name=="Kronos + Trend":
            return kronos*0.6+trend*0.4
        if name=="Momentum":
            return momentum
        if name=="Mean Reversion":
            return mean_reversion
        return kronos*0.35+momentum*0.25+mean_reversion*0.20+trend*0.20

    def run(self,candles):
        names=["Ensemble","Kronos + Momentum","Kronos + Mean Reversion","Kronos + Trend","Momentum","Mean Reversion","Kronos"]
        results=[]
        for name in names:
            def signal(history, candidate=name):
                if len(history)<10: return 0.0
                return max(-1.0,min(1.0,self._signals(candidate,history)))
            result=self.backtester.run(candles,self.starting_balance,0.001,0.0005,signal)
            score=result.total_return*100.0-result.max_drawdown*100.0
            results.append(RobotScore(name,result.total_return*100.0,result.max_drawdown*100.0,result.trades,result.fees_paid,score))
        return sorted([asdict(x) for x in results],key=lambda x:x["score"],reverse=True)

    def winner(self, candles):
        """Return the highest research score. This method never places orders."""
        results=self.run(candles)
        return results[0] if results else None

    def leaderboard(self, candles):
        """Return a numbered research leaderboard for reports and Telegram."""
        return [{"rank": i + 1, **row} for i, row in enumerate(self.run(candles))]
