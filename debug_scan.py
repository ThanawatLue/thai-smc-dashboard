from src.th_smc.engine import scan_symbols, collect_candidate_sources
import sys

def main():
    try:
        data = scan_symbols(min_rr=2.0, market='US')
        print(f"Count: {len(data['results'])}")
        for r in data['results']:
            print(f"{r['symbol']} - RR: {r['rr']}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
