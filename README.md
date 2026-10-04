# kronos-treider-ai
## Research Lab

The repository includes a simulation-only Strategy Lab for comparing research signals with fees and slippage.

Workflow:
1. Load historical OHLCV with the data loaders.
2. Run the research lab.
3. Compare return, max drawdown, trade count and fees.
4. Promote only strategies that survive out-of-sample validation into paper trading.

Kronos is treated as a forecast input, not as an autonomous order generator. Paper execution is isolated from exchange execution.
