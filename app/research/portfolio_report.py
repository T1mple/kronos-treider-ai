from dataclasses import dataclass
from typing import Sequence

from app.research.monte_carlo import MonteCarloResult, run_monte_carlo
from app.research.portfolio_backtester import PortfolioBacktestResult
from app.research.stress_test import StressResult, StressScenario, run_stress_test

@dataclass(frozen=True)
class StrategySummary:
    name: str
    total_return: float
    sharpe: float
    max_drawdown: float
    trades: int
    win_rate: float

@dataclass(frozen=True)
class ResearchReport:
    portfolio: PortfolioBacktestResult
    strategies: tuple[StrategySummary, ...]
    monte_carlo: MonteCarloResult
    stress: tuple[StressResult, ...]
    paper_eligible: bool
    rejection_reasons: tuple[str, ...]

def build_research_report(portfolio: PortfolioBacktestResult, *, monte_carlo_simulations=2000, monte_carlo_horizon=None, max_drawdown_for_paper=0.20, min_sharpe_for_paper=0.50, max_loss_probability=0.50, stress_scenarios: Sequence[StressScenario] | None = None) -> ResearchReport:
    returns = [portfolio.equity_curve[i] / portfolio.equity_curve[i-1] - 1.0 for i in range(1, len(portfolio.equity_curve)) if portfolio.equity_curve[i-1] > 0]
    mc = run_monte_carlo(returns, initial_cash=portfolio.initial_cash, simulations=monte_carlo_simulations, horizon=monte_carlo_horizon)
    scenarios = tuple(stress_scenarios or (StressScenario('BASELINE'), StressScenario('CRASH', return_shock=-0.03), StressScenario('HIGH_VOLATILITY', volatility_multiplier=2.0), StressScenario('ADVERSE_FEES', fee_multiplier=2.0)))
    stress = run_stress_test(returns, scenarios, portfolio.initial_cash)
    reasons = []
    if portfolio.sharpe < min_sharpe_for_paper: reasons.append('portfolio Sharpe below paper threshold')
    if portfolio.max_drawdown > max_drawdown_for_paper: reasons.append('portfolio drawdown above paper threshold')
    if mc.probability_of_loss > max_loss_probability: reasons.append('Monte Carlo probability of loss above threshold')
    summaries = tuple(StrategySummary(name, result.total_return, result.sharpe, result.max_drawdown, result.trades, result.win_rate) for name, result in portfolio.strategy_results.items())
    return ResearchReport(portfolio, summaries, mc, stress, not reasons, tuple(reasons))

def format_research_report(report: ResearchReport) -> str:
    p, mc = report.portfolio, report.monte_carlo
    lines = ['KRONOS PORTFOLIO RESEARCH REPORT', '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', f'Initial Capital: ${p.initial_cash:,.2f}', f'Final Equity:    ${p.final_equity:,.2f}', f'Total Return:    {p.total_return:.2%}', f'Sharpe:          {p.sharpe:.2f}', f'Sortino:         {p.sortino:.2f}', f'Max Drawdown:    {p.max_drawdown:.2%}', f'Volatility:      {p.volatility:.2%}', f'Turnover:        {p.turnover:.2f}', '', 'MONTE CARLO', f'P05:             ${mc.percentile_5:,.2f}', f'Median:          ${mc.percentile_50:,.2f}', f'P95:             ${mc.percentile_95:,.2f}', f'Probability Loss:{mc.probability_of_loss:.2%}', '', 'FINAL ALLOCATION']
    lines += [f'{name:<24} {weight:.2%}' for name, weight in sorted(p.final_allocations.items(), key=lambda x: x[1], reverse=True)]
    lines += ['', 'STRESS'] + [f'{s.scenario:<24} ${s.final_equity:,.2f} | DD {s.max_drawdown:.2%}' for s in report.stress]
    lines += ['', f"PAPER ELIGIBILITY: {'APPROVED' if report.paper_eligible else 'REJECTED'}"] + [f'- {r}' for r in report.rejection_reasons]
    return '\n'.join(lines)