from app.paper.ledger import PaperLedger

class PaperTradingEngine:
    """Simulation-only execution engine. It never connects to an exchange."""
    def __init__(self, starting_cash=300.0, fee_rate=0.001):
        self.ledger=PaperLedger(starting_cash)
        self.fee_rate=fee_rate

    def buy(self, symbol, quantity, price):
        return self.ledger.execute(symbol,"buy",quantity,price,self.fee_rate)

    def sell(self, symbol, quantity, price):
        return self.ledger.execute(symbol,"sell",quantity,price,self.fee_rate)

    def equity(self, marks):
        value=self.ledger.cash
        for symbol,pos in self.ledger.positions.items():
            value += pos.quantity*float(marks.get(symbol,pos.average_price))
        return value
