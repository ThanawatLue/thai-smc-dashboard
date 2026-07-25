import cloudscraper
import re

def test():
    scraper = cloudscraper.create_scraper()
    resp = scraper.get('https://www.alphaspread.com/security/nyse/jpm/summary')
    match = re.search(r'class="intrinsic-value">\$([0-9.]+)', resp.text)
    if not match:
        match = re.search(r'>\$([0-9.]+)<', resp.text)
    print("Value:", match.group(1) if match else "Not found")
    print("Snippet:", resp.text[5000:6000])
    print("Value:", match.group(1) if match else "Not found")

test()
