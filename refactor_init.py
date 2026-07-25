import re

with open('src/th_smc/__init__.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('normalize_th_symbol', 'normalize_symbol')

with open('src/th_smc/__init__.py', 'w', encoding='utf-8') as f:
    f.write(content)
