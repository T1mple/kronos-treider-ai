from app.reporting import rank_reports, summarize_backtest
from app.backtest import BacktestResult

def test_report_ranking():
    a=summarize_backtest("a",BacktestResult(300,330,4,0.1,0.1,1))
    b=summarize_backtest("b",BacktestResult(300,320,4,0.05,0.066,1))
    assert rank_reports([a,b])[0].strategy == "a"
