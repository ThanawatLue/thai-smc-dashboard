import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace collect_candidate_sources
new_collect = '''def collect_candidate_sources(limit_per_source: int = 200, market: str = "TH") -> dict[str, Any]:
    metric_rows, universe_meta = load_market_snapshot(market=market)
    
    if market == "GOLD":
        return {"Gold": {"symbols": {"GC=F"}, "meta": universe_meta}}
        
    if universe_meta["provider"] != "tradingview":
        enriched_rows: list[dict[str, Any]] = []
        for row in metric_rows:
            normalized = row["symbol"]
            try:
                df = load_ohlcv(normalized, market=market)
                enriched_rows.append(_screen_metrics(normalized, df))
            except (IndexError, KeyError, ValueError, TypeError, MarketDataUnavailable):
                continue
        metric_rows = enriched_rows

    if market == "US":
        metric_rows.sort(key=lambda x: x.get("market_cap") or 0.0, reverse=True)
        top100_symbols = {r["symbol"] for r in metric_rows[:100]}
        
        return {
            "US Top 100 (S&P 100 proxy)": {
                "symbols": top100_symbols, 
                "meta": universe_meta
            },
            "US Top 500 (S&P 500 proxy)": {
                "symbols": {r["symbol"] for r in metric_rows}, 
                "meta": universe_meta
            },
        }

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
        raw_symbol = row["symbol"].replace(".BK", "")
        row["is_set100"] = row["symbol"] in set100_symbols
        row["is_canslim_growth"] = raw_symbol in growth_symbols
        # Swing universe: Market Cap >= 2B THB
        row["is_swing_universe"] = (row.get("market_cap") or 0.0) >= 2_000_000_000

    sources: dict[str, list[dict[str, Any]]] = {
        "VCP": [],
        "CANSLIM": [],
        "DIP_BUY": [],
        "SWING_BASE": [],
    }

    for row in metric_rows:
        sym = row["symbol"]
        price = row.get("price", 0.0)
        vol = row.get("volume", 0)
        # Liquidity filter: volume * price >= 5M THB/day roughly
        if price * vol < 5_000_000:
            continue

        rsi = row.get("rsi", 50.0)
        sma20 = row.get("sma20")
        sma50 = row.get("sma50")
        sma200 = row.get("sma200")
        perf_1m = row.get("perf_1m", 0.0)
        perf_3m = row.get("perf_3m", 0.0)

        # Base filter: price > sma50 and sma50 > sma200
        uptrend = False
        if price and sma50 and sma200:
            uptrend = (price > sma50) and (sma50 > sma200)

        # 1. VCP Candidates
        if uptrend and 45 <= rsi <= 65 and perf_3m > 10:
            sources["VCP"].append(row)

        # 2. CANSLIM/Growth Candidates
        if row["is_canslim_growth"] and uptrend and perf_3m > 15:
            sources["CANSLIM"].append(row)

        # 3. Dip Buy (Pullback) Candidates
        if uptrend and sma20 and price < sma20 and 30 <= rsi <= 45:
            sources["DIP_BUY"].append(row)

        # 4. Swing Base Candidates (Broad)
        if row["is_swing_universe"] and uptrend:
            sources["SWING_BASE"].append(row)

    # Sort each source by 1M performance
    for key in sources:
        sources[key].sort(key=lambda x: x.get("perf_1m") or 0.0, reverse=True)

    result_sources: dict[str, Any] = {}
    for key, items in sources.items():
        limited_items = items[:limit_per_source]
        result_sources[key] = {
            "symbols": {i["symbol"] for i in limited_items},
            "meta": universe_meta,
        }
    return result_sources'''

content = re.sub(
    r'def collect_candidate_sources\(limit_per_source: int = 200\) -> dict\[str, Any\]:.*?return result_sources',
    new_collect,
    content,
    flags=re.DOTALL
)

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
