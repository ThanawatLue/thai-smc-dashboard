from src.th_smc.engine import scan_symbols
import time
import json

t0 = time.time()
try:
    res = scan_symbols(min_rr=2.0, market='US')
    with open('test_res.txt', 'w') as f:
        f.write(f"Time: {time.time()-t0}\n")
        f.write(f"Count: {res.get('count')}\n")
        f.write(f"Error: {res.get('error')}\n")
except Exception as e:
    with open('test_res.txt', 'w') as f:
        f.write(str(e))
