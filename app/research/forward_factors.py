from dataclasses import dataclass

@dataclass(frozen=True)
class FactorObservation:
    symbol: str
    timestamp: str
    score: float
    confidence: float
    price: float

@dataclass(frozen=True)
class FactorOutcome:
    symbol: str
    horizon: int
    score: float
    price_return: float
    correct_direction: bool

def evaluate_outcome(observation, future_price, horizon):
    ret=(float(future_price)/observation.price-1.0) if observation.price else 0.0
    expected=1 if observation.score>0 else (-1 if observation.score<0 else 0)
    actual=1 if ret>0 else (-1 if ret<0 else 0)
    return FactorOutcome(observation.symbol,int(horizon),observation.score,ret,expected==actual if expected else False)

class FactorForwardJournal:
    """In-memory forward evaluation for research; no trading side effects."""
    def __init__(self): self.observations=[]
    def add(self, observation): self.observations.append(observation)
    def pending(self, symbol=None): return [x for x in self.observations if symbol is None or x.symbol==symbol]
