import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace analyze_symbol
new_analyze = '''def analyze_symbol(
    symbol: str, data: pd.DataFrame | None = None, source_profile: dict[str, Any] | None = None, min_rr: float | None = None, market: str = "TH"
) -> dict[str, Any]:
    normalized = normalize_symbol(symbol, market)
    df = (data.copy() if data is not None else load_ohlcv(normalized, market=market)).dropna().reset_index(drop=True)

    if len(df) < 20:
        raise MarketDataUnavailable(f"Not enough real OHLCV bars for {normalized}")'''

content = re.sub(
    r'def analyze_symbol\(\s*symbol: str, data: pd\.DataFrame \| None = None, source_profile: dict\[str, Any\] \| None = None, min_rr: float \| None = None\n\) -> dict\[str, Any\]:\n    normalized = normalize_symbol\(symbol\)\n    df = \(data\.copy\(\) if data is not None else load_ohlcv\(normalized\)\)\.dropna\(\)\.reset_index\(drop=True\)\n\n    if len\(df\) < 20:\n        raise MarketDataUnavailable\(f"Not enough real OHLCV bars for \{normalized\}"\)',
    new_analyze,
    content,
    flags=re.DOTALL
)

# Replace scan_symbols
new_scan = '''def scan_symbols(symbols: list[str] | None = None, min_rr: float | None = None, market: str = "TH") -> dict[str, Any]:
    profiles: dict[str, dict[str, Any]] = {}
    scan_meta: dict[str, Any] = {}

    if not symbols:
        sources_data = collect_candidate_sources(limit_per_source=100, market=market)
        
        for k, v in sources_data.items():
            if not scan_meta and "meta" in v:
                scan_meta = v["meta"]
            for s in v["symbols"]:
                profiles[s] = {"source_list": []}

        for k, v in sources_data.items():
            for s in v["symbols"]:
                profiles[s]["source_list"].append(k)
    else:
        scan_meta = {"provider": "manual_list", "raw_count": len(symbols)}

    selected = [normalize_symbol(item, market) for item in symbols] if symbols else list(profiles.keys())
    selected = sorted(list(set(selected)))
    results = []
    errors = []

    def _process(symbol: str) -> dict[str, Any] | None:
        try:
            normalized = normalize_symbol(symbol, market)
            return analyze_symbol(normalized, source_profile=profiles.get(normalized), min_rr=min_rr, market=market)
        except MarketDataUnavailable as e:'''

content = re.sub(
    r'def scan_symbols\(symbols: list\[str\] \| None = None, min_rr: float \| None = None\) -> dict\[str, Any\]:.*?except MarketDataUnavailable as e:',
    new_scan,
    content,
    flags=re.DOTALL
)

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
