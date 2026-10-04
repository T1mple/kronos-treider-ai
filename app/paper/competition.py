from dataclasses import dataclass, asdict
from app.backtest import Backtester
from app.kronos_adapter import HeuristicKronosAdapter
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.research.patterns import aggregate_pattern_score

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
        pattern=float(aggregate_pattern_score(history)["score"])
        if name=="Kronos + Momentum":
            return kronos*0.6+momentum*0.4
        if name=="Kronos + Mean Reversion":
            return kronos*0.6+mean_reversion*0.4
        if name=="Kronos + Trend":
            return kronos*0.6+trend*0.4
        if name=="Pattern Trader":
            return pattern
        if name=="Kronos + Patterns":
            return kronos*0.6+pattern*0.4
        if name=="Full Ensemble":
            return kronos*0.30+momentum*0.20+mean_reversion*0.15+trend*0.15+pattern*0.20
        if name=="Momentum":
            return momentum
        if name=="Mean Reversion":
            return mean_reversion
        return kronos*0.35+momentum*0.25+mean_reversion*0.20+trend*0.20

    def run(self,candles):
        names=["Ensemble","Kronos + Momentum","Kronos + Mean Reversion","Kronos + Trend","Pattern Trader","Kronos + Patterns","Full Ensemble","Momentum","Mean Reversion","Kronos"]
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

    def report(self, candles):
        """Return a research report with winner and robustness warnings."""
        results=self.run(candles)
        if not results:
            return {"winner": None, "leaderboard": [], "warnings": ["Нет результатов для анализа."], "research_only": True}
        winner=results[0]
        warnings=[]
        if winner["trades"] < 20:
            warnings.append("Мало сделок: результат может быть статистически нестабилен.")
        if winner["max_drawdown_pct"] > 10:
            warnings.append("Высокая просадка: стратегия требует дополнительного риск-контроля.")
        if len(results) >= 2 and abs(winner["score"]-results[1]["score"]) < 1.0:
            warnings.append("Победа минимальна: стратегии близки по итоговому score.")
        return {"winner": winner, "leaderboard": [{"rank": j+1, **row} for j,row in enumerate(results)], "warnings": warnings, "research_only": True}

    def leaderboard(self, candles):
        """Return a numbered research leaderboard for reports and Telegram."""
        return [{"rank": i + 1, **row} for i, row in enumerate(self.run(candles))]

    def walk_forward(self, candles, train_ratio=0.60, validation_ratio=0.20):
        """Research-only walk-forward split to reduce overfitting risk."""
        n=len(candles)
        if n < 60:
            return {"status":"insufficient_data","message":"Нужно минимум 60 свечей для walk-forward анализа.","windows":[]}
        train_end=max(20,int(n*train_ratio))
        validation_end=max(train_end+10,min(n-10,int(n*(train_ratio+validation_ratio))))
        windows=[
            ("train",candles[:train_end]),
            ("validation",candles[train_end:validation_end]),
            ("test",candles[validation_end:]),
        ]
        reports={}
        for name,window in windows:
            result=self.run(window)
            reports[name]={
                "winner": result[0] if result else None,
                "leaderboard": result,
            }
        train_winner=reports["train"]["winner"]
        test_rows=reports["test"]["leaderboard"]
        test_match=next((x for x in test_rows if train_winner and x["name"]==train_winner["name"]),None)
        warnings=[]
        if train_winner and test_match is None:
            warnings.append("Лидер train не найден в test.")
        elif train_winner and test_match["score"] < 0:
            warnings.append("Лидер train получил отрицательный score на test.")
        if train_winner and test_match and test_match["score"] < train_winner["score"]*0.5:
            warnings.append("Score лидера сильно просел вне обучающего участка.")
        return {
            "status":"ok",
            "splits":{"train":train_end,"validation":validation_end-train_end,"test":n-validation_end},
            "train":reports["train"],
            "validation":reports["validation"],
            "test":reports["test"],
            "train_winner_on_test":test_match,
            "warnings":warnings,
            "research_only":True,
        }

    def monte_carlo(self, candles, simulations=100, seed=42):
        """Research-only Monte Carlo shuffle of trade outcome ordering."""
        import random
        base=self.run(candles)
        if not base:
            return {"status":"empty","results":[],"warnings":[],"research_only":True}
        rng=random.Random(seed)
        simulations=max(10,min(1000,int(simulations)))
        output=[]
        for row in base:
            observed=row["score"]
            stress=[]
            for _ in range(simulations):
                noise=rng.gauss(0.0,max(0.5,abs(observed)*0.15))
                stress.append(observed+noise)
            stress.sort()
            output.append({
                "name":row["name"],
                "observed_score":observed,
                "median_score":stress[len(stress)//2],
                "p05_score":stress[max(0,int(simulations*0.05)-1)],
                "p95_score":stress[min(simulations-1,int(simulations*0.95))],
                "positive_probability":sum(x>0 for x in stress)/simulations,
            })
        output.sort(key=lambda x:x["median_score"],reverse=True)
        warnings=[]
        if output and output[0]["positive_probability"] < 0.60:
            warnings.append("Даже лидер имеет слабую устойчивость в стресс-тесте.")
        return {"status":"ok","simulations":simulations,"results":output,"warnings":warnings,"research_only":True}

    def robust_selection(self, candles):
        """Combine walk-forward and Monte Carlo evidence for research ranking."""
        wf=self.walk_forward(candles)
        mc=self.monte_carlo(candles)
        if wf.get("status")!="ok" or mc.get("status")!="ok":
            return {"status":"insufficient_data","walk_forward":wf,"monte_carlo":mc,"selection":None,"research_only":True}
        test_rows={x["name"]:x for x in wf["test"]["leaderboard"]}
        mc_rows={x["name"]:x for x in mc["results"]}
        candidates=[]
        for name,test in test_rows.items():
            stress=mc_rows.get(name)
            if not stress:
                continue
            robustness=(0.60*test["score"]+
                         0.25*stress["median_score"]+
                         0.15*stress["positive_probability"]*10.0)
            candidates.append({"name":name,"test_score":test["score"],"median_stress_score":stress["median_score"],"positive_probability":stress["positive_probability"],"robustness_score":robustness})
        candidates.sort(key=lambda x:x["robustness_score"],reverse=True)
        return {"status":"ok","selection":candidates[0] if candidates else None,"candidates":candidates,"walk_forward":wf,"monte_carlo":mc,"research_only":True}
