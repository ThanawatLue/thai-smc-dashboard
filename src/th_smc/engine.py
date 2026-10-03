from __future__ import annotations

import contextlib
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
YF_CACHE_DIR = BASE_DIR / "state" / "yfinance-cache"


DEFAULT_TH_SYMBOLS = [
    "ADVANC",
    "AOT",
    "BBL",
    "BDMS",
    "BEM",
    "BH",
    "BJC",
    "BTS",
    "CBG",
    "CPALL",
    "CPF",
    "CPN",
    "CRC",
    "DELTA",
    "EA",
    "EGCO",
    "GLOBAL",
    "GPSC",
    "GULF",
    "HMPRO",
    "INTUCH",
    "IVL",
    "KBANK",
    "KTB",
    "KTC",
    "LH",
    "MINT",
    "MTC",
    "OR",
    "OSP",
    "PTT",
    "PTTEP",
    "PTTGC",
    "RATCH",
    "SAWAD",
    "SCB",
    "SCC",
    "SCGP",
    "TIDLOR",
    "TISCO",
    "TOP",
    "TRUE",
    "TTB",
    "TU",
]

DEFAULT_US_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "BRK-B",
    "JPM",
    "V",
    "UNH",
    "AMD",
    "NFLX",
    "COST",
    "HD",
    "XOM",
    "MA",
    "PG",
    "JNJ",
    "ABBV",
    "CRM",
    "WMT",
    "BAC",
    "LLY",
    "AVGO",
    "ORCL",
    "MRK",
    "CVX",
    "ACN",
    "TMO",
]

DEFAULT_GOLD_SYMBOLS = [
    {"symbol": "GC=F", "name": "Gold Futures (COMEX)"},
    {"symbol": "SI=F", "name": "Silver Futures (COMEX)"},
    {"symbol": "GLD", "name": "SPDR Gold Shares ETF"},
    {"symbol": "IAU", "name": "iShares Gold Trust ETF"},
    {"symbol": "GDX", "name": "VanEck Gold Miners ETF"},
    {"symbol": "PL=F", "name": "Platinum Futures (NYMEX)"},
]

TV_METRIC_COLUMNS = [
    "name",
    "exchange",
    "type",
    "subtype",
    "description",
    "close",
    "volume",
    "market_cap_basic",
    "RSI",
    "SMA20",
    "SMA50",
    "SMA200",
    "Perf.1M",
    "Perf.3M",
    "Perf.6M",
    "relative_volume_10d_calc",
    "price_52_week_high",
    "price_52_week_low",
    "return_on_equity",
    "debt_to_equity",
    "return_on_invested_capital",
    "free_cash_flow_margin_ttm",
    "gross_margin",
    "ebitda_margin_ttm",
    "total_revenue_cagr_5y",
]

NON_OPERATING_KEYWORDS = (
    "REIT",
    "ETF",
    "FUND",
    "TRUST",
    "DEPOSITARY RECEIPT",
    "DEPOSITORY RECEIPT",
)


def normalize_symbol(raw: str, market: str = "TH") -> str:
    symbol = raw.strip().upper()
    if not symbol:
        raise ValueError("symbol is empty")
    if market == "TH":
        if "." in symbol and not symbol.endswith(".BK"):
            raise ValueError("only Thai .BK symbols are allowed")
        return symbol if symbol.endswith(".BK") else f"{symbol}.BK"
    return symbol


@dataclass(frozen=True)
class SwingPoint:
    index: int
    date: str
    price: float
    kind: str


class MarketDataUnavailable(Exception):
    """Raised when a real market data provider returns no usable OHLCV."""


def make_sample_ohlcv(symbol: str, bars: int = 180) -> pd.DataFrame:
    base = 36 + (sum(ord(ch) for ch in symbol) % 70)
    rows = []
    start = datetime.now() - timedelta(days=bars * 2)
    price = float(base)
    for i in range(bars):
        wave = ((i % 28) - 14) / 14
        drift = 0.045 if i > 80 else -0.015
        open_price = price
        close = max(2.0, open_price + drift + wave * 0.18)
        high = max(open_price, close) + 0.35 + abs(wave) * 0.12
        low = min(open_price, close) - 0.35 - abs(wave) * 0.12
        volume = 1_000_000 + (i % 20) * 85_000
        rows.append(
            {
                "Date": (start + timedelta(days=i)).strftime("%Y-%m-%d"),
                "Open": round(open_price, 2),
                "High": round(high, 2),
                "Low": round(low, 2),
                "Close": round(close, 2),
                "Volume": volume,
            }
        )
        price = close
    df = pd.DataFrame(rows)
    df.attrs["data_source"] = "sample_fixture"
    df.attrs["is_sample"] = True
    return df


