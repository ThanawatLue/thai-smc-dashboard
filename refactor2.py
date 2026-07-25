import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update load_ohlcv
# def load_ohlcv(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
#     normalized = normalize_symbol(symbol)
content = re.sub(
    r'def load_ohlcv\(symbol: str, period: str = "1y", interval: str = "1d"\) -> pd\.DataFrame:\n    normalized = normalize_symbol\(symbol\)',
    '''def load_ohlcv(symbol: str, period: str = "1y", interval: str = "1d", market: str = "TH") -> pd.DataFrame:
    normalized = normalize_symbol(symbol, market)''',
    content,
    flags=re.DOTALL
)

# 2. Update _tv_symbol_to_yf
# def _tv_symbol_to_yf(ticker: str, name: str | None = None) -> str:
#     raw = (name or ticker.split(":")[-1]).strip().upper()
#     return normalize_symbol(raw)
content = re.sub(
    r'def _tv_symbol_to_yf\(ticker: str, name: str \| None = None\) -> str:\n    raw = \(name or ticker\.split\(":"\)\[-1\]\)\.strip\(\)\.upper\(\)\n    return normalize_symbol\(raw\)',
    '''def _tv_symbol_to_yf(ticker: str, name: str | None = None, market: str = "TH") -> str:
    if market == "US":
        raw = ticker.split(":")[-1].strip().upper()
    else:
        raw = (name or ticker.split(":")[-1]).strip().upper()
    return normalize_symbol(raw, market)''',
    content,
    flags=re.DOTALL
)

# 3. Update _is_operating_common_stock
# def _is_operating_common_stock(item: dict[str, Any]) -> bool:
#     if item.get("type") != "stock" or item.get("subtype") != "common":
#         return False
#     exchange = str(item.get("exchange") or "").upper()
#     if exchange not in {"SET", "MAI"}:
#         return False
content = re.sub(
    r'def _is_operating_common_stock\(item: dict\[str, Any\]\) -> bool:\n    if item\.get\("type"\) != "stock" or item\.get\("subtype"\) != "common":\n        return False\n    exchange = str\(item\.get\("exchange"\) or ""\)\.upper\(\)\n    if exchange not in \{"SET", "MAI"\}:\n        return False',
    '''def _is_operating_common_stock(item: dict[str, Any], market: str = "TH") -> bool:
    if item.get("type") != "stock" or item.get("subtype") != "common":
        return False
    if market == "TH":
        exchange = str(item.get("exchange") or "").upper()
        if exchange not in {"SET", "MAI"}:
            return False''',
    content,
    flags=re.DOTALL
)


with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
