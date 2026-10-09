from app.research.portfolio_report import build_research_report, format_research_report
from app.research.portfolio_backtester import PortfolioBacktestResult

def test_report_contains_gate_and_metrics():
    portfolio = PortfolioBacktestResult(300, 330, 0.10, 1.0, 1.2, 0.05, 0.10, 1.0, (300, 303, 306, 310, 320, 330), (), {}, {'trend': 0.6, 'mean_reversion': 0.4})
    report = build_research_report(portfolio, monte_carlo_simulations=50, monte_carlo_horizon=10)
    output = format_research_report(report)
    assert 'KRONOS PORTFOLIO RESEARCH REPORT' in output
    assert 'PAPER ELIGIBILITY' in output