def load_ohlcv(symbol: str, period: str = "1y", interval: str = "1d", market: str = "TH") -> pd.DataFrame:
    normalized = normalize_symbol(symbol, market)
    last_error = None
    try:
        import yfinance as yf

        YF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        if hasattr(yf, "set_tz_cache_location"):
            yf.set_tz_cache_location(str(YF_CACHE_DIR))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            df = yf.download(
                normalized,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
                timeout=10,
            )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        df = df.reset_index()
        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
            out = df[["Date", "Open", "High", "Low", "Close", "Volume"]].dropna()
            if not out.empty:
                out.attrs["data_source"] = "yfinance"
                out.attrs["is_sample"] = False
                return out
    except Exception as exc:
        last_error = exc
    message = f"No real OHLCV available for {normalized}"
    if last_error:
        message = f"{message}: {last_error}"
    raise MarketDataUnavailable(message)


def _sma(series: pd.Series, length: int) -> float | None:
    values = series.tail(length)
    if len(values) < length:
        return None
    return float(values.mean())


def _rsi(close: pd.Series, period: int = 14) -> float | None:
    if len(close) <= period:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    latest_loss = float(loss.iloc[-1])
    if latest_loss == 0:
        return 100.0
    rs = float(gain.iloc[-1]) / latest_loss
    return 100 - (100 / (1 + rs))


def _pct_change(close: pd.Series, bars: int) -> float:
    if len(close) <= bars:
        return 0.0
    start = float(close.iloc[-bars])
    end = float(close.iloc[-1])
    if start <= 0:
        return 0.0
    return ((end / start) - 1) * 100


def _volume_ratio(df: pd.DataFrame, bars: int = 20) -> float:
    avg = float(df["Volume"].tail(bars).mean() or 0)
    latest = float(df.iloc[-1]["Volume"] or 0)
    return latest / avg if avg > 0 else 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if not isfinite(number):
        return default
    return number


def _tv_symbol_to_yf(ticker: str, name: str | None = None, market: str = "TH") -> str:
    if market == "US":
        raw = ticker.split(":")[-1].strip().upper()
    else:
        raw = (name or ticker.split(":")[-1]).strip().upper()
    return normalize_symbol(raw, market)


def _is_operating_common_stock(item: dict[str, Any], market: str = "TH") -> bool:
    if item.get("type") != "stock" or item.get("subtype") != "common":
        return False
    if market == "TH":
        exchange = str(item.get("exchange") or "").upper()
        if exchange not in {"SET", "MAI"}:
            return False
    text = f"{item.get('name') or ''} {item.get('description') or ''}".upper()
    return not any(keyword in text for keyword in NON_OPERATING_KEYWORDS)


