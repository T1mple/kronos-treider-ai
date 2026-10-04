from app.exchanges.mock import PaperExchange

class ExchangeRegistry:
    def __init__(self):
        self.adapters={'paper': PaperExchange()}
    def get(self, name): return self.adapters.get(name)
    def names(self): return list(self.adapters)
