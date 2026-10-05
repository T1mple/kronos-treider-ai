from dataclasses import dataclass
import httpx


@dataclass(frozen=True)
class ExchangeQuote:
    venue: str
    symbol: str
    bid: float
    ask: float


@dataclass(frozen=True)
class ArbitrageOpportunity:
    kind: str
    symbol: str
    buy_venue: str
    sell_venue: str
    gross_edge: float
    net_edge: float
    detail: str


async def _get_json(url, params=None):
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


async def fetch_quotes(symbol="BTCUSDT"):
    okx_symbol = f"{symbol[:-4]}-USDT" if symbol.endswith("USDT") else symbol
    rows = []
    try:
        x = await _get_json("https://api.binance.com/api/v3/ticker/bookTicker", {"symbol": symbol})
        rows.append(ExchangeQuote("binance", symbol, float(x["bidPrice"]), float(x["askPrice"])))
    except Exception:
        pass
    try:
        x = await _get_json("https://www.okx.com/api/v5/market/ticker", {"instId": okx_symbol})
        item = x["data"][0]
        rows.append(ExchangeQuote("okx", symbol, float(item["bidPx"]), float(item["askPx"])))
    except Exception:
        pass
    try:
        x = await _get_json("https://api.bybit.com/v5/market/tickers", {"category": "spot", "symbol": symbol})
        item = x["result"]["list"][0]
        rows.append(ExchangeQuote("bybit", symbol, float(item["bid1Price"]), float(item["ask1Price"])))
    except Exception:
        pass
    return rows


def best_cross_exchange(quotes, fee_rate=0.001, slippage_rate=0.0005):
    if len(quotes) < 2:
        return None
    best = None
    for buy in quotes:
        for sell in quotes:
            if buy.venue == sell.venue or buy.ask <= 0:
                continue
            gross = sell.bid / buy.ask - 1.0
            net = gross - 2.0 * (fee_rate + slippage_rate)
            candidate = ArbitrageOpportunity(
                "cross_exchange_arb", buy.symbol, buy.venue, sell.venue,
                gross, net, "public spot bid/ask; excludes transfer latency and inventory costs",
            )
            if best is None or candidate.net_edge > best.net_edge:
                best = candidate
    return best


async def fetch_spot_perp(symbol="BTCUSDT"):
    try:
        spot = await _get_json("https://api.binance.com/api/v3/ticker/bookTicker", {"symbol": symbol})
        perp = await _get_json("https://fapi.binance.com/fapi/v1/premiumIndex", {"symbol": symbol})
        spot_mid = (float(spot["bidPrice"]) + float(spot["askPrice"])) / 2.0
        mark = float(perp["markPrice"])
        basis = mark / spot_mid - 1.0
        funding = float(perp.get("lastFundingRate", 0.0))
        net = abs(basis) + abs(funding) - 2.0 * (0.001 + 0.0005)
        return ArbitrageOpportunity(
            "spot_perp_arb", symbol, "binance_spot", "binance_perp",
            basis, net,
            f"basis={basis:+.4%}; last funding={funding:+.4%}; research-only",
        )
    except Exception:
        return None


__all__ = ["ExchangeQuote", "ArbitrageOpportunity", "fetch_quotes", "best_cross_exchange", "fetch_spot_perp"]