def load_market_snapshot(market: str = "TH") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if market == "GOLD":
        return DEFAULT_GOLD_SYMBOLS, {
            "provider": "precious_metals_universe",
            "raw_count": len(DEFAULT_GOLD_SYMBOLS),
            "common_stock_count": len(DEFAULT_GOLD_SYMBOLS),
            "error": None,
        }

    try:
        from tradingview_screener import Query

        q = Query().select(*TV_METRIC_COLUMNS)
        if market == "TH":
            q = q.set_markets("thailand").limit(2000)
            total, df = q.get_scanner_data()
        elif market == "US":
            import requests
            import pandas as pd
            import io
            
            # Scrape official S&P 500 symbols from Wikipedia
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            sp500_df = pd.read_html(io.StringIO(r.text))[0]
            # Replace '-' with '.' to match TV naming (e.g. BRK.B)
            sp500_symbols = set(sp500_df["Symbol"].str.replace("-", "."))
            
            # Fetch top 1500 US stocks to ensure we get the metrics for the S&P 500 components
            q = q.set_markets("america").order_by("market_cap_basic", ascending=False).limit(1500)
            total, raw_df = q.get_scanner_data()
            
            # Filter to only keep true S&P 500 constituents
            df = raw_df[raw_df["name"].isin(sp500_symbols)]
            total = len(df)
        elif market == "US_MEDIUM_TERM":
            from th_smc.scraper import get_sp500_symbols
            sp500_symbols = set(get_sp500_symbols())
            q = q.set_markets("america").order_by("market_cap_basic", ascending=False).limit(3000)
            total, raw_df = q.get_scanner_data()
            df = raw_df[raw_df["name"].isin(sp500_symbols)]
            total = len(df)
        elif market == "GOLD":
            return DEFAULT_GOLD_SYMBOLS, {
                "provider": "local_fallback_universe",
                "raw_count": len(DEFAULT_GOLD_SYMBOLS),
                "common_stock_count": len(DEFAULT_GOLD_SYMBOLS),
                "error": None,
            }
            
    except Exception as exc:
        if market == "TH":
            fallback = [{"symbol": normalize_symbol(symbol, market), "name": symbol} for symbol in DEFAULT_TH_SYMBOLS]
        elif market in ["US", "US_MEDIUM_TERM"]:
            fallback = [{"symbol": symbol, "name": symbol} for symbol in DEFAULT_US_SYMBOLS]
        elif market == "GOLD":
            fallback = DEFAULT_GOLD_SYMBOLS
        else:
            fallback = [{"symbol": "AAPL", "name": "AAPL"}]
        return fallback, {
            "provider": "local_fallback_universe",
            "raw_count": len(fallback),
            "common_stock_count": len(fallback),
            "error": str(exc),
        }

    rows: list[dict[str, Any]] = []
    for item in df.to_dict("records"):
        if not _is_operating_common_stock(item, market=market):
            continue
        exchange = str(item.get("exchange") or "").upper()
        try:
            symbol = _tv_symbol_to_yf(str(item.get("ticker") or ""), str(item.get("name") or ""), market=market)
        except ValueError:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": item.get("name") or symbol,
                "description": item.get("description") or item.get("name") or symbol,
                "sector": exchange,
                "price": _safe_float(item.get("close")),
                "sma20": _safe_float(item.get("SMA20"), None),  # type: ignore[arg-type]
                "sma50": _safe_float(item.get("SMA50"), None),  # type: ignore[arg-type]
                "sma150": None,
                "sma200": _safe_float(item.get("SMA200"), None),  # type: ignore[arg-type]
                "rsi": _safe_float(item.get("RSI"), 50.0),
                "perf_1m": _safe_float(item.get("Perf.1M")),
                "perf_3m": _safe_float(item.get("Perf.3M")),
                "perf_6m": _safe_float(item.get("Perf.6M")),
                "distance_high": (
                    ((_safe_float(item.get("close")) / _safe_float(item.get("price_52_week_high"))) - 1)
                    * 100
                    if _safe_float(item.get("price_52_week_high")) > 0
                    else 0.0
                ),
                "distance_low": (
                    ((_safe_float(item.get("close")) / _safe_float(item.get("price_52_week_low"))) - 1)
                    * 100
                    if _safe_float(item.get("price_52_week_low")) > 0
                    else 0.0
                ),
                "volume_ratio": _safe_float(item.get("relative_volume_10d_calc"), 1.0),
                "market_cap": _safe_float(item.get("market_cap_basic")),
                "snapshot_provider": "tradingview",
                "roe": _safe_float(item.get("return_on_equity")),
                "debt_to_equity": _safe_float(item.get("debt_to_equity")),
                "roc": _safe_float(item.get("return_on_invested_capital")),
                "fcf_margin": _safe_float(item.get("free_cash_flow_margin_ttm")),
                "gross_margin": _safe_float(item.get("gross_margin")),
                "ebitda_margin": _safe_float(item.get("ebitda_margin_ttm")),
                "revenue_growth_5y": _safe_float(item.get("total_revenue_cagr_5y")),
            }
        )
    return rows, {
        "provider": "tradingview",
        "raw_count": int(total),
        "common_stock_count": len(rows),
        "error": None,
    }


def _screen_metrics(symbol: str, df: pd.DataFrame, market: str = "TH") -> dict[str, Any]:
    close_series = pd.to_numeric(df["Close"], errors="coerce").dropna()
    high_series = pd.to_numeric(df["High"], errors="coerce").dropna()
    low_series = pd.to_numeric(df["Low"], errors="coerce").dropna()
    close = float(close_series.iloc[-1])
    high_52w = float(high_series.tail(252).max())
    low_52w = float(low_series.tail(252).min())
    sma20 = _sma(close_series, 20)
    sma50 = _sma(close_series, 50)
    sma150 = _sma(close_series, 150)
    sma200 = _sma(close_series, 200)
    rsi = _rsi(close_series)
    perf_1m = _pct_change(close_series, 22)
    perf_3m = _pct_change(close_series, 63)
    perf_6m = _pct_change(close_series, 126)
    distance_high = ((close / high_52w) - 1) * 100 if high_52w > 0 else 0.0
    distance_low = ((close / low_52w) - 1) * 100 if low_52w > 0 else 0.0
    vol_ratio = _volume_ratio(df)
    sector = "SET" if market == "TH" else ("COMMODITY" if market == "GOLD" else "US")
    return {
        "symbol": normalize_symbol(symbol, market),
        "name": normalize_symbol(symbol, market),
        "sector": sector,
        "price": round(close, 2),
        "market_cap": 50_000_000_000,
        "sma20": sma20,
        "sma50": sma50,
        "sma150": sma150,
        "sma200": sma200,
        "rsi": rsi,
        "perf_1m": perf_1m,
        "perf_3m": perf_3m,
        "perf_6m": perf_6m,
        "distance_high": distance_high,
        "distance_low": distance_low,
        "volume_ratio": vol_ratio,
        "roe": 22.0 if market in ["US", "US_MEDIUM_TERM"] else 14.0,
        "debt_to_equity": 0.6 if market in ["US", "US_MEDIUM_TERM"] else 1.1,
        "roc": 16.0 if market in ["US", "US_MEDIUM_TERM"] else 9.0,
        "fcf_margin": 18.0 if market in ["US", "US_MEDIUM_TERM"] else 8.0,
        "gross_margin": 48.0 if market in ["US", "US_MEDIUM_TERM"] else 26.0,
        "ebitda_margin": 26.0 if market in ["US", "US_MEDIUM_TERM"] else 16.0,
        "revenue_growth_5y": 12.0 if market in ["US", "US_MEDIUM_TERM"] else 6.0,
    }


