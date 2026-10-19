#!/usr/bin/env python3
"""Build the public, read-only version of the Daily Brief as plain files in site/.

Run by the GitHub workflow every 30 minutes (and runnable locally: `python3 build.py`).
It reuses server.py's fetching and analysis, then writes the page plus two data files
(data/news.json, data/markets.json) that the page reads instead of the live server.
"""
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone

import server

SITE = os.path.join(server.ROOT, "site")
LAST_MARKETS = os.path.join(server.RUNTIME, "markets_last.json")  # data/ on GitHub, .local/ on your Mac


def write_archive(path, days=28):
    """Compact list of the last 4 weeks of saved headlines, so visitors can track their own
    topics on the public site (searched in their browser, no server needed)."""
    today = datetime.now(timezone.utc).date()
    day_list = [(today - timedelta(days=k)).isoformat() for k in range(days - 1, -1, -1)]
    pubs = [s["id"] for s in server.SOURCES]
    items = []
    for di, day in enumerate(day_list):
        for a in server.load_json(server.history_path(day), {}).values():
            if a.get("pub") in pubs:
                items.append([di, pubs.index(a["pub"]), a["title"], a.get("desc", ""), a["link"]])
    with open(path, "w") as f:
        json.dump({"days": day_list, "pubs": pubs, "items": items}, f, separators=(",", ":"))
    return len(items)


def main():
    server.refresh()
    payload = server.state["payload"]
    if not payload:
        sys.exit("refresh failed: %s" % server.state["error"])

    quotes, movers = server.markets(), server.movers()
    if quotes:
        server.save_json(LAST_MARKETS, {"quotes": quotes, "movers": movers})
    markets = server.load_json(LAST_MARKETS, {"quotes": quotes, "movers": movers})  # keep the last good data if Yahoo refuses

    shutil.rmtree(SITE, ignore_errors=True)
    shutil.copytree(server.STATIC, SITE)
    shutil.copytree(server.LOGOS, os.path.join(SITE, "logo"))
    os.makedirs(os.path.join(SITE, "data"))
    with open(os.path.join(SITE, "data", "news.json"), "w") as f:
        json.dump(payload, f)
    with open(os.path.join(SITE, "data", "markets.json"), "w") as f:
        json.dump(markets, f)

    write_archive(os.path.join(SITE, "data", "archive.json"))

    index = os.path.join(SITE, "index.html")
    with open(index) as f:
        html = f.read()
    html = html.replace("Elisa’s Daily Brief", server.SITE_TITLE)  # bake the name in so it shows before data loads
    html = html.replace("<head>", '<head>\n<meta name="static-build" content="1">', 1)
    # version the stylesheet and script so browsers fetch the new copy after every change
    for name in ("style.css", "app.js"):
        with open(os.path.join(SITE, name), "rb") as f:
            digest = hashlib.sha1(f.read()).hexdigest()[:10]
        html = html.replace('"%s"' % name, '"%s?v=%s"' % (name, digest))
    with open(index, "w") as f:
        f.write(html)
    open(os.path.join(SITE, ".nojekyll"), "w").close()
    server.log("site built — %d stories, %d quotes" % (len(payload["trending"]), len(markets.get("quotes") or [])))


if __name__ == "__main__":
    main()
