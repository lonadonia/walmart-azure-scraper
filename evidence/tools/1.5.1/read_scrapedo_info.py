"""Free Scrape.do /info reading for the Walmart task. Prints and stores no key."""
import datetime as dt, json, pathlib, sys
import httpx
root = pathlib.Path(sys.argv[1])
key = ""
for line in (root / "data/local/scrapedo.env").read_text(encoding="utf-8-sig").splitlines():
    line = line.strip()
    if line.startswith("SCRAPEDO_API_KEY"):
        key = line.split("=", 1)[1].strip().strip("'\"")
assert key
now = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
r = httpx.get("https://api.scrape.do/info", params={"token": key}, timeout=30)
body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"text": r.text[:200]}
out = {"started_at_utc": now, "method": "GET", "url": "https://api.scrape.do/info?token=<key removed>",
       "status": r.status_code, "headers_date": r.headers.get("date"), "body": body}
text = json.dumps(out, indent=1).replace(key, "<key removed>")
(pathlib.Path(sys.argv[2]) / f"scrapedo_info_{now.replace(':', '')}.json").write_text(text, encoding="utf-8")
print(text)
