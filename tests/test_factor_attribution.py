from app.research.factor_attribution import attribute, leave_one_out_score

def test_attribution_reconstructs_weighted_score():
    rows=attribute({"kronos":.8,"technical":.4},{"kronos":.6,"technical":.4})
    assert abs(sum(x["contribution"] for x in rows)-.64)<1e-9

def test_leave_one_out():
    result=leave_one_out_score({"a":1,"b":-1},{"a":.5,"b":.5})
    assert result["a"] == -1
