from app.research.pipeline import ResearchPipeline
from app.research.indicators import sma, zscore

def test_indicators():
    values=[1,2,3,4,5]
    assert sma(values,3)==4
    assert zscore(values,5) is not None

def test_pipeline_is_bounded():
    result=ResearchPipeline().evaluate("BTC/USDT",0.8,0.9,0.7)
    assert -1 <= result.ensemble_score <= 1
    assert 0 <= result.confidence <= 1
