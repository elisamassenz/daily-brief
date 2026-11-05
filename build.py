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

sys.path.insert(0, os.path.join(server.ROOT, "tools"))
import focal

SITE = os.path.join(server.ROOT, "site")
FOCAL_CACHE = os.path.join(server.RUNTIME, "focal_cache.json")
LAST_MARKETS = os.path.join(server.RUNTIME, "markets_last.json")  # data/ on GitHub, .local/ on your Mac


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
    # crop photos to the faces in them (see tools/focal.py)
    images = [s.get("image") for s in payload["trending"]] + [i.get("image") for h in payload["headlines"].values() for i in h]
    focal_cache = server.load_json(FOCAL_CACHE, {})
    if focal.update(images, focal_cache):
        for url in list(focal_cache)[:max(0, len(focal_cache) - 3000)]:
            focal_cache.pop(url)
        server.save_json(FOCAL_CACHE, focal_cache)
    payload = dict(payload, focal={u: focal_cache[u] for u in images if focal_cache.get(u)})
    with open(os.path.join(SITE, "app.js"), "rb") as f:   # a page left open on an older app.js reloads itself
        payload = dict(payload, app_version=hashlib.sha1(f.read()).hexdigest()[:10])
    with open(os.path.join(SITE, "data", "news.json"), "w") as f:
        json.dump(payload, f)
    with open(os.path.join(SITE, "data", "markets.json"), "w") as f:
        json.dump(markets, f)
    if os.path.exists(server.TOP_STORIES_FILE):   # each day's cover story, for the Sunday Instagram recap
        shutil.copy(server.TOP_STORIES_FILE, os.path.join(SITE, "data", "top_stories.json"))
    with open(os.path.join(SITE, "data", "archive.json"), "w") as f:   # topic search
        json.dump(server.archive(), f, separators=(",", ":"))


    index = os.path.join(SITE, "index.html")
    with open(index) as f:
        html = f.read()
    # bake the name into the title, masthead and Home Screen label so it shows before data loads
    for old, new in ((">Wallflower<", ">%s<"), ('content="Wallflower"', 'content="%s"')):
        html = html.replace(old, new % server.SITE_TITLE)
    html = html.replace("<head>", '<head>\n<meta name="static-build" content="1">', 1)
    if server.GA_ID:   # Google Analytics, public site only
        html = html.replace("</head>", ('<script async src="https://www.googletagmanager.com/gtag/js?id={0}"></script>\n'
            # visiting wallflower.news/?me once stops counting that device (the owner's own visits)
            '<script>try{{if(/[?&]me\\b/.test(location.search))localStorage.setItem("wallflower.notrack","1");'
            'if(localStorage.getItem("wallflower.notrack"))window["ga-disable-{0}"]=true}}catch(e){{}}'
            'window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}'
            'gtag("js",new Date());gtag("config","{0}");</script>\n</head>').format(server.GA_ID), 1)
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