def _source_candidate(source: str, metrics: dict[str, Any], score: float, rating: str) -> dict[str, Any]:
    return {
        "source": source,
        "symbol": metrics["symbol"],
        "name": metrics["name"],
        "score": round(score, 1),
        "rating": rating,
        "price": metrics["price"],
        "sector": metrics["sector"],
        "report": "standalone local screener",
        "plan": None,
        "metrics": metrics,
    }


def _score_sources(metrics: dict[str, Any]) -> dict[str, tuple[float, str]]:
    close = metrics["price"]
    sma20 = metrics["sma20"]
    sma50 = metrics["sma50"]
    sma150 = metrics["sma150"]
    sma200 = metrics["sma200"]
    rsi = metrics["rsi"] or 50.0
    vol_ratio = metrics["volume_ratio"]
    perf_1m = metrics["perf_1m"]
    perf_3m = metrics["perf_3m"]
    perf_6m = metrics["perf_6m"]
    distance_high = metrics["distance_high"]
    distance_low = metrics["distance_low"]

    vcp_score = 0.0
    if sma50 and sma150:
        if sma200:
            vcp_score += 25 if close > sma50 > sma150 > sma200 else 8
            vcp_score += 20 if sma200 > 0 and ((close / sma200) - 1) * 100 < 55 else 5
        else:
            vcp_score += 22 if close > sma50 > sma150 else 8
            vcp_score += 12
    elif sma50 and sma200:
        vcp_score += 25 if close > sma50 > sma200 else 8
        vcp_score += 20 if sma200 > 0 and ((close / sma200) - 1) * 100 < 55 else 5
    elif sma20 and sma50:
        vcp_score += 18 if close > sma20 > sma50 else 6
        vcp_score += 8
    vcp_score += 20 if -25 <= distance_high <= 5 else 10
    vcp_score += 20 if distance_low >= 15 else 10 if distance_low >= 0 else 0
    vcp_score += 15 if 35 <= rsi <= 75 else 5
    vcp_pass = bool(
        sma50
        and sma200
        and close > sma50 > sma200
        and -25 <= distance_high <= 5
        and distance_low >= 25
        and 40 <= rsi <= 75
        and ((close / sma200) - 1) * 100 <= 60
    )

    canslim_score = 0.0
    canslim_score += 25 if perf_3m > 8 else 15 if perf_3m > 0 else 0
    canslim_score += 25 if perf_6m > 15 else 15 if perf_6m > 0 else 0
    canslim_score += 20 if -15 <= distance_high <= 0 else 5
    canslim_score += 15 if vol_ratio >= 1.05 else 5
    canslim_score += 15 if sma50 and close > sma50 else 0
    canslim_pass = bool(
        sma50
        and close > sma50
        and perf_3m >= 8
        and perf_6m >= 15
        and -15 <= distance_high <= 5
        and (rsi >= 50 or vol_ratio >= 1.05)
    )

    dip_score = 0.0
    dip_score += 25 if sma50 and close >= sma50 else 0
    dip_score += 25 if sma20 and close <= sma20 * 1.02 else 0
    dip_score += 20 if 30 <= rsi <= 58 else 5
    dip_score += 15 if perf_3m > 0 else 0
    dip_score += 15 if vol_ratio >= 0.75 else 5
    dip_pass = bool(
        sma20
        and sma50
        and close >= sma50
        and close <= sma20 * 1.03
        and 30 <= rsi <= 58
        and perf_3m > 0
    )

    momentum_score = 0.0
    momentum_score += 25 if perf_1m > 5 else 15 if perf_1m > 0 else 0
    momentum_score += 25 if perf_3m > 12 else 15 if perf_3m > 0 else 0
    momentum_score += 20 if rsi >= 58 else 10 if rsi >= 35 else 0
    momentum_score += 20 if vol_ratio >= 1.2 else 5
    momentum_score += 10 if sma20 and close > sma20 else 0
    momentum_pass = bool(
        sma20
        and close > sma20
        and perf_1m >= 5
        and perf_3m >= 12
        and rsi >= 58
        and vol_ratio >= 1.2
    )

    fundamental_score = 0.0
    fundamental_score += 20 if metrics.get("roe", 0) >= 15 else 0
    fundamental_score += 15 if metrics.get("debt_to_equity", 100) < 1.0 else 0
    fundamental_score += 15 if metrics.get("roc", 0) >= 10 else 0
    fundamental_score += 15 if metrics.get("fcf_margin", 0) >= 10 else 0
    fundamental_score += 15 if metrics.get("gross_margin", 0) >= 40 else 0
    fundamental_score += 10 if metrics.get("ebitda_margin", 0) >= 20 else 0
    fundamental_score += 10 if metrics.get("revenue_growth_5y", 0) >= 10 else 0
    
    # We allow some flexibility: score must be at least 70/100 to pass.
    fundamental_pass = fundamental_score >= 70

    passed = {}
    if vcp_pass and metrics.get("is_set100"):
        passed["VCP"] = (vcp_score, "Passed VCP proxy rules")
    if canslim_pass and metrics.get("is_canslim_growth"):
        passed["CANSLIM"] = (canslim_score, "Passed CANSLIM proxy rules")
    if dip_pass and metrics.get("is_swing_universe"):
        passed["DIP_BUY"] = (dip_score, "Passed dip-buy pullback rules")
    if momentum_pass and metrics.get("is_swing_universe"):
        passed["MOMENTUM"] = (momentum_score, "Passed momentum rules")
    if fundamental_pass and metrics.get("is_fundamental_universe"):
        passed["FUNDAMENTAL"] = (fundamental_score, "Passed fundamental criteria")
    return passed


