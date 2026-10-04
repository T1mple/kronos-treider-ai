from app.research.strategy_lab import StrategyLab
from app.research.signals import momentum_signal, mean_reversion_signal, trend_filter_signal

def run_lab(candles, starting_balance=300.0):
    strategies={
        "momentum": momentum_signal,
        "mean_reversion": mean_reversion_signal,
        "trend_filter": trend_filter_signal,
    }
    return StrategyLab().run(candles, strategies, starting_balance)
