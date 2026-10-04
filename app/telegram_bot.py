from dataclasses import asdict
from app.config import settings
from app.paper.engine import PaperTradingEngine
from app.paper.competition import RobotCompetition
from app.data.binance_public import fetch_klines
from app.research.runner import ResearchRunner
from app.paper.reporting import PeriodicReporter

COMMANDS = ['/status','/balance','/positions','/trades','/signals','/kronos','/competition','/risk','/pause','/resume','/emergency']


def authorized(user_id: int) -> bool:
    ids={x.strip() for x in settings.telegram_admin_ids.split(',') if x.strip()}
    return str(user_id) in ids


class TelegramDashboard:
    """Read-only/paper Telegram interface. It never enables live trading."""
    def __init__(self, paper=None):
        self.paper=paper or PaperTradingEngine()
        self.paused=False
        self.reporter=PeriodicReporter()

    def status(self):
        return {
            'mode':'PAPER',
            'live_trading':False,
            'paused':self.paused,
            'cash':self.paper.ledger.cash,
            'positions':len(self.paper.ledger.positions),
        }

    def balance(self):
        return {'cash':self.paper.ledger.cash,'equity':self.paper.equity({})}

    def positions(self):
        return [asdict(x) for x in self.paper.ledger.positions.values()]

    def trades(self):
        return [asdict(x) for x in self.paper.ledger.fills]

    def pause(self):
        self.paused=True
        return {'paused':True}

    def resume(self):
        self.paused=False
        return {'paused':False}

    def emergency(self):
        self.paused=True
        return {'paused':True,'emergency':True}

    def reports(self, records=None):
        return self.reporter.all_periods(records or [])

    async def kronos(self, symbol='BTCUSDT', interval='1h', limit=200):
        runner=ResearchRunner()
        result=await runner.run(symbol,interval,limit,train_size=max(50,limit//2),test_size=min(50,max(5,limit//10)),step=min(50,max(5,limit//10)))
        return result.kronos

    async def signals(self, symbol='BTCUSDT', interval='1h', limit=200):
        runner=ResearchRunner()
        result=await runner.run(symbol,interval,limit,train_size=max(50,limit//2),test_size=min(50,max(5,limit//10)),step=min(50,max(5,limit//10)))
        return result.strategies

    async def competition(self, symbol='BTCUSDT', interval='1h', limit=500):
        """Research-only leaderboard. It never submits exchange orders."""
        candles=await fetch_klines(symbol,interval,limit)
        return RobotCompetition(starting_balance=300.0).leaderboard(candles)
