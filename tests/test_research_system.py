from app.market_data import Candle
from datetime import datetime, timezone

from app.research.system import ResearchSystem


def _candles(prices):
    return [
        Candle(
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            p,
            p * 1.002,
            p * 0.998,
            p,
            1.0,
        )
        for p in prices
    ]


def test_research_system_evaluates_all_symbols_and_allocates_portfolio():
    system = ResearchSystem()
    candles = _candles([100 + i * 0.5 for i in range(100)])
    result = system.evaluate_portfolio(
        {"BTCUSDT": candles, "ETHUSDT": candles},
        available=300.0,
    )
    assert set(result["results"]) == {"BTCUSDT", "ETHUSDT"}
    assert sum(x["notional_usd"] for x in result["allocations"]) <= 200.000001
    assert all("risk_gate" in item for item in result["results"].values())


def test_research_system_risk_gate_can_block_new_entry():
    system = ResearchSystem()
    system.risk.state.exposure = 200.0
    candles = _candles([100 + i * 0.5 for i in range(100)])
    result = system.evaluate_portfolio({"BTCUSDT": candles}, available=300.0)
    item = result["results"]["BTCUSDT"]
    assert item["risk_gate"]["approved"] is False
    assert item["risk_gate"]["reason"] == "exposure_limit"
    assert item["action"] != "BUY"
