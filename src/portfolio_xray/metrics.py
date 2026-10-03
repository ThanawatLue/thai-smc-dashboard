"""
Quantitative metrics engine for Portfolio X-Ray.
Calculates look-through exposure, overlap matrix, concentration (HHI),
and risk-return metrics (CAGR, Volatility, Drawdown with currency loss, Sharpe, Sortino, Calmar).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import yfinance as yf

from src.portfolio_xray.holdings_data import get_asset_holdings, get_asset_metadata

logger = logging.getLogger(__name__)


def calculate_look_through(assets: List[dict]) -> dict:
    """
    Decomposes ETF holdings to compute true aggregate underlying exposure.
    
    Formula:
    Effective Exposure W_k = sum_i (w_i * h_{i,k})
    """
    effective_map: Dict[str, float] = {}
    direct_stocks: Dict[str, float] = {}
    etf_contributions: Dict[str, List[dict]] = {}

    for asset in assets:
        sym = asset["symbol"]
        weight = float(asset.get("weight", 0.0))
        if weight <= 0:
            continue

        holdings = get_asset_holdings(sym)
        is_etf = len(holdings) > 1 or "_OTHER" in holdings

        if not is_etf:
            direct_stocks[sym] = weight

        for h_sym, h_weight in holdings.items():
            eff_w = weight * h_weight
            effective_map[h_sym] = effective_map.get(h_sym, 0.0) + eff_w

            if h_sym not in etf_contributions:
                etf_contributions[h_sym] = []
            etf_contributions[h_sym].append({
                "source": sym,
                "source_weight": weight,
                "holding_in_source": h_weight,
                "contribution": eff_w,
            })

    # Sort holdings descending
    sorted_holdings = sorted(
        effective_map.items(), key=lambda x: x[1], reverse=True
    )

    top_holdings = []
    other_weight = 0.0
    for sym, w in sorted_holdings:
        if sym == "_OTHER":
            other_weight += w
            continue
        top_holdings.append({
            "symbol": sym,
            "effective_weight": round(w, 4),
            "effective_pct": round(w * 100, 2),
            "sources": etf_contributions.get(sym, []),
        })

    # Calculate Big Tech aggregate exposure
    big_tech_symbols = {"NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO"}
    big_tech_exposure = sum(
        effective_map.get(s, 0.0) for s in big_tech_symbols
    )

    # Generate insights
    insights = []
    if top_holdings and top_holdings[0]["effective_pct"] > 10.0:
        top_sym = top_holdings[0]["symbol"]
        top_pct = top_holdings[0]["effective_pct"]
        insights.append(
            f"หุ้นเดี่ยวที่มีสัดส่วนสูงสุดคือ {top_sym} ({top_pct}%) ซึ่งอาจเกิดจากการถือซ้ำในหลาย ETF"
        )

    if big_tech_exposure > 0.25:
        insights.append(
            f"พอร์ตนี้มีน้ำหนักในกลุ่ม US Mega-Cap Tech รวมกันถึง {round(big_tech_exposure * 100, 1)}% "
            f"ส่งผลให้ผลตอบแทนจะขึ้นลงตามทิศทางกลุ่มเทคโนโลยีขนาดใหญ่เป็นหลัก"
        )

    return {
        "top_holdings": top_holdings[:15],
        "other_etf_diffused_pct": round(other_weight * 100, 2),
        "big_tech_exposure_pct": round(big_tech_exposure * 100, 2),
        "total_unique_holdings": len(effective_map),
        "insights": insights,
    }


def calculate_overlap_matrix(tickers: List[str]) -> dict:
    """
    Computes pairwise holding overlap coefficient between assets:
    Overlap(A, B) = sum_k min(h_{A,k}, h_{B,k})
    """
    n = len(tickers)
    matrix = np.zeros((n, n))
    holdings_dict = {t: get_asset_holdings(t) for t in tickers}
    redundant_pairs = []

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0
                continue
            sym_a = tickers[i]
            sym_b = tickers[j]
            h_a = holdings_dict[sym_a]
            h_b = holdings_dict[sym_b]

            # Common keys excluding generic _OTHER
            common_keys = set(h_a.keys()) & set(h_b.keys())
            common_keys.discard("_OTHER")

            overlap_val = sum(min(h_a[k], h_b[k]) for k in common_keys)
            matrix[i][j] = round(overlap_val, 4)

            # Record high overlap pairs (i < j to avoid duplicate)
            if i < j and overlap_val >= 0.25:
                # Find top shared stocks
                shared_stocks = sorted(
                    [(k, min(h_a[k], h_b[k])) for k in common_keys],
                    key=lambda x: x[1],
                    reverse=True,
                )[:3]
                shared_str = ", ".join([f"{k} ({round(w * 100, 1)}%)" for k, w in shared_stocks])
                redundant_pairs.append({
                    "asset_a": sym_a,
                    "asset_b": sym_b,
                    "overlap_pct": round(overlap_val * 100, 1),
                    "shared_stocks": shared_str,
                    "severity": "HIGH" if overlap_val >= 0.40 else "MODERATE",
                    "explanation": (
                        f"{sym_a} และ {sym_b} มีสินทรัพย์ทับซ้อนกัน {round(overlap_val * 100, 1)}% "
                        f"(หุ้นร่วมหลัก: {shared_str}) การถือทั้งสองตัวทำให้เกิดการลงทุนซ้ำซ้อน ไม่ได้กระจายความเสี่ยงอย่างแท้จริง"
                    ),
                })

    return {
        "tickers": tickers,
        "matrix": matrix.tolist(),
        "redundant_pairs": redundant_pairs,
    }


def calculate_concentration(
    stated_assets: List[dict], look_through_holdings: List[dict]
) -> dict:
    """
    Calculates Herfindahl-Hirschman Index (HHI) and Effective Number of Bets.
    HHI = sum(w_i^2)
    N_eff = 1 / HHI
    """
    # 1. Stated Weights HHI
    stated_weights = [a["weight"] for a in stated_assets if a.get("weight", 0) > 0]
    total_sw = sum(stated_weights) or 1.0
    norm_sw = [w / total_sw for w in stated_weights]
    stated_hhi = sum(w**2 for w in norm_sw)
    stated_n_eff = round(1.0 / stated_hhi, 1) if stated_hhi > 0 else len(stated_assets)

    # 2. Look-Through Effective HHI
    eff_weights = [h["effective_weight"] for h in look_through_holdings]
    total_ew = sum(eff_weights) or 1.0
    norm_ew = [w / total_ew for w in eff_weights]
    eff_hhi = sum(w**2 for w in norm_ew)
    eff_n_eff = round(1.0 / eff_hhi, 1) if eff_hhi > 0 else len(look_through_holdings)

    # Stated Top 3 / Top 5
    sorted_stated = sorted(norm_sw, reverse=True)
    top3_pct = round(sum(sorted_stated[:3]) * 100, 1)
    top5_pct = round(sum(sorted_stated[:5]) * 100, 1)

    # Qualitative verdict
    if stated_hhi > 0.30:
        verdict = "กระจุกตัวสูงมาก (Highly Concentrated)"
        desc = "พอร์ตพึ่งพาผลตอบแทนจากสินทรัพย์เพียง 1-2 ตัวเป็นหลัก หากเกิดความผิดพลาดจะกระทบพอร์ตโดยรวมอย่างรุนแรง"
    elif stated_hhi > 0.18:
        verdict = "กระจุกตัวปานกลาง (Moderately Concentrated)"
        desc = "พอร์ตมีความสมดุลระหว่างการเก็งกำไรเฉพาะตัวและการกระจายความเสี่ยง"
    else:
        verdict = "กระจายตัวดี (Well Diversified)"
        desc = "พอร์ตไม่มีการพึ่งพาสินทรัพย์ใดสินทรัพย์หนึ่งเกินขนาด ความเสี่ยงเฉพาะตัวค่อนข้างต่ำ"

    return {
        "stated_hhi": round(stated_hhi, 4),
        "stated_effective_positions": stated_n_eff,
        "effective_hhi": round(eff_hhi, 4),
        "effective_positions": eff_n_eff,
        "top3_weight_pct": top3_pct,
        "top5_weight_pct": top5_pct,
        "verdict": verdict,
        "description": desc,
    }


def calculate_risk_return(
    tickers: List[str],
    weights: List[float],
    portfolio_value: float = 1_000_000,
    currency: str = "THB",
    period: str = "3y",
    benchmark_symbol: str = "VOO",
) -> dict:
    """
    Downloads total return adjusted prices, resamples weekly,
    and computes CAGR, Volatility, Max Drawdown (with real money loss),
    Sharpe, Sortino, Calmar, and Correlation Matrix.
    """
    symbols_to_fetch = list(dict.fromkeys(tickers + [benchmark_symbol]))

    try:
        raw_df = yf.download(
            symbols_to_fetch,
            period=period,
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"yfinance download failed: {e}")
        return {"error": f"Failed to download market data: {e}"}

    # Extract Close series
    if "Close" in raw_df.columns:
        close_df = raw_df["Close"]
    else:
        close_df = raw_df

    # If single symbol, close_df is Series; convert to DataFrame
    if isinstance(close_df, pd.Series):
        close_df = close_df.to_frame(name=symbols_to_fetch[0])

    # Resample weekly on Friday to align Crypto and Equities
    weekly_df = close_df.resample("W-FRI").last().ffill().dropna()

    if weekly_df.empty or len(weekly_df) < 8:
        return {
            "error": "ข้อมูลราคาย้อนหลังมีไม่เพียงพอสำหรับการคำนวณทางสถิติ (ต้องการอย่างน้อย 8 สัปดาห์)"
        }

    # Weekly returns
    returns_df = weekly_df.pct_change().dropna()

    # Portfolio return calculation
    # Normalize weights for available tickers
    avail_tickers = [t for t in tickers if t in returns_df.columns]
    if not avail_tickers:
        return {"error": "ไม่พบข้อมูลราคาของสินทรัพย์ในพอร์ต"}

    avail_weights = []
    for t in avail_tickers:
        idx = tickers.index(t)
        avail_weights.append(weights[idx])

    sum_w = sum(avail_weights) or 1.0
    norm_w = np.array([w / sum_w for w in avail_weights])

    port_returns = returns_df[avail_tickers].dot(norm_w)
    bench_returns = (
        returns_df[benchmark_symbol]
        if benchmark_symbol in returns_df.columns
        else port_returns
    )

    # Compute stats helper
    def _compute_stats(r_series: pd.Series) -> dict:
        n_weeks = len(r_series)
        years = n_weeks / 52.0

        # Cumulative wealth index
        wealth = (1.0 + r_series).cumprod()
        total_return = wealth.iloc[-1] - 1.0

        # CAGR
        cagr = (wealth.iloc[-1]) ** (1.0 / max(years, 0.1)) - 1.0

        # Annualized Volatility
        ann_vol = r_series.std() * np.sqrt(52)

        # Max Drawdown
        running_max = wealth.cummax()
        drawdown_series = (wealth - running_max) / running_max
        max_dd = float(drawdown_series.min())

        # Drawdown Duration and Recovery Time
        dd_trough_idx = drawdown_series.idxmin()
        peak_before = wealth.loc[:dd_trough_idx].idxmax()
        recovered_df = wealth.loc[dd_trough_idx:][wealth.loc[dd_trough_idx:] >= wealth.loc[peak_before]]
        if not recovered_df.empty:
            recovery_idx = recovered_df.index[0]
            recovery_weeks = len(wealth.loc[dd_trough_idx:recovery_idx])
            recovery_text = f"{recovery_weeks} สัปดาห์ (ฟื้นตัวกลับสู่จุดเดิมแล้ว)"
        else:
            recovery_text = "ยังไม่ฟื้นตัวสู่จุดสูงสุดเดิม"

        # Risk-free rate assumed 4.0% annualized
        rf_weekly = 0.04 / 52.0
        excess_returns = r_series - rf_weekly

        # Sharpe
        sharpe = (
            float((excess_returns.mean() / (r_series.std() or 1e-6)) * np.sqrt(52))
            if r_series.std() > 0
            else 0.0
        )

        # Sortino (downside volatility)
        downside_returns = r_series[r_series < rf_weekly] - rf_weekly
        downside_std = downside_returns.std() if len(downside_returns) > 1 else 1e-6
        sortino = (
            float((excess_returns.mean() / (downside_std or 1e-6)) * np.sqrt(52))
            if downside_std > 0
            else 0.0
        )

        # Calmar
        calmar = float(cagr / abs(max_dd)) if abs(max_dd) > 1e-4 else 0.0

        # Real money translation
        cash_loss = portfolio_value * abs(max_dd)
        min_portfolio_val = portfolio_value * (1.0 - abs(max_dd))

        return {
            "total_return_pct": round(total_return * 100, 2),
            "cagr_pct": round(cagr * 100, 2),
            "annualized_volatility_pct": round(ann_vol * 100, 2),
            "max_drawdown_pct": round(max_dd * 100, 2),
            "real_cash_loss": round(cash_loss, 2),
            "lowest_portfolio_value": round(min_portfolio_val, 2),
            "recovery_time": recovery_text,
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "dates": [d.strftime("%Y-%m-%d") for d in wealth.index],
            "wealth_index": [round(float(v), 4) for v in wealth.values],
            "drawdown_curve": [round(float(v) * 100, 2) for v in drawdown_series.values],
        }

    port_stats = _compute_stats(port_returns)
    bench_stats = _compute_stats(bench_returns)

    # Correlation Matrix
    corr_subset = [t for t in tickers if t in returns_df.columns]
    if benchmark_symbol in returns_df.columns and benchmark_symbol not in corr_subset:
        corr_subset.append(benchmark_symbol)

    corr_df = returns_df[corr_subset].corr()
    corr_matrix = corr_df.round(3).values.tolist()

    return {
        "period": period,
        "sample_weeks": len(returns_df),
        "start_date": returns_df.index[0].strftime("%Y-%m-%d"),
        "end_date": returns_df.index[-1].strftime("%Y-%m-%d"),
        "portfolio": port_stats,
        "benchmark": bench_stats,
        "benchmark_symbol": benchmark_symbol,
        "portfolio_value": portfolio_value,
        "currency": currency,
        "correlation": {
            "tickers": corr_subset,
            "matrix": corr_matrix,
        },
    }
