"""
Reverse DCF Engine & Valuation Solver.
Solves for the implied 10-year Free Cash Flow growth rate embedded in current market prices,
and provides Bull / Base / Bear scenario intrinsic value modeling with Margin of Safety.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def solve_reverse_dcf(
    current_price: float,
    shares_outstanding: float,
    current_fcf: float,
    net_debt: float = 0.0,
    wacc: float = 0.09,
    terminal_growth: float = 0.025,
    forecast_years: int = 10,
) -> dict:
    """
    Uses bisection root-finding to solve for the implied 10-year FCF CAGR (g_implied)
    that equates the DCF model's equity value per share to the current market price.
    
    Formula:
    PV(FCF) = sum_{t=1}^N [ FCF_0 * (1 + g)^t / (1 + wacc)^t ]
    TV_N = [ FCF_N * (1 + terminal_growth) ] / (wacc - terminal_growth)
    PV(TV) = TV_N / (1 + wacc)^N
    Equity Value = PV(FCF) + PV(TV) - Net Debt
    Price_model(g) = Equity Value / shares_outstanding
    """
    if current_price <= 0 or shares_outstanding <= 0:
        return {"error": "Invalid current price or shares outstanding."}

    # If current FCF is negative or zero, use a normalized FCF baseline
    if current_fcf <= 0:
        return {
            "error": "FCF ติดลบหรือเป็นศูนย์ ไม่สามารถทำ Standard Reverse DCF ได้โดยตรง ต้องใช้ Multiple Valuation แทน",
            "implied_growth_pct": None,
            "is_unprofitable": True,
        }

    market_cap = current_price * shares_outstanding
    target_equity_value = market_cap

    def _calc_equity_value(growth_rate: float) -> float:
        pv_fcf = 0.0
        fcf_t = current_fcf
        for t in range(1, forecast_years + 1):
            fcf_t *= 1.0 + growth_rate
            discount_factor = (1.0 + wacc) ** t
            pv_fcf += fcf_t / discount_factor

        # Terminal Value
        tv = (fcf_t * (1.0 + terminal_growth)) / max(wacc - terminal_growth, 0.01)
        pv_tv = tv / ((1.0 + wacc) ** forecast_years)

        enterprise_val = pv_fcf + pv_tv
        equity_val = enterprise_val - net_debt
        return equity_val

    # Bisection bounds: growth between -40% (-0.40) and +150% (1.50)
    low_g = -0.40
    high_g = 1.50
    implied_g = None

    for _ in range(40):
        mid_g = (low_g + high_g) / 2.0
        eq_val = _calc_equity_value(mid_g)
        diff = eq_val - target_equity_value

        if abs(diff) / target_equity_value < 1e-4:
            implied_g = mid_g
            break

        if diff < 0:
            low_g = mid_g
        else:
            high_g = mid_g
    else:
        implied_g = (low_g + high_g) / 2.0

    # Interpret implied growth
    implied_pct = round(implied_g * 100, 2)
    if implied_pct > 30.0:
        sentiment = "Extreme Optimism (ราคาตั้งความหวังสูงมาก)"
        reality_check = (
            f"ตลาดกำลังตั้งสมมติฐานว่าบริษัทต้องขยายกระแสเงินสดอิสระ (FCF) เติบโตเฉลี่ยถึง {implied_pct}% ต่อปี "
            f"ติดต่อกัน 10 ปี ซึ่งเป็นอัตราที่สูงกว่าบริษัทชั้นนำส่วนใหญ่ในประวัติศาสตร์ "
            f"หากการเติบโตชะลอตัวแม้เพียงเล็กน้อย หุ้นมีความเสี่ยงที่จะถูก De-rating ปรับลด P/E ลงอย่างแรง"
        )
    elif implied_pct > 18.0:
        sentiment = "High Growth Priced In (สะท้อนการเติบโตระดับผู้นำอุตสาหกรรม)"
        reality_check = (
            f"ตลาดคาดหวัง FCF Growth เฉลี่ย {implied_pct}% ต่อปี เป็นเวลา 10 ปี "
            f"ต้องการความแข็งแกร่งของ Moat และการเติบโตของอุตสาหกรรมอย่างต่อเนื่องเพื่อสนับสนุนราคานี้"
        )
    elif implied_pct > 8.0:
        sentiment = "Moderate / Reasonable (สะท้อนการเติบโตสมเหตุสมผล)"
        reality_check = (
            f"ตลาดคาดหวัง FCF Growth เฉลี่ย {implied_pct}% ต่อปี เป็นอัตราที่เป็นไปได้สำหรับบริษัทที่มีคุณภาพดีและมีกระแสเงินสดสม่ำเสมอ"
        )
    else:
        sentiment = "Pessimistic / Turnaround (ตลาดมองแง่ลบมาก หรือถูกกดดันจากวัฏจักร)"
        reality_check = (
            f"ตลาดคาดหวังการเติบโตเพียง {implied_pct}% ต่อปี หรือแทบไม่โตเลย "
            f"หากบริษัทสามารถรักษาระดับกำไรหรือพลิกฟื้นได้ หุ้นจะมี Margin of Safety สูง"
        )

    # Calculate Scenarios
    # Bear scenario: 50% of implied or 5%
    g_bear = max(0.04, implied_g * 0.5)
    p_bear = max(0.1, _calc_equity_value(g_bear) / shares_outstanding)

    # Base scenario: reasonable target (e.g. 12-15% or 75% of implied if hypergrowth)
    g_base = min(0.15, max(0.08, implied_g * 0.75))
    p_base = max(0.1, _calc_equity_value(g_base) / shares_outstanding)

    # Bull scenario: 25% or 120% of implied
    g_bull = min(0.35, max(0.18, implied_g * 1.2))
    p_bull = max(0.1, _calc_equity_value(g_bull) / shares_outstanding)

    margin_of_safety_pct = round(((p_base - current_price) / current_price) * 100, 1)

    return {
        "current_price": round(current_price, 2),
        "shares_outstanding": shares_outstanding,
        "current_fcf": current_fcf,
        "net_debt": net_debt,
        "wacc_pct": round(wacc * 100, 1),
        "terminal_growth_pct": round(terminal_growth * 100, 1),
        "implied_fcf_growth_pct": implied_pct,
        "market_sentiment": sentiment,
        "reality_check": reality_check,
        "scenarios": {
            "bear": {
                "assumed_growth_pct": round(g_bear * 100, 1),
                "target_price": round(p_bear, 2),
                "upside_downside_pct": round(((p_bear - current_price) / current_price) * 100, 1),
            },
            "base": {
                "assumed_growth_pct": round(g_base * 100, 1),
                "target_price": round(p_base, 2),
                "upside_downside_pct": round(((p_base - current_price) / current_price) * 100, 1),
            },
            "bull": {
                "assumed_growth_pct": round(g_bull * 100, 1),
                "target_price": round(p_bull, 2),
                "upside_downside_pct": round(((p_bull - current_price) / current_price) * 100, 1),
            },
        },
        "margin_of_safety_pct": margin_of_safety_pct,
    }
