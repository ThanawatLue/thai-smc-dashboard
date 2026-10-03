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

    # 3-Year Historical Financials
    hist_financials = []
    try:
        fin_df = ticker.financials
        if fin_df is not None and not fin_df.empty:
            years = sorted([c for c in fin_df.columns if hasattr(c, 'strftime')])[-3:]
            for y_ts in years:
                y_str = str(y_ts)[:10]
                rev_val = float(fin_df.loc["Total Revenue", y_ts]) if "Total Revenue" in fin_df.index and str(fin_df.loc["Total Revenue", y_ts]) != 'nan' else 0.0
                gp_val = float(fin_df.loc["Gross Profit", y_ts]) if "Gross Profit" in fin_df.index and str(fin_df.loc["Gross Profit", y_ts]) != 'nan' else 0.0
                op_val = float(fin_df.loc["Operating Income", y_ts]) if "Operating Income" in fin_df.index and str(fin_df.loc["Operating Income", y_ts]) != 'nan' else 0.0
                ni_val = float(fin_df.loc["Net Income Common Stockholders", y_ts]) if "Net Income Common Stockholders" in fin_df.index and str(fin_df.loc["Net Income Common Stockholders", y_ts]) != 'nan' else (float(fin_df.loc["Net Income", y_ts]) if "Net Income" in fin_df.index and str(fin_df.loc["Net Income", y_ts]) != 'nan' else 0.0)

                hist_financials.append({
                    "date": y_str,
                    "revenue": rev_val,
                    "gross_profit": gp_val,
                    "gross_margin_pct": round((gp_val / rev_val) * 100, 1) if rev_val > 0 else 0.0,
                    "operating_income": op_val,
                    "operating_margin_pct": round((op_val / rev_val) * 100, 1) if rev_val > 0 else 0.0,
                    "net_income": ni_val,
                })
    except Exception as e:
        logger.debug(f"Historical financials fetch failed: {e}")

    # TAM & Growth Driver Estimation
    sector_str = info.get("sector", "")
    ind_str = info.get("industry", "")
    if "Semiconductor" in ind_str or "Hardware" in ind_str:
        tam_size_bn = 1200.0  # $1.2T
        tam_description = "AI Accelerators, Data Center Compute & Edge Silicon (Expected $1.2T by 2030)"
        s_curve_phase = "Rapid Growth / Scaling Phase (Enterprise AI Adoption)"
        catalysts = [
            "Data Center Capex expansion from Hyperscalers (Microsoft, Meta, Google, Amazon)",
            "Generative AI inference scaling across edge devices and sovereign AI",
            "Next-gen packaging & architecture transitions (e.g. Blackwell, Rubin)"
        ]
    elif "Software" in ind_str or "Cloud" in ind_str:
        tam_size_bn = 850.0
        tam_description = "Enterprise Cloud Software, Cybersecurity & AI Automation"
        s_curve_phase = "Mid-to-Late Expansion Phase"
        catalysts = [
            "AI Copilot and agentic workflow monetization",
            "Consolidation of multi-point SaaS into unified platforms",
            "Expansion into regulated industries (Healthcare, Government, Finance)"
        ]
    elif "Aerospace" in ind_str or "Space" in ind_str:
        tam_size_bn = 1500.0
        tam_description = "Global Space Economy, Satellite Launch & Constellation Services (Expected $1.5T+ by 2035)"
        s_curve_phase = "Early-to-Mid Commercialization S-Curve"
        catalysts = [
            "Launch cadence acceleration and medium-lift rocket deployment",
            "Defense and national security constellation contracts (SDA, USSF)",
            "Direct-to-device cellular satellite connectivity"
        ]
    else:
        tam_size_bn = max(100.0, (market_cap / 1e9) * 5.0)
        tam_description = f"Global {ind_str or sector_str} Market Opportunity"
        s_curve_phase = "Mature Growth / Cash Generation Phase"
        catalysts = [
            "Market share expansion through technological differentiation",
            "Operating leverage and margin expansion",
            "Share buybacks and capital return programs"
        ]

    penetration_pct = round(((total_revenue / 1e9) / max(tam_size_bn, 1.0)) * 100, 1)

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
        "historical_financials": hist_financials,
        "tam_analysis": {
            "tam_size_bn": tam_size_bn,
            "tam_description": tam_description,
            "current_revenue_bn": round(total_revenue / 1e9, 2),
            "penetration_pct": penetration_pct,
            "s_curve_phase": s_curve_phase,
            "catalysts": catalysts,
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
            "target_mean": round(float(target_mean), 2) if target_mean else "N/A",
            "target_high": round(float(target_high), 2) if target_high else "N/A",
            "target_low": round(float(target_low), 2) if target_low else "N/A",
            "upside_mean_pct": round(((float(target_mean) - current_price) / current_price) * 100, 1) if target_mean and current_price > 0 else None,
            "upside_high_pct": round(((float(target_high) - current_price) / current_price) * 100, 1) if target_high and current_price > 0 else None,
            "upside_low_pct": round(((float(target_low) - current_price) / current_price) * 100, 1) if target_low and current_price > 0 else None,
            "recommendation": recommendation,
            "recommendation_th": {
                "STRONG_BUY": "แนะนำซื้ออย่างยิ่ง (Strong Buy)",
                "BUY": "แนะนำซื้อ (Buy / Outperform)",
                "HOLD": "ถือลงทุน (Hold / Neutral)",
                "UNDERPERFORM": "ลดน้ำหนักการลงทุน (Underperform)",
                "SELL": "แนะนำขาย (Sell)",
            }.get(recommendation, recommendation),
            "number_of_analysts": num_analysts or "N/A",
        },
        "investment_verdict": {
            "action": (
                "ACCUMULATE (ทยอยสะสม)"
                if dcf_result.get("scenarios", {}).get("base", {}).get("upside_downside_pct", 0.0) > 15.0 and roe > 0.15
                else (
                    "HOLD / NEUTRAL (ถือรอจังหวะ)"
                    if dcf_result.get("scenarios", {}).get("base", {}).get("upside_downside_pct", 0.0) >= -10.0
                    else "WAIT / CAUTION (รอจังหวะย่อตัว)"
                )
            ),
            "summary": (
                "Fair Value สูงกว่าราคาตลาด และความสามารถในการทำกำไร (ROE) อยู่ในเกณฑ์แข็งแกร่ง เหมาะสำหรับทยอยสะสมตามรอบ"
                if dcf_result.get("scenarios", {}).get("base", {}).get("upside_downside_pct", 0.0) > 15.0 and roe > 0.15
                else (
                    "ราคาปัจจุบันสะท้อนการเติบโตส่วนใหญ่ไปแล้ว (Fairly Valued) ควรถือรอการพิสูจน์ผลประกอบการไตรมาสถัดไป"
                    if dcf_result.get("scenarios", {}).get("base", {}).get("upside_downside_pct", 0.0) >= -10.0
                    else "ตลาดกำลังสะท้อนความคาดหวังการเติบโตที่ตึงตัวเกินไป (Stretched Valuation) ควรรอราคาปรับฐานเพื่อเพิ่ม Margin of Safety"
                )
            ),
            "base_fair_value": dcf_result.get("scenarios", {}).get("base", {}).get("target_price"),
            "margin_of_safety_pct": dcf_result.get("scenarios", {}).get("base", {}).get("upside_downside_pct", 0.0),
        },
        "reverse_dcf": dcf_result,
        "moat_analysis": moat_tags,
        "pre_mortem": pre_mortem,
        "as_of_date": info.get("regularMarketTime") or "Latest Available",
    }