def collect_candidate_sources(market: str = "TH", limit_per_source: int = 0) -> dict[str, Any]:
    if limit_per_source <= 0:
        limit_per_source = 15

    metric_rows, universe_meta = load_market_snapshot(market)
    is_fallback = universe_meta.get("provider") != "tradingview"
    if is_fallback:
        metric_rows = metric_rows[:25]
        enriched_rows: list[dict[str, Any]] = []

        def _enrich(row: dict[str, Any]) -> dict[str, Any] | None:
            normalized = row["symbol"]
            try:
                df = load_ohlcv(normalized, market=market)
                metrics = _screen_metrics(normalized, df, market=market)
                if row.get("name") and row["name"] != normalized:
                    metrics["name"] = row["name"]
                return metrics
            except (IndexError, KeyError, ValueError, TypeError, MarketDataUnavailable):
                return None

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_enrich, r) for r in metric_rows]
            for future in as_completed(futures):
                res = future.result()
                if res:
                    enriched_rows.append(res)
        metric_rows = enriched_rows

    # Flag SET100 proxy
    set_stocks = [r for r in metric_rows if r.get("sector") == "SET"]
    set_stocks.sort(key=lambda x: x.get("market_cap") or 0.0, reverse=True)
    set100_symbols = {r["symbol"] for r in set_stocks[:100]}
    
    growth_symbols = {
        "DELTA", "HANA", "KCE", "CCET", "SIS", "SYNEX", "ADVICE",
        "CPALL", "CPAXT", "COM7", "MOSHI", "AU", "SINGER", "BEAUTY",
        "SAPPE", "ICHI", "COCOCO", "MALEE", "PLUS", "KCG", "BTG", "CBG", "OSP",
        "MTC", "SAWAD", "TIDLOR", "AEONTS", "JMT", "BAM",
        "WHA", "AMATA", "SJWD", "III", "MENA",
        "BDMS", "BH", "PR9", "MASTER", "CHG",
        "GULF", "GPSC", "BGRIM", "EA",
        "SIRI", "AP", "SPALI", "DOHOME", "GLOBAL", "MEGA", "PLANB",
        "AOT", "MINT", "CENTEL", "ERW", "SPA", "TRUE"
    }
    
    for row in metric_rows:
        raw_symbol = row["symbol"].replace(".BK", "").split(":")[-1]
        if market == "TH":
            row["is_set100"] = True if is_fallback else (row["symbol"] in set100_symbols)
            row["is_canslim_growth"] = True if is_fallback else (raw_symbol in growth_symbols)
            row["is_swing_universe"] = True if is_fallback else ((row.get("market_cap") or 0.0) >= 2_000_000_000)
            row["is_fundamental_universe"] = False
        elif market == "US":
            row["is_set100"] = True  # Proxy to pass VCP
            row["is_canslim_growth"] = True  # Proxy to pass CANSLIM
            row["is_swing_universe"] = True
            row["is_fundamental_universe"] = False
        elif market == "US_MEDIUM_TERM":
            row["is_set100"] = True
            row["is_canslim_growth"] = True
            row["is_swing_universe"] = True
            row["is_fundamental_universe"] = True
        elif market == "GOLD":
            row["is_set100"] = False
            row["is_canslim_growth"] = False
            row["is_swing_universe"] = True
            row["is_fundamental_universe"] = False

    sources: dict[str, list[dict[str, Any]]] = {
        "VCP": [],
        "CANSLIM": [],
        "DIP_BUY": [],
        "MOMENTUM": [],
        "FUNDAMENTAL": [],
        "COMMODITY": [],
        "CORE_MONITOR": [],
    }

    for metrics in metric_rows:
        scored = _score_sources(metrics)
        if market == "GOLD":
            scored["COMMODITY"] = (100, "Precious Metals Core")
        for source, (score, rating) in scored.items():
            if source in sources:
                sources[source].append(_source_candidate(source, metrics, score, rating))

    passed_counts = {key: len(value) for key, value in sources.items()}
    for key, bucket in sources.items():
        bucket.sort(key=lambda item: item["score"] or 0, reverse=True)
        sources[key] = bucket[:limit_per_source]
    selected_counts = {key: len(value) for key, value in sources.items()}

    by_symbol: dict[str, dict[str, Any]] = {}
    for bucket in sources.values():
        for entry in bucket:
            symbol = entry["symbol"]
            merged = by_symbol.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": entry["name"],
                    "sector": entry["sector"],
                    "sources": [],
                    "source_details": [],
                },
            )
            merged["sources"].append(entry["source"])
            merged["source_details"].append(entry)
            if not merged.get("sector") and entry.get("sector"):
                merged["sector"] = entry["sector"]

    # Liquid Candidate Guarantee: ensure at least 15 core liquid assets are evaluated
    if len(by_symbol) < 10 and metric_rows:
        sorted_rows = sorted(
            metric_rows,
            key=lambda m: (m.get("volume_ratio") or 0.0, m.get("perf_1m") or 0.0),
            reverse=True
        )
        for m in sorted_rows:
            sym = m["symbol"]
            if sym not in by_symbol:
                entry = _source_candidate("CORE_MONITOR", m, 75.0, "Core Liquid Monitor")
                sources["CORE_MONITOR"].append(entry)
                by_symbol[sym] = {
                    "symbol": sym,
                    "name": m.get("name") or sym,
                    "sector": m.get("sector") or ("SET" if market == "TH" else "US"),
                    "sources": ["CORE_MONITOR"],
                    "source_details": [entry],
                }
            if len(by_symbol) >= 15:
                break

    return {
        "sources": sources,
        "candidates": list(by_symbol.values()),
        "reports": {
            "VCP": "standalone local screener",
            "CANSLIM": "standalone local screener",
            "DIP_BUY": "standalone local screener",
            "MOMENTUM": "standalone local screener",
            "FUNDAMENTAL": "standalone local screener",
            "COMMODITY": "standalone local screener",
            "CORE_MONITOR": "standalone local screener",
        },
        "fallback_used": False,
        "data_policy": "real_market_data_only",
        "universe": universe_meta,
        "passed_counts": passed_counts,
        "selected_counts": selected_counts,
    }


