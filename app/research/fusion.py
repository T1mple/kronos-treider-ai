from app.ensemble import Forecast, combine
from app.research.patterns import aggregate_pattern_score
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal
from app.kronos_adapter import HeuristicKronosAdapter

def build_forecast(symbol, candles, kronos=None):
    """Research-only signal fusion. Kronos is a forecast input, never an order."""
    model=kronos or HeuristicKronosAdapter()
    kp=model.predict(symbol,candles)
    pattern=aggregate_pattern_score(candles)
    forecasts=[
        Forecast(symbol,kp.direction,kp.confidence),
        Forecast(symbol,pattern["score"],pattern["confidence"]),
    ]
    strategy=(0.35*momentum_signal(candles)+0.35*mean_reversion_signal(candles)+0.30*trend_filter_signal(candles))
    score=combine(forecasts,strategy)
    confidence=min(1.0,(kp.confidence+pattern["confidence"])/2)
    return {
        "symbol":symbol,
        "score":score,
        "confidence":confidence,
        "kronos":{"direction":kp.direction,"confidence":kp.confidence},
        "pattern":pattern,
        "strategy_score":strategy,
        "mode":"RESEARCH",
    }
