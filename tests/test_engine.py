from th_smc.engine import analyze_symbol, make_sample_ohlcv, normalize_symbol


def test_normalize_symbol_accepts_plain_ticker():
    assert normalize_symbol("ptt", "TH") == "PTT.BK"


def test_normalize_symbol_rejects_non_th_suffix():
    assert normalize_symbol("AAPL", "US") == "AAPL"


def test_analyze_symbol_returns_rr_and_checklist():
    df = make_sample_ohlcv("PTT.BK")
    result = analyze_symbol("PTT", df)
    assert result["symbol"] == "PTT.BK"
    assert "rr_pass" in result["checklist"]
    assert result["decision"] in {"ARMED", "NO TRADE", "WAIT"}
    assert result["candles"]
