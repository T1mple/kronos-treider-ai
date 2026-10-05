from dataclasses import dataclass
from app.research.technical_factors import calculate
from app.research.fundamentals import score_overview
from app.research.sentiment import score_news

@dataclass
class Candle:
    close: float
    volume: float

def test_technical_factors_are_bounded():
    candles=[Candle(100+i,1000+i*10) for i in range(30)]
    result=calculate(candles)
    assert -1 <= result.score <= 1

def test_fundamental_score_is_bounded():
    result=score_overview({'PERatio':'20','PEGRatio':'1.2','QuarterlyRevenueGrowthYOY':'0.2','ProfitMargin':'0.2','ReturnOnEquityTTM':'0.3','DebtToEquity':'50','DividendYield':'0.01'})
    assert -1 <= result.score <= 1

def test_sentiment_aggregates_articles():
    result=score_news({'feed':[{'overall_sentiment_score':'0.5'},{'overall_sentiment_score':'-0.2'}]})
    assert result.article_count == 2
    assert result.bullish == 0.5
