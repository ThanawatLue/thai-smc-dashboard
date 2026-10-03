"""
Unit tests for AI Portfolio X-Ray Pro engine and components.
"""

import pytest
from src.portfolio_xray.parser import parse_portfolio_input, normalize_symbol
from src.portfolio_xray.holdings_data import get_asset_holdings, get_asset_metadata
from src.portfolio_xray.metrics import (
    calculate_look_through,
    calculate_overlap_matrix,
    calculate_concentration,
)
from src.portfolio_xray.reverse_dcf import solve_reverse_dcf
from src.portfolio_xray.engine import analyze


def test_symbol_normalization():
    assert normalize_symbol("btc") == "BTC-USD"
    assert normalize_symbol("ETH") == "ETH-USD"
    assert normalize_symbol("VOO") == "VOO"
    assert normalize_symbol("$AAPL") == "AAPL"


def test_parser_weighted_pct():
    raw = "VOO 35% QQQM 20% SCHD 15% GLD 10% TLT 10% BTC 10%"
    res = parse_portfolio_input(raw)
    assert res["mode"] == "portfolio"
    assert len(res["assets"]) == 6
    assert res["is_equal_weight"] is False
    assert res["equal_weight_warning"] is None
    symbols = [a["symbol"] for a in res["assets"]]
    assert "VOO" in symbols
    assert "BTC-USD" in symbols
    assert round(sum(a["weight"] for a in res["assets"]), 2) == 1.0


def test_parser_unweighted_equal_weight():
    raw = "VOO QQQM SCHD GLD TLT BTC"
    res = parse_portfolio_input(raw)
    assert res["mode"] == "portfolio"
    assert len(res["assets"]) == 6
    assert res["is_equal_weight"] is True
    assert "Illustrative Equal Weight" in res["equal_weight_warning"]
    for a in res["assets"]:
        assert abs(a["weight"] - 1.0 / 6.0) < 0.01


def test_parser_single_stock():
    raw = "NVDA"
    res = parse_portfolio_input(raw)
    assert res["mode"] == "single_stock"
    assert len(res["assets"]) == 1
    assert res["assets"][0]["symbol"] == "NVDA"
    assert res["assets"][0]["weight"] == 1.0


def test_holdings_curated():
    voo_h = get_asset_holdings("VOO")
    assert "NVDA" in voo_h
    assert "AAPL" in voo_h
    assert voo_h["NVDA"] > 0.05


def test_look_through_calculation():
    assets = [
        {"symbol": "VOO", "weight": 0.5},
        {"symbol": "QQQM", "weight": 0.5},
    ]
    lt = calculate_look_through(assets)
    assert "top_holdings" in lt
    assert len(lt["top_holdings"]) > 0
    top_syms = [h["symbol"] for h in lt["top_holdings"]]
    assert "NVDA" in top_syms
    assert "AAPL" in top_syms
    assert lt["big_tech_exposure_pct"] > 0


def test_overlap_matrix():
    tickers = ["VOO", "QQQM", "GLD"]
    overlap = calculate_overlap_matrix(tickers)
    mat = overlap["matrix"]
    # Diagonal should be 1.0
    assert mat[0][0] == 1.0
    assert mat[1][1] == 1.0
    assert mat[2][2] == 1.0
    # VOO vs QQQM has substantial overlap
    assert mat[0][1] > 0.25
    # GLD (gold) has 0 overlap with VOO
    assert mat[0][2] == 0.0
    assert len(overlap["redundant_pairs"]) >= 1


def test_concentration_hhi():
    # 2 equal assets -> HHI = 0.5^2 + 0.5^2 = 0.5, N_eff = 2.0
    assets = [
        {"symbol": "A", "weight": 0.5},
        {"symbol": "B", "weight": 0.5},
    ]
    eff_holdings = [
        {"symbol": "A", "effective_weight": 0.5},
        {"symbol": "B", "effective_weight": 0.5},
    ]
    conc = calculate_concentration(assets, eff_holdings)
    assert conc["stated_hhi"] == 0.5
    assert conc["stated_effective_positions"] == 2.0


def test_reverse_dcf_solver():
    res = solve_reverse_dcf(
        current_price=100.0,
        shares_outstanding=1_000_000,
        current_fcf=5_000_000,
        net_debt=0.0,
        wacc=0.09,
    )
    assert "implied_fcf_growth_pct" in res
    assert res["implied_fcf_growth_pct"] is not None
    assert "scenarios" in res
    assert "bear" in res["scenarios"]
    assert "base" in res["scenarios"]
    assert "bull" in res["scenarios"]


