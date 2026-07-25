import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace collect_candidate_sources signature
old_collect = 'def collect_candidate_sources(limit_per_source: int = 200) -> dict[str, Any]:'
new_collect = 'def collect_candidate_sources(market: str = "TH", limit_per_source: int = 200) -> dict[str, Any]:'
content = content.replace(old_collect, new_collect)

# Replace load_thai_market_snapshot() call with load_market_snapshot(market)
content = content.replace('metric_rows, universe_meta = load_thai_market_snapshot()', 'metric_rows, universe_meta = load_market_snapshot(market)')

# Replace load_ohlcv(normalized) call in collect_candidate_sources with load_ohlcv(normalized, market=market)
content = content.replace('df = load_ohlcv(normalized)', 'df = load_ohlcv(normalized, market=market)')

# Replace scan_symbols signature
old_scan = 'def scan_symbols(symbols: list[str] | None = None, min_rr: float = 2.0) -> dict[str, Any]:'
new_scan = 'def scan_symbols(symbols: list[str] | None = None, min_rr: float = 2.0, market: str = "TH") -> dict[str, Any]:'
content = content.replace(old_scan, new_scan)

# Replace collect_candidate_sources() call in scan_symbols
content = content.replace('source_payload = collect_candidate_sources()', 'source_payload = collect_candidate_sources(market=market)')

# In scan_symbols, we use selected = [normalize_symbol(item) for item in symbols] ... wait, normalize_symbol requires market
old_normalize = 'selected = [normalize_symbol(item) for item in symbols] if symbols else list(profiles.keys())'
new_normalize = 'selected = [normalize_symbol(item, market) for item in symbols] if symbols else list(profiles.keys())'
content = content.replace(old_normalize, new_normalize)

# Inside process_symbol, load_ohlcv must pass market
# Let's find process_symbol
content = content.replace('def process_symbol(symbol: str) -> dict[str, Any] | None:', 'def process_symbol(symbol: str, market_param: str) -> dict[str, Any] | None:')
content = content.replace('df = load_ohlcv(symbol, period="2y", interval="1d")', 'df = load_ohlcv(symbol, period="2y", interval="1d", market=market_param)')
content = content.replace('df_htf = load_ohlcv(symbol, period="5y", interval="1wk")', 'df_htf = load_ohlcv(symbol, period="5y", interval="1wk", market=market_param)')
content = content.replace('executor.submit(process_symbol, sym)', 'executor.submit(process_symbol, sym, market)')

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

