from app.telegram_runner import format_dict, format_report


def test_format_report_escapes_html_in_dynamic_diagnostics():
    report = {
        "equity": 300.0,
        "total_pnl": 0.0,
        "realized_pnl": 0.0,
        "closed_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "win_rate": 0.0,
        "max_drawdown": 0.0,
        "snapshots": 1,
    }
    diagnostics = {
        "decisions": 1,
        "actions": {"HOLD": 1},
        "reasons": {"alpha_below_threshold:+0.162<0.200 & test": 1},
        "latest": [{
            "symbol": "BTC<USDT",
            "signal": 0.162,
            "confidence": 0.561,
            "action": "HOLD",
            "reason": "alpha_below_threshold:+0.162<0.200 & test",
        }],
    }
    output = format_report(report, diagnostics)
    assert "&lt;" in output
    assert "&gt;" in output
    assert "&amp;" in output
    assert "<alpha_below_threshold" not in output


def test_format_dict_escapes_dynamic_values():
    output = format_dict("<title>", {"reason": "x < y & z"})
    assert "&lt;title&gt;" in output
    assert "x &lt; y &amp; z" in output
