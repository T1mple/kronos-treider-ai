from app.assets.models import Asset, AssetType

STOCKS = {
    symbol: Asset(symbol, AssetType.STOCK, exchange, "USD", sector=sector, country="US")
    for symbol, exchange, sector in [
        ("AAPL", "NASDAQ", "Technology"), ("MSFT", "NASDAQ", "Technology"),
        ("NVDA", "NASDAQ", "Semiconductors"), ("AMD", "NASDAQ", "Semiconductors"),
        ("AVGO", "NASDAQ", "Semiconductors"), ("AMZN", "NASDAQ", "Consumer"),
        ("META", "NASDAQ", "Communication"), ("GOOGL", "NASDAQ", "Communication"),
        ("TSLA", "NASDAQ", "Consumer"), ("JPM", "NYSE", "Financials"),
        ("V", "NYSE", "Financials"), ("MA", "NYSE", "Financials"),
        ("XOM", "NYSE", "Energy"), ("CVX", "NYSE", "Energy"),
        ("JNJ", "NYSE", "Healthcare"), ("UNH", "NYSE", "Healthcare"),
        ("KO", "NYSE", "Consumer"), ("PEP", "NASDAQ", "Consumer"),
    ]
}

ETFS = {
    symbol: Asset(symbol, AssetType.ETF, exchange, "USD", sector=sector, country="US")
    for symbol, exchange, sector in [
        ("SPY", "NYSEARCA", "Broad Market"), ("QQQ", "NASDAQ", "Technology"),
        ("VTI", "NYSEARCA", "Broad Market"), ("VOO", "NYSEARCA", "Broad Market"),
        ("DIA", "NYSEARCA", "Large Cap"), ("IWM", "NYSEARCA", "Small Cap"),
        ("EEM", "NYSEARCA", "Emerging Markets"), ("VUG", "NYSEARCA", "Growth"),
        ("SPHD", "NYSEARCA", "Dividend"), ("PFF", "NYSEARCA", "Preferred"),
        ("PGX", "NYSEARCA", "Preferred"), ("SDIV", "NYSEARCA", "Dividend"),
    ]
}
