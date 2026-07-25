import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. replace normalize_th_symbol
content = re.sub(
    r'def normalize_th_symbol\(raw: str\) -> str:.*?return symbol if symbol\.endswith\("\.BK"\) else f"\{symbol\}\.BK"',
    '''def normalize_symbol(raw: str, market: str = "TH") -> str:
    symbol = raw.strip().upper()
    if not symbol:
        raise ValueError("symbol is empty")
    if market == "TH":
        if "." in symbol and not symbol.endswith(".BK"):
            raise ValueError("only Thai .BK symbols are allowed")
        return symbol if symbol.endswith(".BK") else f"{symbol}.BK"
    return symbol''',
    content,
    flags=re.DOTALL
)

# Replace function calls
content = content.replace('normalize_th_symbol(', 'normalize_symbol(')

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
