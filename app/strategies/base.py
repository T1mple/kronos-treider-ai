from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Signal:
    symbol: str
    score: float
    confidence: float
    strategy: str

class Strategy(ABC):
    name: str
    @abstractmethod
    async def generate(self, market): ...