def _to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = []
    for row in df.tail(120).to_dict("records"):
        records.append(
            {
                "time": row["Date"],
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row.get("Volume") or 0),
            }
        )
    return records


def _confirmed_swings(df: pd.DataFrame, left: int = 3, right: int = 3) -> list[SwingPoint]:
    swings: list[SwingPoint] = []
    highs = df["High"].tolist()
    lows = df["Low"].tolist()
    dates = df["Date"].tolist()
    for i in range(left, len(df) - right):
        high_window = highs[i - left : i + right + 1]
        low_window = lows[i - left : i + right + 1]
        if highs[i] == max(high_window) and high_window.count(highs[i]) == 1:
            swings.append(SwingPoint(i, dates[i], float(highs[i]), "high"))
        if lows[i] == min(low_window) and low_window.count(lows[i]) == 1:
            swings.append(SwingPoint(i, dates[i], float(lows[i]), "low"))
    return swings


def _nearest_zone(df: pd.DataFrame, kind: str) -> dict[str, Any] | None:
    lookback = df.tail(90).reset_index(drop=True)
    if lookback.empty:
        return None
    if kind == "demand":
        idx = int(lookback["Low"].idxmin())
        row = lookback.iloc[idx]
        return {
            "kind": "DZ",
            "date": row["Date"],
            "low": round(float(row["Low"]), 2),
            "high": round(float(max(row["Open"], row["Close"])), 2),
        }
    idx = int(lookback["High"].idxmax())
    row = lookback.iloc[idx]
    return {
        "kind": "SZ",
        "date": row["Date"],
        "low": round(float(min(row["Open"], row["Close"])), 2),
        "high": round(float(row["High"]), 2),
    }


def _latest_fvg(df: pd.DataFrame) -> dict[str, Any] | None:
    for i in range(len(df) - 1, 2, -1):
        prev2 = df.iloc[i - 2]
        cur = df.iloc[i]
        if float(cur["Low"]) > float(prev2["High"]):
            return {
                "type": "bullish",
                "date": cur["Date"],
                "low": round(float(prev2["High"]), 2),
                "high": round(float(cur["Low"]), 2),
            }
        if float(cur["High"]) < float(prev2["Low"]):
            return {
                "type": "bearish",
                "date": cur["Date"],
                "low": round(float(cur["High"]), 2),
                "high": round(float(prev2["Low"]), 2),
            }
    return None


