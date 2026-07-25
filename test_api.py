import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    res = urllib.request.urlopen('http://127.0.0.1:5080/api/scan?min_rr=2.0&market=US&refresh=1', context=ctx).read()
    data = json.loads(res)
    print("API Total Results:", len(data.get("results", [])))
    print("API Armed Count:", data.get("armed_count"))
    for idx, r in enumerate(data.get("results", [])):
        print(f"[{idx}] {r.get('symbol')} RR: {r.get('rr')} Decision: {r.get('decision')}")
except Exception as e:
    import traceback
    traceback.print_exc()
