from datetime import datetime, timezone
from app.exchanges.base import ExchangeAdapter

class PaperExchange(ExchangeAdapter):
    name = 'paper'
    def __init__(self):
        self._orders=[]
    async def balances(self): return {}
    async def positions(self): return []
    async def ticker(self, symbol): return {'symbol':symbol,'timestamp':datetime.now(timezone.utc).isoformat()}
    async def place_order(self, symbol, side, quantity, order_type='market'):
        order={'symbol':symbol,'side':side,'quantity':quantity,'type':order_type,'status':'filled','paper':True}
        self._orders.append(order)
        return order
