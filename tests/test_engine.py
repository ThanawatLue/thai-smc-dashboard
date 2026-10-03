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


def test_load_market_snapshot_gold_returns_precious_metals():
    from th_smc.engine import load_market_snapshot
    rows, meta = load_market_snapshot("GOLD")
    assert len(rows) >= 5
    symbols = {r["symbol"] for r in rows}
    assert "GC=F" in symbols
    assert "GLD" in symbols
    assert "SI=F" in symbols


def test_collect_candidate_sources_fallback_guarantees_candidates():
    from unittest.mock import patch
    from th_smc.engine import collect_candidate_sources, load_market_snapshot
    import th_smc.engine as engine
    
    # Mock load_market_snapshot to simulate Render cloud 429
    def mock_load(market):
        if market == "TH":
            fallback = [{"symbol": s, "name": s} for s in engine.DEFAULT_TH_SYMBOLS[:10]]
        elif market in ["US", "US_MEDIUM_TERM"]:
            fallback = [{"symbol": s, "name": s} for s in engine.DEFAULT_US_SYMBOLS[:10]]
        else:
            fallback = engine.DEFAULT_GOLD_SYMBOLS
        return fallback, {"provider": "local_fallback_universe", "raw_count": len(fallback), "common_stock_count": len(fallback), "error": "429"}

    with patch("th_smc.engine.load_market_snapshot", side_effect=mock_load):
        for m in ["TH", "US", "GOLD"]:
            res = collect_candidate_sources(m)
            assert len(res["candidates"]) > 0, f"Expected candidates for {m} even under 429"

