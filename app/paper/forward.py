from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass
class ForwardState:
    symbol:str
    last_timestamp:str=""
    processed:int=0
    skipped:int=0

class ForwardPaperMonitor:
    """Stateful research monitor. Processes each closed candle once."""
    def __init__(self):
        self.states={}

    def accept(self,symbol,candle_timestamp):
        state=self.states.setdefault(symbol,ForwardState(symbol))
        stamp=str(candle_timestamp)
        if state.last_timestamp and stamp<=state.last_timestamp:
            state.skipped+=1
            return False
        state.last_timestamp=stamp
        state.processed+=1
        return True

    def snapshot(self):
        return {k:v.__dict__.copy() for k,v in self.states.items()}
