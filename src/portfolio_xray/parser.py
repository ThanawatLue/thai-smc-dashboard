"""
Smart input parser for Portfolio X-Ray and Deep Thesis modes.
Accepts free-form ticker strings with or without weights.
"""

from __future__ import annotations

import re

# Crypto tickers that map to Yahoo Finance tickers
CRYPTO_MAP = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "BNB": "BNB-USD",
    "XRP": "XRP-USD",
    "ADA": "ADA-USD",
    "DOGE": "DOGE-USD",
    "AVAX": "AVAX-USD",
}

# Common noise words in user queries that should not be parsed as tickers
STOP_WORDS = {
    "ทำ", "ช่วย", "วิเคราะห์", "พอร์ต", "ให้", "หน่อย", "และ", "กับ", "ขอ",
    "THESIS", "DEEP", "REVERSE", "DCF", "HTML", "DASHBOARD", "PORTFOLIO",
    "XRAY", "X-RAY", "ANALYSIS", "PLUS", "WITH", "FOR", "AND"
}


def normalize_symbol(symbol: str) -> str:
    """Normalizes ticker symbol, mapping common crypto abbreviations."""
    clean = symbol.strip().upper().replace("$", "")
    return CRYPTO_MAP.get(clean, clean)


def parse_portfolio_input(raw_text: str) -> dict:
    """
    Parses flexible portfolio input text.
    
    Supports:
    - Weighted with %: 'VOO 35% QQQM 20% SCHD 15% GLD 10% TLT 10% BTC 10%'
    - Weighted with numbers: 'VOO 35 QQQM 20 SCHD 15'
    - Colon/comma format: 'VOO: 40%, QQQM: 30%, SCHD: 30%'
    - Unweighted list: 'VOO QQQM SCHD GLD TLT BTC' or 'VOO, QQQM, SCHD' (Equal weight)
    - Single asset: 'NVDA' or 'RKLB ทำ Deep Thesis'
    """
    text = raw_text.strip()
    if not text:
        return {
            "mode": "portfolio",
            "assets": [],
            "tickers": [],
            "is_equal_weight": False,
            "equal_weight_warning": None,
            "raw_input": text,
        }

    # 1. Clean lines and extract tokens
    # Remove obvious prompt commands while preserving tickers
    tokens = re.findall(r"[A-Za-z0-9\.\-\=\:]+|[0-9]+(?:\.[0-9]+)?%?", text)

    # 2. Try parsing pairs of (Ticker, Weight)
    # Match patterns like "TICKER 35%" or "TICKER: 35" or "TICKER 35.5"
    pair_pattern = re.compile(
        r"([A-Za-z0-9\.\-\=]+)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)\s*%", re.IGNORECASE
    )
    matches = pair_pattern.findall(text)

    # If no % sign, try "TICKER [:=] NUMBER"
    if not matches:
        pair_num_pattern = re.compile(
            r"([A-Za-z]{1,6}(?:-[A-Za-z]+)?)\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)(?:\s+|$|,)",
            re.IGNORECASE,
        )
        matches = pair_num_pattern.findall(text)

    assets = []
    is_equal_weight = False

    if matches:
        total_raw_weight = 0.0
        parsed_items = []
        for sym, w_str in matches:
            sym_clean = sym.strip().upper()
            if sym_clean in STOP_WORDS or not sym_clean.replace(".", "").replace("-", "").isalpha():
                continue
            try:
                w_val = float(w_str)
                if w_val > 0:
                    parsed_items.append((normalize_symbol(sym_clean), w_val))
                    total_raw_weight += w_val
            except ValueError:
                continue

        if parsed_items and total_raw_weight > 0:
            for sym_norm, w_val in parsed_items:
                normalized_w = w_val / total_raw_weight
                assets.append({
                    "symbol": sym_norm,
                    "weight": round(normalized_w, 4),
                    "weight_pct": round(normalized_w * 100, 2),
                })

    # 3. If no weights found, treat as unweighted list of tickers
    if not assets:
        raw_words = re.split(r"[\s,;\n\r]+", text)
        tickers = []
        for word in raw_words:
            w_clean = word.strip().upper().replace("$", "")
            if not w_clean or w_clean in STOP_WORDS:
                continue
            # Basic validation of ticker format (e.g. AAPL, BRK.B, BTC-USD, GC=F)
            if re.match(r"^[A-Z0-9\.\-\=]{1,10}$", w_clean) and not w_clean.isdigit():
                tickers.append(normalize_symbol(w_clean))

        # Deduplicate while preserving order
        unique_tickers = list(dict.fromkeys(tickers))

        if len(unique_tickers) == 1:
            # Single asset mode
            assets = [{
                "symbol": unique_tickers[0],
                "weight": 1.0,
                "weight_pct": 100.0,
            }]
        elif len(unique_tickers) > 1:
            # Equal weight
            is_equal_weight = True
            n = len(unique_tickers)
            equal_w = 1.0 / n
            for sym in unique_tickers:
                assets.append({
                    "symbol": sym,
                    "weight": round(equal_w, 4),
                    "weight_pct": round(equal_w * 100, 2),
                })

    mode = "single_stock" if len(assets) == 1 else "portfolio"
    warning = (
        "Illustrative Equal Weight — ไม่ใช่ Portfolio จริงของผู้ใช้"
        if (is_equal_weight and mode == "portfolio")
        else None
    )

    return {
        "mode": mode,
        "assets": assets,
        "tickers": [a["symbol"] for a in assets],
        "is_equal_weight": is_equal_weight,
        "equal_weight_warning": warning,
        "raw_input": raw_text,
    }
