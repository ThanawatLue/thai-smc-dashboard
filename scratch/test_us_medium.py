import json
import time
from th_smc.engine import scan_symbols
from th_smc.scraper import get_fundamental_extras

# Let's test fundamental extraction for AAPL
print("Testing Scraper for AAPL...")
extras = get_fundamental_extras("AAPL")
print(json.dumps(extras, indent=2))

# Let's test the engine flow for US_MEDIUM_TERM
print("\nTesting Engine scan for AAPL, MSFT in US_MEDIUM_TERM...")
start = time.time()
res = scan_symbols(["AAPL", "MSFT"], market="US_MEDIUM_TERM", min_rr=2.0)
end = time.time()

print(f"Scan completed in {end - start:.2f} seconds.")
results = res.get("results", [])
for r in results:
    if "FUNDAMENTAL" in r.get("sources", []):
        print(f"\n[{r['symbol']}] Passed FUNDAMENTAL!")
        print(f"  Decision: {r['decision']}")
        print(f"  Intrinsic Value: {r.get('intrinsic_value')}")
        print(f"  PEG Ratio: {r.get('peg_ratio')}")
        print(f"  ROE: {r.get('roe')}%")
        print(f"  FCF Margin: {r.get('fcf_margin')}%")
        print(f"  D/E: {r.get('debt_to_equity')}")
        print(f"  Revenue Growth 5y: {r.get('revenue_growth_5y')}%")
    else:
        print(f"\n[{r['symbol']}] Did not pass FUNDAMENTAL.")
