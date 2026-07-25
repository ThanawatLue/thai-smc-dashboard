import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. replace load_thai_market_snapshot
old_snapshot_func = '''def load_thai_market_snapshot() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    try:
        from tradingview_screener import Query

        total, df = (
            Query()
            .set_markets("thailand")
            .select(*TV_METRIC_COLUMNS)
            .limit(2000)
            .get_scanner_data()
        )
    except Exception as exc:
        fallback = [{"symbol": normalize_symbol(symbol), "name": symbol} for symbol in DEFAULT_TH_SYMBOLS]
        return fallback, {
            "provider": "local_fallback_universe",
            "raw_count": len(fallback),
            "common_stock_count": len(fallback),
            "error": str(exc),
        }

    rows: list[dict[str, Any]] = []
    for item in df.to_dict("records"):
        if not _is_operating_common_stock(item):
            continue
        exchange = str(item.get("exchange") or "").upper()
        try:
            symbol = _tv_symbol_to_yf(str(item.get("ticker") or ""), str(item.get("name") or ""))
        except ValueError:
            continue'''

new_snapshot_func = '''def load_market_snapshot(market: str = "TH") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if market == "GOLD":
        fallback = [{"symbol": "GC=F", "name": "Gold Futures (COMEX)"}]
        return fallback, {
            "provider": "hardcoded_gold",
            "raw_count": 1,
            "common_stock_count": 1,
            "error": None
        }

    try:
        from tradingview_screener import Query

        q = Query().select(*TV_METRIC_COLUMNS)
        if market == "TH":
            q = q.set_markets("thailand").limit(2000)
        elif market == "US":
            q = q.set_markets("america").where("is_primary", True).order_by("market_cap_basic", ascending=False).limit(500)
        
        total, df = q.get_scanner_data()
    except Exception as exc:
        if market == "TH":
            fallback = [{"symbol": normalize_symbol(symbol, market), "name": symbol} for symbol in DEFAULT_TH_SYMBOLS]
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
            continue'''

content = content.replace(old_snapshot_func, new_snapshot_func)

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
