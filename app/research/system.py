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
    """Single research/PAPER orchestration boundary. Never submits live orders."""

    def __init__(self):
        self.kronos = HeuristicKronosAdapter()
        self.adaptive = AdaptiveStrategyEngine()
        self.decision = ResearchDecisionEngine()
        self.allocator = PortfolioAllocator(
            settings.max_total_exposure_usd,
            settings.max_concurrent_positions,
        )
        self.forward = ForwardPaperMonitor()
        self.risk = AdvancedRiskController(
            settings.max_position_usd,
            settings.max_total_exposure_usd,
            settings.max_daily_loss_usd,
            settings.max_concurrent_positions,
        )

    def _analyze(self, symbol, candles):
        prediction = self.kronos.predict(symbol, candles)
        regime = detect_regime(candles)
        signals = {
            "momentum": float(momentum_signal(candles)),
            "mean_reversion": float(mean_reversion_signal(candles)),
            "trend_filter": float(trend_filter_signal(candles)),
        }
        adaptive = self.adaptive.evaluate(
            candles,
            symbol,
            prediction.direction,
            prediction.confidence,
            signals,
        )
        return prediction, regime, signals, adaptive

    def evaluate_portfolio(self, candles_by_symbol, available=300.0):
        """Evaluate all symbols first, then allocate capital across the portfolio."""
        analyses = {}
        candidates = []
        for symbol, candles in candles_by_symbol.items():
            if not candles:
                continue
            prediction, regime, signals, adaptive = self._analyze(symbol, candles)
            analyses[symbol] = (prediction, regime, signals, adaptive)
            if adaptive.ensemble_score > 0:
                candidates.append({
                    "name": symbol,
                    "score": max(0.0, adaptive.ensemble_score) * max(0.0, adaptive.confidence),
                })

        allocations = self.allocator.allocate(candidates, capital=available, current_exposure=self.risk.state.exposure, open_positions=self.risk.state.open_positions)
        allocation_map = {item.strategy: item for item in allocations}
        results = {}

        for symbol, (prediction, regime, signals, adaptive) in analyses.items():
            allocation = allocation_map.get(symbol)
            notional = float(allocation.notional_usd) if allocation else 0.0

            # Risk is the final gate. Exits are handled by PAPER independently.
            approved, risk_reason = self.risk.approve(notional, equity=available)
            action = "HOLD"
            if adaptive.ensemble_score >= 0.35 and adaptive.confidence >= 0.45:
                action = "BUY" if approved else "HOLD"
            elif adaptive.ensemble_score <= -0.35 and adaptive.confidence >= 0.45:
                action = "SELL"

            price = float(candles_by_symbol[symbol][-1].close)
            timestamp = getattr(candles_by_symbol[symbol][-1], "timestamp", "")
            forward_evaluated = self.forward.evaluate(symbol, price)
            self.forward.observe(
                symbol,
                timestamp,
                price,
                adaptive.ensemble_score,
                adaptive.confidence,
                action,
                strategy="ensemble",
                regime=regime.name,
            )

            results[symbol] = {
                "symbol": symbol,
                "regime": asdict(regime),
                "signals": signals,
                "kronos": asdict(prediction),
                "adaptive": asdict(adaptive),
                "portfolio_allocation": asdict(allocation) if allocation else None,
                "risk_gate": {"approved": approved, "reason": risk_reason},
                "forward_evaluated": forward_evaluated,
                "action": action,
                "mode": "RESEARCH_PAPER",
            }

        return {
            "results": results,
            "allocations": [asdict(x) for x in allocations],
            "forward_performance": self.forward.performance(),
            "mode": "RESEARCH_PAPER",
        }

    def evaluate(self, symbol, candles, available=300.0):
        portfolio = self.evaluate_portfolio({symbol: candles}, available)
        return portfolio["results"].get(symbol, {
            "symbol": symbol,
            "action": "HOLD",
            "mode": "RESEARCH_PAPER",
        })