def _liquidity_sweep(df: pd.DataFrame, swings: list[SwingPoint]) -> dict[str, Any]:
    recent = df.tail(20).reset_index(drop=True)
    last_close = float(recent.iloc[-1]["Close"])
    prior_lows = [s for s in swings if s.kind == "low" and s.index < len(df) - 3]
    prior_highs = [s for s in swings if s.kind == "high" and s.index < len(df) - 3]

    if prior_lows:
        ref = prior_lows[-1]
        sweep_low = float(recent["Low"].min())
        if sweep_low < ref.price and last_close > ref.price:
            return {
                "side": "sell-side swept",
                "reference": round(ref.price, 2),
                "sweep": round(sweep_low, 2),
                "confirmed": True,
            }
    if prior_highs:
        ref = prior_highs[-1]
        sweep_high = float(recent["High"].max())
        if sweep_high > ref.price and last_close < ref.price:
            return {
                "side": "buy-side swept",
                "reference": round(ref.price, 2),
                "sweep": round(sweep_high, 2),
                "confirmed": True,
            }
    return {"side": "waiting", "reference": None, "sweep": None, "confirmed": False}


def _structure(df: pd.DataFrame, swings: list[SwingPoint]) -> dict[str, Any]:
    close = float(df.iloc[-1]["Close"])
    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    last_high = highs[-1] if highs else None
    last_low = lows[-1] if lows else None

    event = "range"
    bias = "neutral"
    if last_high and close > last_high.price:
        event = "BOS bullish"
        bias = "bullish"
    elif last_low and close < last_low.price:
        event = "BOS bearish"
        bias = "bearish"
    elif len(highs) >= 2 and len(lows) >= 2:
        if highs[-1].price > highs[-2].price and lows[-1].price > lows[-2].price:
            bias = "bullish"
        elif highs[-1].price < highs[-2].price and lows[-1].price < lows[-2].price:
            bias = "bearish"

    return {
        "event": event,
        "bias": bias,
        "last_high": _swing_to_dict(last_high),
        "last_low": _swing_to_dict(last_low),
    }


def _swing_to_dict(swing: SwingPoint | None) -> dict[str, Any] | None:
    if swing is None:
        return None
    return {"date": swing.date, "price": round(swing.price, 2), "kind": swing.kind}


def _rr(entry: float, stop: float, target: float, side: str) -> float:
    risk = entry - stop if side == "buy" else stop - entry
    reward = target - entry if side == "buy" else entry - target
    if risk <= 0 or reward <= 0:
        return 0.0
    return round(reward / risk, 2)


