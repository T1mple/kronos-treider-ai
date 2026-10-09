from app.research.monte_carlo import run_monte_carlo
from app.research.stress_test import StressScenario, run_stress_test


def test_monte_carlo_is_reproducible():
    returns = [0.01, -0.005, 0.002, 0.0, 0.008, -0.003]
    a = run_monte_carlo(returns, simulations=100, horizon=20, seed=7)
    b = run_monte_carlo(returns, simulations=100, horizon=20, seed=7)
    assert a.terminal_equities == b.terminal_equities
    assert 0 <= a.probability_of_loss <= 1


def test_stress_test_applies_shock():
    returns = [0.01, 0.01, -0.01]
    result = run_stress_test(
        returns,
        [StressScenario("baseline"), StressScenario("crash", return_shock=-0.03)],
        initial_cash=300,
    )
    assert result[1].final_equity < result[0].final_equity
    assert result[1].max_drawdown >= 0
