import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: _screen_metrics definition
old_def = 'def _screen_metrics(symbol: str, df: pd.DataFrame) -> dict[str, Any]:'
new_def = 'def _screen_metrics(symbol: str, df: pd.DataFrame, market: str = "TH") -> dict[str, Any]:'
content = content.replace(old_def, new_def)

# Fix 2: inside _screen_metrics, the return dict
old_ret = '''    return {
        "symbol": normalize_symbol(symbol),
        "name": normalize_symbol(symbol),'''
new_ret = '''    return {
        "symbol": normalize_symbol(symbol, market),
        "name": normalize_symbol(symbol, market),'''
content = content.replace(old_ret, new_ret)

# Fix 3: where _screen_metrics is called in collect_candidate_sources
old_call = 'enriched_rows.append(_screen_metrics(normalized, df))'
new_call = 'enriched_rows.append(_screen_metrics(normalized, df, market=market))'
content = content.replace(old_call, new_call)

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
