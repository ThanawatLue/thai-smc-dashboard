import re

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace _get_cache_path
old_cache_path = '''def _get_cache_path(min_rr: float) -> Path:
    return BASE_DIR / "state" / f"last_scan_{min_rr}.json"'''

new_cache_path = '''def _get_cache_path(min_rr: float, market: str) -> Path:
    return BASE_DIR / "state" / f"last_scan_{market}_{min_rr}.json"'''

content = content.replace(old_cache_path, new_cache_path)

# Update _load_scan_cache
content = content.replace('def _load_scan_cache(min_rr: float) -> dict | None:', 'def _load_scan_cache(min_rr: float, market: str) -> dict | None:')
content = content.replace('key = str(min_rr)', 'key = f"{market}_{min_rr}"')
content = content.replace('_get_cache_path(min_rr)', '_get_cache_path(min_rr, market)')

# Update _save_scan_cache
content = content.replace('def _save_scan_cache(data: dict, min_rr: float) -> None:', 'def _save_scan_cache(data: dict, min_rr: float, market: str) -> None:')
content = content.replace('_SCAN_CACHE[str(min_rr)]', '_SCAN_CACHE[f"{market}_{min_rr}"]')

# Update api_scan
old_api_scan = '''@app.get("/api/scan")
def api_scan():
    raw = request.args.get("symbols", "")
    symbols = [part.strip() for part in raw.split(",") if part.strip()] if raw else None
    refresh = request.args.get("refresh") == "1"
    min_rr_str = request.args.get("min_rr", "2.0")
    try:
        min_rr = float(min_rr_str)
    except ValueError:
        min_rr = 2.0

    if symbols:
        return jsonify(scan_symbols(symbols, min_rr=min_rr))

    now = time.time()
    cached = _load_scan_cache(min_rr)
    if cached and not refresh and now - float(_SCAN_CACHE.get(str(min_rr), {}).get("at", 0.0)) < _SCAN_TTL_SECONDS:
        return jsonify(cached)

    with _SCAN_LOCK:
        now = time.time()
        cached = _load_scan_cache(min_rr)
        if cached and not refresh and now - float(_SCAN_CACHE.get(str(min_rr), {}).get("at", 0.0)) < _SCAN_TTL_SECONDS:
            return jsonify(cached)
        data = scan_symbols(min_rr=min_rr)
        _save_scan_cache(data, min_rr)
        return jsonify(data)'''

new_api_scan = '''@app.get("/api/scan")
def api_scan():
    raw = request.args.get("symbols", "")
    symbols = [part.strip() for part in raw.split(",") if part.strip()] if raw else None
    refresh = request.args.get("refresh") == "1"
    min_rr_str = request.args.get("min_rr", "2.0")
    market = request.args.get("market", "TH").upper()
    if market not in ["TH", "US", "GOLD"]:
        market = "TH"
    
    try:
        min_rr = float(min_rr_str)
    except ValueError:
        min_rr = 2.0

    if symbols:
        return jsonify(scan_symbols(symbols, min_rr=min_rr, market=market))

    cache_key = f"{market}_{min_rr}"
    now = time.time()
    cached = _load_scan_cache(min_rr, market)
    if cached and not refresh and now - float(_SCAN_CACHE.get(cache_key, {}).get("at", 0.0)) < _SCAN_TTL_SECONDS:
        return jsonify(cached)

    with _SCAN_LOCK:
        now = time.time()
        cached = _load_scan_cache(min_rr, market)
        if cached and not refresh and now - float(_SCAN_CACHE.get(cache_key, {}).get("at", 0.0)) < _SCAN_TTL_SECONDS:
            return jsonify(cached)
        data = scan_symbols(min_rr=min_rr, market=market)
        _save_scan_cache(data, min_rr, market)
        return jsonify(data)'''

content = content.replace(old_api_scan, new_api_scan)

with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
