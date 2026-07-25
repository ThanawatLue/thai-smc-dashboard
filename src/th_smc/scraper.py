import urllib.request
import urllib.error
import re
import pandas as pd
import yfinance as yf
from io import StringIO
import time
import random

def get_sp500_symbols():
    try:
        req = urllib.request.Request(
            'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        html = urllib.request.urlopen(req).read().decode('utf-8')
        df = pd.read_html(StringIO(html))[0]
        # Clean symbols (e.g., BRK.B -> BRK-B)
        symbols = df['Symbol'].str.replace('.', '-', regex=False).tolist()
        return symbols
    except Exception as e:
        print(f"Error fetching S&P 500 list: {e}")
        return []

def get_fundamental_extras(symbol, exchange=""):
    # 1. PEG Ratio and Target Price (Proxy for Intrinsic Value) via yfinance
    peg_ratio = None
    intrinsic_value = None
    try:
        info = yf.Ticker(symbol).info
        peg_ratio = info.get('pegRatio')
        
        # Use targetMeanPrice or targetMedianPrice as Intrinsic Value proxy
        # since it's the Wall St consensus target.
        intrinsic_value = info.get('targetMeanPrice') or info.get('targetMedianPrice')
        
    except Exception as e:
        print(f"Error fetching yfinance fundamentals for {symbol}: {e}")

    # 2. Try fetching true Intrinsic Value from AlphaSpread using cloudscraper
    try:
        import cloudscraper
        import re
        scraper = cloudscraper.create_scraper()
        
        # Normalize exchange for URL (e.g. "NASDAQ" -> "nasdaq", "NYSE" -> "nyse")
        exch_str = exchange.lower()
        if not exch_str:
            # Guess based on common patterns or just default
            exch_str = "nasdaq"
            
        url = f"https://www.alphaspread.com/security/{exch_str}/{symbol.lower()}/summary"
        resp = scraper.get(url, timeout=10)
        if resp.status_code == 200:
            match = re.search(r'The <b[^>]*>intrinsic value</b>.*?Base Case.*?restriction-sensitive-data[^>]*>([0-9.]+)<', resp.text, re.DOTALL)
            if not match:
                match = re.search(r'class="price-ladder__label">Intrinsic Value</span>.*?class="price-ladder__value">.*?([0-9.]+)', resp.text, re.DOTALL)
            if match:
                intrinsic_value = float(match.group(1))
    except Exception as e:
        print(f"Error fetching AlphaSpread for {symbol}: {e}")

    # Delay to avoid hitting rate limits
    time.sleep(random.uniform(0.1, 0.3))
    
    return {
        "peg_ratio": peg_ratio,
        "intrinsic_value": intrinsic_value
    }

if __name__ == "__main__":
    # Test
    print("S&P500 length:", len(get_sp500_symbols()))
    print("AAPL Extras:", get_fundamental_extras("AAPL"))
    print("JPM Extras:", get_fundamental_extras("JPM"))
