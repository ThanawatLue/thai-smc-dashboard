"""
Deep Thesis Engine for Single Stock Analysis.
Pulls live fundamentals, business model breakdown, competitive moat analysis,
valuation multiples, Reverse DCF implied growth, scenarios, and pre-mortem risk evaluation.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional
import yfinance as yf

from src.portfolio_xray.reverse_dcf import solve_reverse_dcf

logger = logging.getLogger(__name__)


def generate_deep_thesis(symbol: str) -> dict:
    """
    Generates an institutional-grade Deep Thesis report for a single asset.
    """
    clean_sym = symbol.strip().upper()
    ticker = yf.Ticker(clean_sym)
    info = ticker.info or {}

    if not info or "currentPrice" not in info and "regularMarketPrice" not in info:
        return {
            "error": f"ไม่พบข้อมูลสำหรับสัญลักษณ์ {clean_sym} หรือข้อมูลไม่เพียงพอ",
            "symbol": clean_sym,
        }

    current_price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)
    market_cap = float(info.get("marketCap") or 0.0)
    shares_outstanding = float(info.get("sharesOutstanding") or (market_cap / max(current_price, 1e-6)))
    enterprise_value = float(info.get("enterpriseValue") or market_cap)
    total_debt = float(info.get("totalDebt") or 0.0)
    total_cash = float(info.get("totalCash") or 0.0)
    net_debt = total_debt - total_cash

    # Cash Flow & Income
    fcf = float(info.get("freeCashflow") or 0.0)
    # If FCF missing, try calculating from operating cashflow - capex
    if fcf <= 0:
        op_cf = float(info.get("operatingCashflow") or 0.0)
        # CapEx approximation from cashflow if available
        try:
            cf_df = ticker.cashflow
            if cf_df is not None and not cf_df.empty:
                capex = abs(float(cf_df.loc["Capital Expenditure"].iloc[0])) if "Capital Expenditure" in cf_df.index else 0.0
                fcf = max(0.0, op_cf - capex)
        except Exception:
            fcf = max(0.0, op_cf * 0.7) if op_cf > 0 else 0.0

    total_revenue = float(info.get("totalRevenue") or 0.0)
    rev_growth_yoy = float(info.get("revenueGrowth") or 0.0)
    gross_margin = float(info.get("grossMargins") or 0.0)
    operating_margin = float(info.get("operatingMargins") or 0.0)
    fcf_margin = (fcf / total_revenue) if total_revenue > 0 and fcf > 0 else 0.0

    # Valuation Multiples
    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    ev_to_ebitda = info.get("enterpriseToEbitda")
    ev_to_sales = info.get("enterpriseToRevenue")
    price_to_book = info.get("priceToBook")
    peg_ratio = info.get("pegRatio")
    div_yield = info.get("dividendYield") or 0.0

    # Returns & Balance Sheet Health
    roe = float(info.get("returnOnEquity") or 0.0)
    roa = float(info.get("returnOnAssets") or 0.0)
    current_ratio = float(info.get("currentRatio") or 1.0)
    debt_to_equity = float(info.get("debtToEquity") or 0.0)
    beta = float(info.get("beta") or 1.0)

    # Analyst Targets
    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    recommendation = info.get("recommendationKey", "N/A").upper()
    num_analysts = info.get("numberOfAnalystOpinions")

    # Run Reverse DCF
    dcf_result = solve_reverse_dcf(
        current_price=current_price,
        shares_outstanding=shares_outstanding,
        current_fcf=fcf,
        net_debt=net_debt,
        wacc=max(0.08, min(0.12, 0.045 + beta * 0.05)),  # Dynamic WACC based on beta
        terminal_growth=0.025,
        forecast_years=10,
    )

    # Determine Moat Strengths
    moat_tags = []
    if gross_margin > 0.50 or operating_margin > 0.25:
        moat_tags.append("High Pricing Power / Cost Advantage (อัตรากำไรสูง)")
    if roe > 0.20:
        moat_tags.append("Capital Efficiency / High ROIC (ผลตอบแทนต่อเงินทุนสูง)")
    if info.get("sector") in ["Technology", "Communication Services"]:
        moat_tags.append("Ecosystem & High Switching Costs (การเปลี่ยนผู้ให้บริการทำได้ยาก)")

    if not moat_tags:
        moat_tags.append("Commoditized / Competitive Industry (ต้องพึ่งพาต้นทุนหรือปริมาณการขาย)")

    # Pre-Mortem evaluation
    pre_mortem = [
        f"1. Valuation De-Rating: หากการเติบโตของ FCF ไม่ถึงระดับที่ตลาดคาดหวัง ({dcf_result.get('implied_fcf_growth_pct', 'N/A')}%) Multiple P/E อาจหดตัวลงอย่างมีนัยสำคัญ",
        f"2. Margin Compression: ความเสี่ยงด้านต้นทุน R&D / Capex หรือการแข่งขันด้านราคาที่จะกดดัน Gross Margin ({round(gross_margin * 100, 1)}%)",
        f"3. Macro & Beta Sensitivity: หุ้นมีค่า Beta เท่ากับ {round(beta, 2)} จึงมีความอ่อนไหวต่อภาวะสภาพคล่องและทิศทางอัตราดอกเบี้ย",
    ]

    return {
        "symbol": clean_sym,
        "name": info.get("longName") or info.get("shortName") or clean_sym,
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "country": info.get("country", "US"),
        "summary": info.get("longBusinessSummary", "ไม่มีคำอธิบาย"),
        "current_price": current_price,
        "market_cap": market_cap,
        "enterprise_value": enterprise_value,
        "shares_outstanding": shares_outstanding,
        "beta": round(beta, 2),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "financials": {
            "total_revenue": total_revenue,
            "revenue_growth_yoy_pct": round(rev_growth_yoy * 100, 2),
            "gross_margin_pct": round(gross_margin * 100, 2),
            "operating_margin_pct": round(operating_margin * 100, 2),
            "fcf": fcf,
            "fcf_margin_pct": round(fcf_margin * 100, 2),
            "roe_pct": round(roe * 100, 2),
            "roa_pct": round(roa * 100, 2),
            "net_debt": net_debt,
            "current_ratio": round(current_ratio, 2),
            "debt_to_equity": round(debt_to_equity, 2),
        },
        "multiples": {
            "trailing_pe": round(float(trailing_pe), 2) if trailing_pe else "N/A",
            "forward_pe": round(float(forward_pe), 2) if forward_pe else "N/A",
            "ev_to_ebitda": round(float(ev_to_ebitda), 2) if ev_to_ebitda else "N/A",
            "ev_to_sales": round(float(ev_to_sales), 2) if ev_to_sales else "N/A",
            "price_to_book": round(float(price_to_book), 2) if price_to_book else "N/A",
            "peg_ratio": round(float(peg_ratio), 2) if peg_ratio else "N/A",
            "dividend_yield_pct": round(float(div_yield) * 100, 2),
        },
        "analyst_consensus": {
            "target_mean": target_mean,
            "target_high": target_high,
            "target_low": target_low,
            "recommendation": recommendation,
            "number_of_analysts": num_analysts,
        },
        "reverse_dcf": dcf_result,
        "moat_analysis": moat_tags,
        "pre_mortem": pre_mortem,
        "as_of_date": info.get("regularMarketTime") or "Latest Available",
    }
