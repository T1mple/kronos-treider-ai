from dataclasses import dataclass, asdict
from app.assets.universe import AssetUniverse
from app.research.scanner import MarketScanner

@dataclass(frozen=True)
class ScanSnapshot:
    timestamp: str
    stocks: list
    etfs: list

class ResearchMarketScanner:
    """Multi-asset scanner boundary. Data is supplied by read-only providers."""
    def __init__(self, universe=None, scanner=None):
        self.universe=universe or AssetUniverse(); self.scanner=scanner or MarketScanner()
    def scan(self, datasets, timestamp):
        return ScanSnapshot(timestamp,self.scanner.stocks(datasets),self.scanner.etfs(datasets))
    @staticmethod
    def as_dict(snapshot): return asdict(snapshot)
