from th_smc.engine import analyze_symbol, make_sample_ohlcv, normalize_th_symbol


def test_normalize_th_symbol_accepts_plain_ticker():
    assert normalize_th_symbol("ptt") == "PTT.BK"


def test_normalize_th_symbol_rejects_non_th_suffix():
    try:
        normalize_th_symbol("AAPL")
    except ValueError:
        raise AssertionError("Plain Thai-like ticker should be normalized")

    try:
        normalize_th_symbol("AAPL.US")
    except ValueError:
        return
    raise AssertionError("Non-.BK suffix should be rejected")


def test_analyze_symbol_returns_rr_and_checklist():
    df = make_sample_ohlcv("PTT.BK")
    result = analyze_symbol("PTT", df)
    assert result["symbol"] == "PTT.BK"
    assert "rr_3_plus" in result["checklist"]
    assert result["decision"] in {"ARMED", "NO TRADE", "WAIT"}
    assert result["candles"]
