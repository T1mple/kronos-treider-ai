from dataclasses import asdict
from app.config import settings
from app.paper.engine import PaperTradingEngine
from app.paper.competition import RobotCompetition
from app.data.binance_public import fetch_klines
from app.data.stocks.provider import AlphaVantageStockProvider
from app.assets.universe import AssetUniverse
from app.research.runner import ResearchRunner
from app.research.stock_report import StockResearchReport
from app.paper.reporting import PeriodicReporter

COMMANDS = ['/help','/status','/balance','/positions','/trades','/signals','/kronos','/competition','/risk','/pause','/resume','/emergency','/test','/performance','/reports','/stocks','/stock','/etf','/sectors','/market']

def authorized(user_id: int) -> bool:
    ids={x.strip() for x in settings.telegram_admin_ids.split(',') if x.strip()}
    return str(user_id) in ids

class TelegramDashboard:
    """Read-only/paper Telegram interface. It never enables live trading."""
    def __init__(self, paper=None):
        self.paper=paper or PaperTradingEngine()
        self.paused=False
        self.reporter=PeriodicReporter()
        self.universe=AssetUniverse()
        self.stock_provider=AlphaVantageStockProvider()
        self.stock_report=StockResearchReport(self.universe)

    def status(self):
        return {'mode':'PAPER','live_trading':False,'paused':self.paused,'cash':self.paper.ledger.cash,'positions':len(self.paper.ledger.positions)}
    def balance(self): return {'cash':self.paper.ledger.cash,'equity':self.paper.equity({})}
    def positions(self): return [asdict(x) for x in self.paper.ledger.positions.values()]
    def trades(self): return [asdict(x) for x in self.paper.ledger.fills]
    def pause(self): self.paused=True; return {'paused':True}
    def resume(self): self.paused=False; return {'paused':False}
    def emergency(self): self.paused=True; return {'paused':True,'emergency':True}
    def reports(self, records=None): return self.reporter.all_periods(records or [])

    async def kronos(self, symbol='BTCUSDT', interval='1h', limit=200):
        runner=ResearchRunner()
        result=await runner.run(symbol,interval,limit,train_size=max(50,limit//2),test_size=min(50,max(5,limit//10)),step=min(50,max(5,limit//10)))
        return result.kronos

    async def signals(self, symbol='BTCUSDT', interval='1h', limit=200):
        runner=ResearchRunner()
        result=await runner.run(symbol,interval,limit,train_size=max(50,limit//2),test_size=min(50,max(5,limit//10)),step=min(50,max(5,limit//10)))
        return result.strategies

    async def competition(self, symbol='BTCUSDT', interval='1h', limit=500):
        candles=await fetch_klines(symbol,interval,limit)
        return RobotCompetition(starting_balance=300.0).report(candles)

    async def stock_report(self, symbol):
        asset=self.universe.get(symbol)
        if asset is None: raise ValueError(f'Неизвестный актив: {symbol.upper()}')
        candles=await self.stock_provider.candles(symbol,limit=100)
        quote=await self.stock_provider.quote(symbol)
        result=self.stock_report.build(symbol,candles)
        result['price']=quote.price
        result['volume']=quote.volume
        result['timestamp']=quote.timestamp.isoformat()
        return result

    def assets(self, asset_type=None):
        assets=self.universe.all() if asset_type is None else self.universe.by_type(asset_type)
        return [asdict(x) for x in assets]
