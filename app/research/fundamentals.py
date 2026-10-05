from dataclasses import dataclass

@dataclass(frozen=True)
class FundamentalFactors:
    valuation: float
    growth: float
    profitability: float
    balance_sheet: float
    dividend: float
    score: float

def _clip(x): return max(-1.0,min(1.0,float(x)))
def _norm(value, low, high):
    if value is None: return 0.0
    return _clip((float(value)-low)/(high-low)*2-1)

def score_overview(data):
    pe=data.get("PERatio"); peg=data.get("PEGRatio"); growth=data.get("QuarterlyRevenueGrowthYOY"); margin=data.get("ProfitMargin"); roe=data.get("ReturnOnEquityTTM"); debt=data.get("DebtToEquity"); dividend=data.get("DividendYield")
    valuation=_clip((-_norm(pe,10,40)+-_norm(peg,0.5,3))/2)
    growth=_norm(growth,0,0.30); profitability=_norm(margin,0,0.30)
    balance=_norm(debt,0,200)*-1; div=_norm(dividend,0,0.05)
    score=_clip(0.25*valuation+0.25*growth+0.25*profitability+0.15*balance+0.10*div)
    return FundamentalFactors(valuation,growth,profitability,balance,div,score)