def test_reverse_dcf_negative_fcf():
    res = solve_reverse_dcf(
        current_price=50.0,
        shares_outstanding=1_000_000,
        current_fcf=-1_000_000,
    )
    assert "error" in res
    assert res.get("is_unprofitable") is True


def test_analyze_portfolio_end_to_end():
    res = analyze("VOO 60% SCHD 40%", portfolio_value=500_000, period="1y")
    assert res["mode"] == "portfolio"
    assert len(res["assets"]) == 2
    assert "look_through" in res
    assert "overlap" in res
    assert "concentration" in res
    assert "risk_return" in res
    assert "html_report" in res
    assert "<!DOCTYPE html>" in res["html_report"]


def test_flask_api_xray_endpoints():
    from dashboard.app import app
    client = app.test_client()

    # 1. Analyze endpoint
    r1 = client.post("/api/xray/analyze", json={"input": "VOO 60% SCHD 40%", "portfolio_value": 1000000})
    assert r1.status_code == 200
    d1 = r1.get_json()
    assert d1["mode"] == "portfolio"
    assert len(d1["assets"]) == 2

    # 2. Export HTML endpoint
    r2 = client.post("/api/xray/export-html", json={"input": "NVDA"})
    assert r2.status_code == 200
    assert "text/html" in r2.headers.get("Content-Type", "")
    assert "<!DOCTYPE html>" in r2.data.decode("utf-8")


def test_risk_contribution_and_rebalancing():
    from src.portfolio_xray.metrics import calculate_risk_return

    tickers = ["VOO", "QQQ", "GLD"]
    weights = [0.5, 0.3, 0.2]

    res = calculate_risk_return(tickers=tickers, weights=weights, period="1y")
    assert "risk_contribution" in res
    assert len(res["risk_contribution"]) == 3
    # Check sum of risk contribution is approximately 100%
    total_rc = sum(rc["risk_contribution_pct"] for rc in res["risk_contribution"])
    assert 99.0 <= total_rc <= 101.0
    assert "rebalancing_plan" in res


def test_tam_and_historical_financials():
    from src.portfolio_xray.deep_thesis import generate_deep_thesis

    # Call with NVDA (should return TAM and financial trends)
    res = generate_deep_thesis("NVDA")
    assert "tam_analysis" in res
    tam = res["tam_analysis"]
    assert "tam_size_bn" in tam
    assert tam["tam_size_bn"] > 0
    assert "s_curve_phase" in tam
    assert "historical_financials" in res
    assert isinstance(res["historical_financials"], list)


def test_html_generator_renders_new_sections():
    from src.portfolio_xray.html_generator import generate_portfolio_html_report, generate_thesis_html_report

    sample_xray = {
        "summary": "Portfolio X-Ray",
        "assets": [{"symbol": "VOO", "weight": 0.6, "weight_pct": 60.0}],
        "look_through": {"top_holdings": []},
        "overlap": {"redundant_pairs": []},
        "concentration": {"effective_positions": 1.5, "verdict": "Moderate"},
        "risk_return": {
            "portfolio": {"cagr_pct": 12.5, "max_drawdown_pct": -10.2, "sharpe_ratio": 1.1},
            "benchmark": {"cagr_pct": 10.0},
            "risk_contribution": [{"symbol": "VOO", "weight_pct": 60.0, "risk_contribution_pct": 60.0, "is_risk_dominator": False}],
            "rebalancing_plan": [],
        }
    }
    p_html = generate_portfolio_html_report(sample_xray)
    assert "Risk Contribution & Variance Attribution" in p_html
    assert "Position Sizing & Rebalancing Action Plan" in p_html

    sample_thesis = {
        "symbol": "NVDA",
        "current_price": 120.0,
        "financials": {"gross_margin_pct": 75.0, "operating_margin_pct": 60.0, "roe_pct": 80.0},
        "multiples": {"trailing_pe": 45.0, "forward_pe": 35.0},
        "reverse_dcf": {"implied_fcf_growth_pct": 25.0, "reality_check": "Moderate Growth", "scenarios": {}},
        "tam_analysis": {"tam_size_bn": 1200.0, "s_curve_phase": "Rapid Growth"},
        "historical_financials": [{"date": "2024", "revenue": 60e9, "gross_margin_pct": 72.0, "operating_income": 32e9, "operating_margin_pct": 54.0, "net_income": 29e9}],
        "moat_analysis": ["CUDA Ecosystem"],
        "pre_mortem": ["Hyperscaler Capex slow down"],
    }
    t_html = generate_thesis_html_report(sample_thesis)
    assert "Total Addressable Market (TAM)" in t_html
    assert "Historical Financial Trend" in t_html