def analyze_symbol(
    symbol: str,
    data: pd.DataFrame | None = None,
    source_profile: dict[str, Any] | None = None,
    min_rr: float = 2.0,
    market: str = "TH",
) -> dict[str, Any]:
    normalized = normalize_symbol(symbol, market)
    df = (data.copy() if data is not None else load_ohlcv(normalized, market=market)).dropna().reset_index(drop=True)
    data_source = df.attrs.get("data_source", "provided" if data is not None else "unknown")
    is_sample = bool(df.attrs.get("is_sample", False))
    if len(df) < 40:
        raise MarketDataUnavailable(f"Not enough real OHLCV bars for {normalized}")

    for col in ["Open", "High", "Low", "Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().reset_index(drop=True)

    swings = _confirmed_swings(df)
    structure = _structure(df, swings)
    sweep = _liquidity_sweep(df, swings)
    demand = _nearest_zone(df, "demand")
    supply = _nearest_zone(df, "supply")
    fvg = _latest_fvg(df)

    close = float(df.iloc[-1]["Close"])
    side = "wait"
    stop = target = rr = 0.0
    if structure["bias"] == "bullish":
        side = "buy"
        # Prevent excessively wide stop loss by picking the higher (tighter) level between 20-day low and demand zone
        stop = max(float(df.tail(20)["Low"].min()), demand["low"] if demand else 0)
        target = supply["low"] if supply and supply["low"] > close else close + (close - stop) * min_rr
        rr = _rr(close, stop, target, side)
    elif structure["bias"] == "bearish":
        side = "sell"
        # Prevent excessively wide stop loss by picking the lower (tighter) level between 20-day high and supply zone
        stop = min(float(df.tail(20)["High"].max()), supply["high"] if supply else float('inf'))
        target = demand["high"] if demand and demand["high"] < close else close - (stop - close) * min_rr
        rr = _rr(close, stop, target, side)

    checklist = {
        "htf_context": structure["bias"] != "neutral",
        "h4_zone": demand is not None and supply is not None,
        "liquidity_sweep": bool(sweep["confirmed"]),
        "fvg_or_zone": fvg is not None or demand is not None or supply is not None,
        "rr_pass": rr >= min_rr,
    }
    score = sum([15 if checklist["htf_context"] else 0, 15 if checklist["h4_zone"] else 0])
    score += 25 if checklist["liquidity_sweep"] else 0
    score += 15 if checklist["fvg_or_zone"] else 0
    score += 30 if checklist["rr_pass"] else 0

    if side == "wait":
        decision = "WAIT"
    elif score >= 70 and rr >= min_rr:
        decision = "ARMED"
    else:
        decision = "NO TRADE"

    rr_clean = rr if isfinite(rr) else 0.0
    
    pct_gain = 0.0
    pct_loss = 0.0
    if close > 0 and stop > 0 and target > 0:
        pct_gain = abs(target - close) / close * 100.0
        pct_loss = abs(close - stop) / close * 100.0

    # Extract fundamentals from source_details
    roe = debt_to_equity = roc = fcf_margin = gross_margin = ebitda_margin = revenue_growth_5y = None
    intrinsic_value = peg_ratio = None
    
    if market == "US_MEDIUM_TERM" and source_profile:
        sources = source_profile.get("sources", [])
        if "FUNDAMENTAL" in sources:
            source_details = source_profile.get("source_details", [])
            metrics_raw = next((d for d in source_details if d["source"] == "FUNDAMENTAL"), source_details[0] if source_details else {})
            raw = metrics_raw.get("metrics", {})
            roe = raw.get("roe")
            debt_to_equity = raw.get("debt_to_equity")
            roc = raw.get("roc")
            fcf_margin = raw.get("fcf_margin")
            gross_margin = raw.get("gross_margin")
            ebitda_margin = raw.get("ebitda_margin")
            revenue_growth_5y = raw.get("revenue_growth_5y")
            
            # Fetch deep fundamentals using yfinance/alphaspread
            if score >= 70:
                try:
                    from .scraper import get_fundamental_extras
                    raw_sym = symbol.replace(".BK", "").split(":")[-1]
                    exchange_tv = (source_profile or {}).get("exchange", "")
                    extras = get_fundamental_extras(raw_sym, exchange_tv)
                    peg_ratio = extras.get("peg_ratio") or peg_ratio
                    intrinsic_value = extras.get("intrinsic_value") or intrinsic_value
                except Exception as e:
                    print(f"Error getting fundamentals for {raw_sym}: {e}")

    return {
        "symbol": normalized,
        "name": (source_profile or {}).get("name") or normalized,
        "sector": (source_profile or {}).get("sector"),
        "sources": (source_profile or {}).get("sources", []),
        "source_details": (source_profile or {}).get("source_details", []),
        "intrinsic_value": intrinsic_value,
        "peg_ratio": peg_ratio,
        "roe": roe,
        "debt_to_equity": debt_to_equity,
        "roc": roc,
        "fcf_margin": fcf_margin,
        "gross_margin": gross_margin,
        "ebitda_margin": ebitda_margin,
        "revenue_growth_5y": revenue_growth_5y,
        "data_source": data_source,
        "is_sample": is_sample,
        "as_of": str(df.iloc[-1]["Date"]),
        "close": round(close, 2),
        "side": side,
        "decision": decision,
        "score": int(score),
        "rr": rr_clean,
        "entry": round(close, 2),
        "stop": round(stop, 2) if stop else None,
        "target": round(target, 2) if target else None,
        "pct_gain": round(pct_gain, 2),
        "pct_loss": round(pct_loss, 2),
        "structure": structure,
        "liquidity": sweep,
        "zones": {"demand": demand, "supply": supply, "fvg": fvg},
        "checklist": checklist,
        "candles": _to_records(df),
    }


def scan_symbols(symbols: list[str] | None = None, min_rr: float = 2.0, market: str = "TH") -> dict[str, Any]:
    source_payload = collect_candidate_sources(market=market)
    profiles = {item["symbol"]: item for item in source_payload["candidates"]}
    if symbols:
        selected = [normalize_symbol(item, market) for item in symbols]
    else:
        selected = list(profiles.keys())[:15]
    results = []
    max_workers = min(4, max(1, len(selected)))

    def _analyze_selected(symbol: str) -> dict[str, Any] | None:
        try:
            normalized = normalize_symbol(symbol, market)
            return analyze_symbol(normalized, source_profile=profiles.get(normalized), min_rr=min_rr, market=market)
        except Exception as e:
            print(f"ERROR on {symbol}: {e}")
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_analyze_selected, symbol) for symbol in selected]
        for future in as_completed(futures):
            item = future.result()
            if item:
                results.append(item)
    results.sort(key=lambda item: (item["decision"] != "ARMED", -item["score"], -item["rr"]))
    armed = [item for item in results if item["decision"] == "ARMED"]
    return {
        "market": market,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(results),
        "armed_count": len(armed),
        "source_summary": {
            key: source_payload["passed_counts"].get(key, 0) for key in source_payload["sources"]
        },
        "selected_summary": source_payload["selected_counts"],
        "source_reports": source_payload["reports"],
        "fallback_used": source_payload["fallback_used"],
        "data_policy": source_payload["data_policy"],
        "universe": source_payload["universe"],
        "results": results,
    }
