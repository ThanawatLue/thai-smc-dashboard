import re

with open('src/th_smc/engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_loop = '''    for row in metric_rows:
        raw_symbol = row["symbol"].replace(".BK", "")
        row["is_set100"] = row["symbol"] in set100_symbols
        row["is_canslim_growth"] = raw_symbol in growth_symbols
        # Swing universe: Market Cap >= 2B THB
        row["is_swing_universe"] = (row.get("market_cap") or 0.0) >= 2_000_000_000'''

new_loop = '''    for row in metric_rows:
        raw_symbol = row["symbol"].replace(".BK", "")
        if market == "TH":
            row["is_set100"] = row["symbol"] in set100_symbols
            row["is_canslim_growth"] = raw_symbol in growth_symbols
            row["is_swing_universe"] = (row.get("market_cap") or 0.0) >= 2_000_000_000
        elif market == "US":
            row["is_set100"] = True  # Proxy to pass VCP
            row["is_canslim_growth"] = True  # Proxy to pass CANSLIM
            row["is_swing_universe"] = True
        elif market == "GOLD":
            row["is_set100"] = False
            row["is_canslim_growth"] = False
            row["is_swing_universe"] = True'''
            
content = content.replace(old_loop, new_loop)

# Let's check _score_sources to make sure Gold passes momentum or dip
# Actually dip_pass and momentum_pass depend on SMA. Gold should have SMA from `_screen_metrics`.
# If GOLD doesn't pass the SMA check, we might want to force it to pass for testing, or it will just be empty.
# If it's an empty scan because no setup is armed, we shouldn't force it to have a setup if it really doesn't.
# But wait, Gold is just one symbol. If it's not in any source, it won't be analyzed.
# We should always add GOLD to MOMENTUM so it gets analyzed.

old_bucket_add = '''    for metrics in metric_rows:
        for source, (score, rating) in _score_sources(metrics).items():
            sources[source].append(_source_candidate(source, metrics, score, rating))'''

new_bucket_add = '''    for metrics in metric_rows:
        scored = _score_sources(metrics)
        if market == "GOLD":
            scored["MOMENTUM"] = (100, "GOLD always analyzed")
        for source, (score, rating) in scored.items():
            sources[source].append(_source_candidate(source, metrics, score, rating))'''

content = content.replace(old_bucket_add, new_bucket_add)

with open('src/th_smc/engine.py', 'w', encoding='utf-8') as f:
    f.write(content)
