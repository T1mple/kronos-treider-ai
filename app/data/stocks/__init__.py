"""Read-only stock/ETF data interfaces."""
from app.data.stocks.provider import StockDataProvider, StaticStockDataProvider
__all__ = ["StockDataProvider", "StaticStockDataProvider"]
