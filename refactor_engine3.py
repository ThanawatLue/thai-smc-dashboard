import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove where("is_primary", True)
old_line = 'q = q.set_markets("america").where("is_primary", True).order_by("market_cap_basic", \nascending=False).limit(500)'
new_line = 'q = q.set_markets("america").order_by("market_cap_basic", ascending=False).limit(500)'
content = content.replace(old_line, new_line)

# If the newline was different
old_line2 = 'q = q.set_markets("america").where("is_primary", True).order_by("market_cap_basic", \nascending=False).limit(500)'.replace('\\n', '\n')
content = content.replace('q = q.set_markets("america").where("is_primary", True).order_by("market_cap_basic", \nascending=False).limit(500)', 'q = q.set_markets("america").order_by("market_cap_basic", ascending=False).limit(500)')
content = re.sub(r'q = q\.set_markets\("america"\)\.where\("is_primary", True\)\.order_by\("market_cap_basic",\s*ascending=False\)\.limit\(500\)', 'q = q.set_markets("america").order_by("market_cap_basic", ascending=False).limit(500)', content)

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

