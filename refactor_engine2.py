import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix analyze_symbol signature
old_analyze = '''def analyze_symbol(
    symbol: str,
    data: pd.DataFrame | None = None,
    source_profile: dict[str, Any] | None = None,
    min_rr: float = 2.0,
) -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    df = (data.copy() if data is not None else load_ohlcv(normalized)).dropna().reset_index(drop=True)'''

new_analyze = '''def analyze_symbol(
    symbol: str,
    data: pd.DataFrame | None = None,
    source_profile: dict[str, Any] | None = None,
    min_rr: float = 2.0,
    market: str = "TH",
) -> dict[str, Any]:
    normalized = normalize_symbol(symbol, market)
    df = (data.copy() if data is not None else load_ohlcv(normalized, market=market)).dropna().reset_index(drop=True)'''
content = content.replace(old_analyze, new_analyze)

# Fix scan_symbols internal analyze wrapper
old_wrapper = '''    def _analyze_selected(symbol: str) -> dict[str, Any] | None:
        try:
            normalized = normalize_symbol(symbol)
            return analyze_symbol(normalized, source_profile=profiles.get(normalized), min_rr=min_rr)'''

new_wrapper = '''    def _analyze_selected(symbol: str) -> dict[str, Any] | None:
        try:
            normalized = normalize_symbol(symbol, market)
            return analyze_symbol(normalized, source_profile=profiles.get(normalized), min_rr=min_rr, market=market)'''
content = content.replace(old_wrapper, new_wrapper)

# Fix hardcoded "market": "TH" in scan_symbols
content = content.replace('"market": "TH",\n        "generated_at"', '"market": market,\n        "generated_at"')

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

