"""
Main Engine orchestrator for AI Portfolio X-Ray Pro.
Dispatches analysis between Portfolio X-Ray Mode and Deep Thesis Mode,
and coordinates HTML report generation.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

from src.portfolio_xray.parser import parse_portfolio_input
from src.portfolio_xray.holdings_data import get_asset_metadata
from src.portfolio_xray.metrics import (
    calculate_look_through,
    calculate_overlap_matrix,
    calculate_concentration,
    calculate_risk_return,
    calculate_fee_drag,
    calculate_macro_stress_test,
)
from src.portfolio_xray.deep_thesis import generate_deep_thesis
from src.portfolio_xray.html_generator import (
    generate_portfolio_html_report,
    generate_thesis_html_report,
)

logger = logging.getLogger(__name__)


def analyze(
    raw_input: str,
    portfolio_value: float = 1_000_000,
    currency: str = "THB",
    period: str = "3y",
    benchmark_symbol: str = "VOO",
) -> dict:
    """
    Main entry point for AI Portfolio X-Ray Pro.
    Automatically chooses between Portfolio X-Ray Mode and Deep Thesis Mode.
    """
    parsed = parse_portfolio_input(raw_input)
    mode = parsed.get("mode", "portfolio")
    assets = parsed.get("assets", [])

    if not assets:
        return {
            "error": "ไม่พบสัญลักษณ์สินทรัพย์ (Ticker) ที่ถูกต้อง กรุณาใส่สัญลักษณ์ เช่น 'VOO 35% QQQM 20% SCHD 15%' หรือ 'NVDA'",
            "raw_input": raw_input,
        }

    # 1. Single Asset -> Deep Thesis Mode
    if mode == "single_stock":
        sym = assets[0]["symbol"]
        thesis_data = generate_deep_thesis(sym)
        if "error" in thesis_data and not thesis_data.get("name"):
            return thesis_data

        html_report = generate_thesis_html_report(thesis_data)
        return {
            "mode": "single_stock",
            "symbol": sym,
            "data": thesis_data,
            "html_report": html_report,
            "raw_input": raw_input,
        }

    # 2. Multi-Asset -> Portfolio X-Ray Mode
    # Enrich assets with metadata (role, asset class, expense ratio, etc.)
    enriched_assets = []
    for a in assets:
        meta = get_asset_metadata(a["symbol"])
        merged = {**meta, **a}
        enriched_assets.append(merged)

    # Calculate Look-Through
    look_through = calculate_look_through(enriched_assets)

    # Calculate Overlap Matrix
    tickers = [a["symbol"] for a in enriched_assets]
    overlap = calculate_overlap_matrix(tickers)

    # Calculate Concentration (HHI)
    concentration = calculate_concentration(
        enriched_assets, look_through.get("top_holdings", [])
    )

    # Calculate Risk-Return Performance
    weights = [a["weight"] for a in enriched_assets]
    risk_return = calculate_risk_return(
        tickers=tickers,
        weights=weights,
        portfolio_value=portfolio_value,
        currency=currency,
        period=period,
        benchmark_symbol=benchmark_symbol,
    )

    # Calculate Fee Drag & Macro Stress Test
    fee_analysis = calculate_fee_drag(
        assets=enriched_assets,
        portfolio_value=portfolio_value,
        currency=currency,
    )
    macro_stress_test = calculate_macro_stress_test(
        assets=enriched_assets,
        portfolio_value=portfolio_value,
        currency=currency,
    )

    result_payload = {
        "mode": "portfolio",
        "assets": enriched_assets,
        "tickers": tickers,
        "is_equal_weight": parsed.get("is_equal_weight", False),
        "equal_weight_warning": parsed.get("equal_weight_warning"),
        "look_through": look_through,
        "overlap": overlap,
        "concentration": concentration,
        "risk_return": risk_return,
        "fee_analysis": fee_analysis,
        "macro_stress_test": macro_stress_test,
        "raw_input": raw_input,
    }

    # Generate Standalone HTML
    html_report = generate_portfolio_html_report(result_payload)
    result_payload["html_report"] = html_report

    return result_payload
