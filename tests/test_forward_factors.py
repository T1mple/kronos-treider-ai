from app.research.forward_factors import FactorObservation, evaluate_outcome

def test_positive_factor_direction():
    obs=FactorObservation("NVDA","2026-10-05",.8,.9,100)
    outcome=evaluate_outcome(obs,110,5)
    assert outcome.price_return > 0
    assert outcome.correct_direction is True
