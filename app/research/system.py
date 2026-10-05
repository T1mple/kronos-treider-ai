from dataclasses import asdict
from app.config import settings
from app.research.adaptive import AdaptiveStrategyEngine
from app.research.decision import ResearchDecisionEngine
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.kronos_adapter import HeuristicKronosAdapter
from app.research.regime import detect_regime
from app.portfolio.allocator import PortfolioAllocator
from app.risk.advanced import AdvancedRiskController
from app.paper.forward import ForwardPaperMonitor

class ResearchSystem:
    """Single research/paper orchestration boundary. Never submits live orders."""
    def __init__(self):
        self.kronos=HeuristicKronosAdapter()
        self.adaptive=AdaptiveStrategyEngine()
        self.decision=ResearchDecisionEngine()
        self.allocator=PortfolioAllocator(settings.max_total_exposure_usd, settings.max_concurrent_positions)
        self.forward=ForwardPaperMonitor()
        self.risk=AdvancedRiskController(
            settings.max_position_usd, settings.max_total_exposure_usd,
            settings.max_daily_loss_usd, settings.max_concurrent_positions
        )

    def evaluate(self, symbol, candles, available=300.0):
        prediction=self.kronos.predict(symbol,candles)
        regime=detect_regime(candles)
        regime_name=regime.name
        adaptive_weights=self.forward.adaptive_weights(regime_name, min_samples=5)
        signals={
            "momentum":float(momentum_signal(candles)),
            "mean_reversion":float(mean_reversion_signal(candles)),
            "trend_filter":float(trend_filter_signal(candles)),
        }
        adaptive=self.adaptive.evaluate(candles,symbol,prediction.direction,prediction.confidence,signals)
        decision=self.decision.evaluate(
            adaptive,available=available,
            current_exposure=self.risk.state.exposure,
            open_positions=self.risk.state.open_positions,
            daily_pnl=self.risk.state.daily_pnl,
            volatility=regime.volatility
        )
        allocation=self.allocator.allocate([{"name":symbol,"score":max(0.0,adaptive.ensemble_score)}])
        approved,reason=self.risk.approve(decision.allocation["notional_usd"])
        action="BUY" if adaptive.ensemble_score >= 0.35 and adaptive.confidence >= 0.45 else ("SELL" if adaptive.ensemble_score <= -0.35 and adaptive.confidence >= 0.45 else "HOLD")
        price=float(candles[-1].close) if candles else 0.0
        evaluated=self.forward.evaluate(price)
        timestamp=getattr(candles[-1], "timestamp", "") if candles else ""
        self.forward.observe(symbol, timestamp, price, adaptive.ensemble_score, adaptive.confidence, action, strategy="ensemble", regime=regime.name)
        return {
            "symbol":symbol,
            "regime":asdict(regime),
            "signals":signals,
            "kronos":asdict(prediction),
            "adaptive":asdict(adaptive),
            "decision":asdict(decision),
            "portfolio_candidates":[asdict(x) for x in allocation],
            "risk_gate":{"approved":approved,"reason":reason},
            "adaptive_weights":adaptive_weights,
            "forward_evaluated":evaluated,
            "forward_performance":self.forward.performance(),
            "mode":"RESEARCH_PAPER",
        }
