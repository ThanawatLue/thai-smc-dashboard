import re

with open('dashboard/templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_cache_key = 'const CACHE_KEY = "thai-smc-last-scan-v3";'
new_cache_key = 'const getCacheKey = () => `smc-last-scan-${currentMarket}-${document.getElementById("minRrInput").value}`;'

content = content.replace(old_cache_key, new_cache_key)

content = content.replace('localStorage.setItem(CACHE_KEY, JSON.stringify(payload));', 'localStorage.setItem(getCacheKey(), JSON.stringify(payload));')
content = content.replace('const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || "null");', 'const cached = JSON.parse(localStorage.getItem(getCacheKey()) || "null");')
content = content.replace('localStorage.removeItem(CACHE_KEY);', 'localStorage.removeItem(getCacheKey());')

with open('dashboard/templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
