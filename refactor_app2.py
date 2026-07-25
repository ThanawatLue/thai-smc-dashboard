import re

with open('dashboard/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update api_sources
old_sources = '''@app.get("/api/sources")
def api_sources():
    return jsonify(collect_candidate_sources())'''

new_sources = '''@app.get("/api/sources")
def api_sources():
    market = request.args.get("market", "TH").upper()
    if market not in ["TH", "US", "GOLD"]:
        market = "TH"
    return jsonify(collect_candidate_sources(market=market))'''

content = content.replace(old_sources, new_sources)

# Update api_symbol
old_symbol = '''@app.get("/api/symbol/<symbol>")
def api_symbol(symbol: str):
    return jsonify(analyze_symbol(symbol))'''

new_symbol = '''@app.get("/api/symbol/<symbol>")
def api_symbol(symbol: str):
    market = request.args.get("market", "TH").upper()
    if market not in ["TH", "US", "GOLD"]:
        market = "TH"
    return jsonify(analyze_symbol(symbol, market=market))'''

content = content.replace(old_symbol, new_symbol)

with open('dashboard/app.py', 'w', encoding='utf-8') as f:
    f.write(content)
