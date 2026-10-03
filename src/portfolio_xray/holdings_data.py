"""
Holdings database and classification engine for ETFs and assets.
Combines curated institutional ETF holdings with live yfinance fallback and caching.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional
import yfinance as yf

logger = logging.getLogger(__name__)

# Curated Top Holdings for major institutional ETFs (% in decimal form 0.0 - 1.0)
CURATED_ETF_HOLDINGS: Dict[str, Dict[str, float]] = {
    # S&P 500 ETFs
    "VOO": {
        "NVDA": 0.0808,
        "AAPL": 0.0703,
        "MSFT": 0.0570,
        "AMZN": 0.0384,
        "GOOGL": 0.0301,
        "AVGO": 0.0265,
        "GOOG": 0.0240,
        "META": 0.0190,
        "MU": 0.0163,
        "TSLA": 0.0157,
        "BRK.B": 0.0152,
        "JPM": 0.0135,
        "LLY": 0.0125,
        "_OTHER": 0.5907,
    },
    "SPY": {
        "NVDA": 0.0808,
        "AAPL": 0.0703,
        "MSFT": 0.0570,
        "AMZN": 0.0384,
        "GOOGL": 0.0301,
        "AVGO": 0.0265,
        "GOOG": 0.0240,
        "META": 0.0190,
        "MU": 0.0163,
        "TSLA": 0.0157,
        "BRK.B": 0.0152,
        "JPM": 0.0135,
        "LLY": 0.0125,
        "_OTHER": 0.5907,
    },
    "IVV": {
        "NVDA": 0.0808,
        "AAPL": 0.0703,
        "MSFT": 0.0570,
        "AMZN": 0.0384,
        "GOOGL": 0.0301,
        "AVGO": 0.0265,
        "GOOG": 0.0240,
        "META": 0.0190,
        "MU": 0.0163,
        "TSLA": 0.0157,
        "BRK.B": 0.0152,
        "JPM": 0.0135,
        "LLY": 0.0125,
        "_OTHER": 0.5907,
    },
    # Nasdaq-100 ETFs
    "QQQ": {
        "NVDA": 0.0890,
        "AAPL": 0.0870,
        "MSFT": 0.0810,
        "AMZN": 0.0540,
        "AVGO": 0.0480,
        "META": 0.0460,
        "GOOGL": 0.0310,
        "GOOG": 0.0290,
        "TSLA": 0.0270,
        "COST": 0.0240,
        "AMD": 0.0210,
        "NFLX": 0.0190,
        "_OTHER": 0.4740,
    },
    "QQQM": {
        "NVDA": 0.0890,
        "AAPL": 0.0870,
        "MSFT": 0.0810,
        "AMZN": 0.0540,
        "AVGO": 0.0480,
        "META": 0.0460,
        "GOOGL": 0.0310,
        "GOOG": 0.0290,
        "TSLA": 0.0270,
        "COST": 0.0240,
        "AMD": 0.0210,
        "NFLX": 0.0190,
        "_OTHER": 0.4740,
    },
    # Dividend Quality ETF
    "SCHD": {
        "LMT": 0.0435,
        "CSCO": 0.0425,
        "TXN": 0.0415,
        "ABBV": 0.0405,
        "AMGN": 0.0395,
        "HD": 0.0385,
        "PFE": 0.0375,
        "MRK": 0.0365,
        "CVX": 0.0355,
        "PEP": 0.0345,
        "KO": 0.0335,
        "VZ": 0.0325,
        "_OTHER": 0.4440,
    },
    # Semiconductor ETF
    "SMH": {
        "NVDA": 0.2050,
        "TSM": 0.1320,
        "AVGO": 0.0760,
        "ASML": 0.0560,
        "QCOM": 0.0490,
        "AMD": 0.0460,
        "TXN": 0.0420,
        "AMAT": 0.0400,
        "MU": 0.0380,
        "LRCX": 0.0350,
        "ADI": 0.0310,
        "INTC": 0.0280,
        "_OTHER": 0.2230,
    },
    # Total US Stock Market
    "VTI": {
        "NVDA": 0.0680,
        "AAPL": 0.0590,
        "MSFT": 0.0480,
        "AMZN": 0.0320,
        "GOOGL": 0.0250,
        "AVGO": 0.0220,
        "META": 0.0160,
        "TSLA": 0.0130,
        "BRK.B": 0.0130,
        "JPM": 0.0110,
        "_OTHER": 0.6930,
    },
    # Total World Stock Market
    "VT": {
        "NVDA": 0.0450,
        "AAPL": 0.0390,
        "MSFT": 0.0320,
        "AMZN": 0.0210,
        "GOOGL": 0.0170,
        "AVGO": 0.0150,
        "META": 0.0110,
        "TSM": 0.0090,
        "TSLA": 0.0090,
        "BRK.B": 0.0080,
        "_OTHER": 0.7940,
    },
    # Fixed Income / Treasuries
    "TLT": {
        "US_TREASURY_20Y_PLUS": 1.0000,
    },
    "BND": {
        "US_TREASURY_CORP_BOND": 1.0000,
    },
    "BIL": {
        "US_TBILL_1_3M": 1.0000,
    },
    # Commodities
    "GLD": {
        "GOLD_BULLION": 1.0000,
    },
    "IAU": {
        "GOLD_BULLION": 1.0000,
    },
    # Real Estate
    "VNQ": {
        "PLD": 0.0750,
        "AMT": 0.0620,
        "EQIX": 0.0580,
        "WELL": 0.0420,
        "SPG": 0.0390,
        "DLR": 0.0350,
        "O": 0.0320,
        "_OTHER": 0.6570,
    },
}

# Curated Asset Roles and Classification Metadata
ASSET_CLASSIFICATIONS: Dict[str, dict] = {
    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "asset_class": "US Large Cap Blend",
        "role": "CORE",
        "region": "US",
        "risk_driver": "US Equity Market Risk (Beta = 1.0)",
        "expense_ratio": 0.0003,
    },
    "SPY": {
        "name": "SPDR S&P 500 ETF Trust",
        "asset_class": "US Large Cap Blend",
        "role": "CORE",
        "region": "US",
        "risk_driver": "US Equity Market Risk (Beta = 1.0)",
        "expense_ratio": 0.0009,
    },
    "IVV": {
        "name": "iShares Core S&P 500 ETF",
        "asset_class": "US Large Cap Blend",
        "role": "CORE",
        "region": "US",
        "risk_driver": "US Equity Market Risk (Beta = 1.0)",
        "expense_ratio": 0.0003,
    },
    "QQQ": {
        "name": "Invesco QQQ Trust (Nasdaq 100)",
        "asset_class": "US Large Cap Growth",
        "role": "GROWTH / SATELLITE",
        "region": "US",
        "risk_driver": "Mega-Cap Tech / Multiples Compression",
        "expense_ratio": 0.0020,
    },
    "QQQM": {
        "name": "Invesco NASDAQ 100 ETF",
        "asset_class": "US Large Cap Growth",
        "role": "GROWTH / SATELLITE",
        "region": "US",
        "risk_driver": "Mega-Cap Tech / Multiples Compression",
        "expense_ratio": 0.0015,
    },
    "SCHD": {
        "name": "Schwab U.S. Dividend Equity ETF",
        "asset_class": "US Large Cap Value / Dividend",
        "role": "INCOME / CORE VALUE",
        "region": "US",
        "risk_driver": "Economic Cycle / Quality Value Factor",
        "expense_ratio": 0.0006,
    },
    "SMH": {
        "name": "VanEck Semiconductor ETF",
        "asset_class": "Sector / Semiconductor",
        "role": "SATELLITE / HIGH GROWTH",
        "region": "US & Global",
        "risk_driver": "Semiconductor Capex / AI Hardware Cycle",
        "expense_ratio": 0.0035,
    },
    "VTI": {
        "name": "Vanguard Total Stock Market ETF",
        "asset_class": "US Total Market Blend",
        "role": "CORE",
        "region": "US",
        "risk_driver": "Broad US Equity Market",
        "expense_ratio": 0.0003,
    },
    "VT": {
        "name": "Vanguard Total World Stock ETF",
        "asset_class": "Global Equity Blend",
        "role": "GLOBAL CORE",
        "region": "Global",
        "risk_driver": "Global Economic Growth & FX",
        "expense_ratio": 0.0007,
    },
    "TLT": {
        "name": "iShares 20+ Year Treasury Bond ETF",
        "asset_class": "US Long-Term Government Bond",
        "role": "HEDGE / DURATION",
        "region": "US",
        "risk_driver": "Interest Rate Sensitivity (Duration ~16 yrs)",
        "expense_ratio": 0.0015,
    },
    "GLD": {
        "name": "SPDR Gold Shares",
        "asset_class": "Commodity / Precious Metals",
        "role": "HEDGE / STORE OF VALUE",
        "region": "Global",
        "risk_driver": "Real Yields / Fiat Debasement / Geopolitics",
        "expense_ratio": 0.0040,
    },
    "IAU": {
        "name": "iShares Gold Trust",
        "asset_class": "Commodity / Precious Metals",
        "role": "HEDGE / STORE OF VALUE",
        "region": "Global",
        "risk_driver": "Real Yields / Fiat Debasement / Geopolitics",
        "expense_ratio": 0.0025,
    },
    "VNQ": {
        "name": "Vanguard Real Estate ETF",
        "asset_class": "Real Estate / REITs",
        "role": "INCOME / REAL ASSETS",
        "region": "US",
        "risk_driver": "Cap Rates / Commercial Real Estate Debt",
        "expense_ratio": 0.0012,
    },
    "BTC-USD": {
        "name": "Bitcoin",
        "asset_class": "Digital Asset / Crypto",
        "role": "SPECULATIVE / ASYMMETRIC",
        "region": "Global",
        "risk_driver": "Crypto Liquidity / Adoption / Regulatory",
        "expense_ratio": 0.0,
    },
    "ETH-USD": {
        "name": "Ethereum",
        "asset_class": "Digital Asset / Smart Contracts",
        "role": "SPECULATIVE / ASYMMETRIC",
        "region": "Global",
        "risk_driver": "DeFi Activity / Crypto Liquidity / Gas Fees",
        "expense_ratio": 0.0,
    },
}

# In-memory cache for live fetched holdings & metadata
_CACHE_HOLDINGS: Dict[str, Dict[str, float]] = {}
_CACHE_METADATA: Dict[str, dict] = {}


def get_asset_holdings(symbol: str) -> Dict[str, float]:
    """
    Returns breakdown of underlying holdings for an asset or ETF.
    If the asset is an ETF, returns a dict of {holding_ticker: weight_fraction}.
    If the asset is a single stock or commodity/crypto, returns {symbol: 1.0}.
    """
    clean_sym = symbol.strip().upper()

    # Check cache first
    if clean_sym in _CACHE_HOLDINGS:
        return _CACHE_HOLDINGS[clean_sym]

    # Check curated ETF holdings
    if clean_sym in CURATED_ETF_HOLDINGS:
        _CACHE_HOLDINGS[clean_sym] = CURATED_ETF_HOLDINGS[clean_sym]
        return CURATED_ETF_HOLDINGS[clean_sym]

    # Fallback to yfinance funds_data
    try:
        t = yf.Ticker(clean_sym)
        funds_data = getattr(t, "funds_data", None)
        if funds_data is not None:
            top_df = getattr(funds_data, "top_holdings", None)
            if top_df is not None and not top_df.empty:
                holdings = {}
                total_w = 0.0
                for h_sym, row in top_df.iterrows():
                    sym_code = str(h_sym).strip().upper()
                    # Handle holding percent column
                    pct_val = float(row.get("Holding Percent", 0.0) or 0.0)
                    if pct_val > 0:
                        holdings[sym_code] = pct_val
                        total_w += pct_val

                if total_w < 1.0:
                    holdings["_OTHER"] = max(0.0, 1.0 - total_w)

                if holdings:
                    _CACHE_HOLDINGS[clean_sym] = holdings
                    return holdings
    except Exception as e:
        logger.debug(f"Failed to fetch live ETF holdings for {clean_sym}: {e}")

    # Single asset fallback
    single_holding = {clean_sym: 1.0}
    _CACHE_HOLDINGS[clean_sym] = single_holding
    return single_holding


def get_asset_metadata(symbol: str) -> dict:
    """
    Returns asset classification, role, style, and fund metrics.
    """
    clean_sym = symbol.strip().upper()

    # Check cache
    if clean_sym in _CACHE_METADATA:
        return _CACHE_METADATA[clean_sym]

    # Check curated database
    if clean_sym in ASSET_CLASSIFICATIONS:
        meta = dict(ASSET_CLASSIFICATIONS[clean_sym])
        meta["symbol"] = clean_sym
        _CACHE_METADATA[clean_sym] = meta
        return meta

    # Query live yfinance info
    try:
        t = yf.Ticker(clean_sym)
        info = t.info or {}
        qtype = info.get("quoteType", "EQUITY")
        name = info.get("longName") or info.get("shortName") or clean_sym
        category = info.get("category") or info.get("sector") or "General"
        expense = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio") or 0.0
        div_yield = info.get("yield") or info.get("dividendYield") or 0.0

        if qtype == "ETF":
            role = "CORE" if "Blend" in category or "500" in name else "SATELLITE"
            asset_class = f"ETF ({category})"
            risk_driver = f"Underlying {category} Basket Risk"
        elif qtype == "CRYPTOCURRENCY":
            role = "SPECULATIVE / ASYMMETRIC"
            asset_class = "Digital Asset / Crypto"
            risk_driver = "Crypto Market Sentiment & Volatility"
            expense = 0.0
        else:
            role = "SINGLE STOCK / HIGH CONVICTION"
            asset_class = f"Equity ({category})"
            risk_driver = f"{category} Sector & Company Specific Execution Risk"

        meta = {
            "symbol": clean_sym,
            "name": name,
            "asset_class": asset_class,
            "role": role,
            "region": "US" if not clean_sym.endswith("-USD") else "Global",
            "risk_driver": risk_driver,
            "expense_ratio": round(float(expense), 4),
            "dividend_yield": round(float(div_yield), 4),
            "quote_type": qtype,
        }
        _CACHE_METADATA[clean_sym] = meta
        return meta
    except Exception as e:
        logger.debug(f"Failed to fetch live metadata for {clean_sym}: {e}")
        fallback_meta = {
            "symbol": clean_sym,
            "name": clean_sym,
            "asset_class": "Equity / Asset",
            "role": "CORE / SATELLITE",
            "region": "US",
            "risk_driver": "Market & Sector Risk",
            "expense_ratio": 0.0,
            "dividend_yield": 0.0,
            "quote_type": "EQUITY",
        }
        _CACHE_METADATA[clean_sym] = fallback_meta
        return fallback_meta
