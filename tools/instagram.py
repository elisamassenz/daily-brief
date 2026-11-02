#!/usr/bin/env python3
"""Instagram carousel: render static/ig.html to JPEGs and post them, twice a day, from the GitHub workflow.

  python3 tools/instagram.py render BASE_URL OUT_DIR [--mode week]   preview, e.g. http://localhost:8787
  python3 tools/instagram.py due [--force am|pm|week]                 exit 0 if a post is due now (Eastern time)
  python3 tools/instagram.py prepare [--force …]                      render into site/ig/ before the Pages deploy
  python3 tools/instagram.py post                                     after the deploy: publish the carousel + a Story

Slots: 11:30–12:29 ET ("am") and 17:30–18:29 ET ("pm"); Sunday's pm post is the week recap. One-offs: run the
workflow by hand with ig_slot "intro" (the pinned intro post); `render … --mode about` makes the About highlight Stories. The workflow runs at
:11 and :41, so each slot is hit once (data/instagram.json records what was posted, which also stops the evening
post repeating the midday stories).

Needs repo secrets IG_USER_ID and IG_TOKEN (and IG_API_HOST if the token is a Facebook-login one:
graph.facebook.com; default graph.instagram.com). Rendering needs Playwright + Chromium."""
import json
import os
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
STATE = os.path.join(ROOT, "data", "instagram.json")
PENDING = os.path.join(ROOT, ".ig-pending.json")
PUBLIC = "https://wallflower.news"
API = "https://%s/v21.0" % (os.environ.get("IG_API_HOST") or "graph.instagram.com")


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


def now_et():
    return datetime.now(ZoneInfo("America/New_York"))


def slot(force=None):
    """The slot due right now, or None."""
    if force:
        return force
    t = now_et()
    mins = t.hour * 60 + t.minute
    if 11 * 60 + 30 <= mins < 12 * 60 + 30:
        return "am"
    if 17 * 60 + 30 <= mins < 18 * 60 + 30:
        return "week" if t.weekday() == 6 else "pm"
    return None


def due(force=None):
    """Slot name if a post is due and not yet made today, else None."""
    s = slot(force)
    if not s or not os.environ.get("IG_TOKEN"):
        return None
    posted = load(STATE, {}).get("posted", {})
    return None if (now_et().strftime("%Y-%m-%d") + "-" + s) in posted and not force else s


def render(base, out, query=""):
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1920}, device_scale_factor=1)
        page.goto(base.rstrip("/") + "/ig.html" + (("?" + query) if query else ""), wait_until="networkidle")
        page.wait_for_selector("body[data-ready]", timeout=30000)
        files = []
        for i, el in enumerate(page.query_selector_all(".slide"), 1):
            path = os.path.join(out, "slide-%d.jpg" % i)
            el.screenshot(path=path, type="jpeg", quality=92)
            files.append(os.path.basename(path))
        # the Story repeats slide 1, minus its swipe cue and page count (nothing to swipe to in a Story)
        first = page.query_selector(".slide")
        if first:
            page.evaluate("""() => { const f = document.querySelector('.slide .foot');
              if (f && f.lastElementChild) f.lastElementChild.textContent = ''; }""")
            first.screenshot(path=os.path.join(out, "story.jpg"), type="jpeg", quality=92)
        info = page.evaluate("window.IG")
        browser.close()
    info["files"] = files
    info["story"] = os.path.exists(os.path.join(out, "story.jpg"))
    save(os.path.join(out, "post.json"), info)
    with open(os.path.join(out, "caption.txt"), "w") as f:
        f.write(info["caption"])
    return info


def prepare(force=None):
    s = due(force)
    if not s:
        print("instagram: nothing due")
        return
    today = now_et().strftime("%Y-%m-%d")
    posted = load(STATE, {}).get("posted", {})
    skip = "|".join(k for name, p in posted.items() if name.startswith(today) for k in p.get("keys", []))
    query = urllib.parse.urlencode({k: v for k, v in (("mode", s if s in ("week", "intro") else ""), ("skip", skip)) if v})
    # serve the freshly built site locally (the fonts kit allows localhost)
    srv = ThreadingHTTPServer(("127.0.0.1", 8790), partial(SimpleHTTPRequestHandler, directory=SITE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    stamp = "%s-%s" % (today, s)
    try:
        info = render("http://127.0.0.1:8790", os.path.join(SITE, "ig", stamp), query)
    finally:
        srv.shutdown()
    info.update(slot=s, stamp=stamp)
    save(PENDING, info)
    print("instagram: rendered %s (%d slides)" % (stamp, len(info["files"])))


def api(path, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    req = urllib.request.Request(API + path, data=urllib.parse.urlencode(params).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError("%s %s" % (path, e.read().decode()[:400]))


def status(container):
    url = "%s/%s?fields=status_code&access_token=%s" % (API, container, urllib.parse.quote(os.environ["IG_TOKEN"]))
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r).get("status_code")


def wait_ready(container):
    for _ in range(30):
        code = status(container)
        if code == "FINISHED":
            return
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError("container %s: %s" % (container, code))
        time.sleep(4)
    raise RuntimeError("container %s never finished" % container)


def image_item(user, url, alt, **extra):
    try:   # alt text for screen readers; retried without it if the API version rejects the field
        return api("/%s/media" % user, image_url=url, alt_text=alt[:1000], **extra)["id"]
    except RuntimeError as e:
        if "alt_text" not in str(e):
            raise
        return api("/%s/media" % user, image_url=url, **extra)["id"]


def post():
    info = load(PENDING, None)
    if not info:
        print("instagram: nothing to post")
        return
    user = os.environ["IG_USER_ID"]
    urls = ["%s/ig/%s/%s" % (PUBLIC, info["stamp"], f) for f in info["files"]]
    for _ in range(20):   # wait for the Pages deploy to serve the images
        try:
            urllib.request.urlopen(urls[0], timeout=20)
            break
        except Exception:
            time.sleep(15)
    alts = info.get("alts", [])
    children = [image_item(user, u, alts[i] if i < len(alts) else "", is_carousel_item="true") for i, u in enumerate(urls)]
    for c in children:
        wait_ready(c)
    carousel = api("/%s/media" % user, media_type="CAROUSEL", children=",".join(children), caption=info["caption"])["id"]
    wait_ready(carousel)
    media = api("/%s/media_publish" % user, creation_id=carousel)["id"]
    print("instagram: posted", media)
    try:   # also share the first slide to the Story
        story_url = "%s/ig/%s/story.jpg" % (PUBLIC, info["stamp"]) if info.get("story") else urls[0]
        story = api("/%s/media" % user, media_type="STORIES", image_url=story_url)["id"]
        wait_ready(story)
        api("/%s/media_publish" % user, creation_id=story)
    except Exception as e:
        print("instagram: story skipped:", e)
    state = load(STATE, {})
    posted = state.setdefault("posted", {})
    posted[info["stamp"]] = {"id": media, "keys": info.get("keys", []), "slides": len(urls)}
    state["posted"] = {k: posted[k] for k in sorted(posted)[-60:]}
    save(STATE, state)
    os.remove(PENDING)


if __name__ == "__main__":
    args = sys.argv[1:]
    force = args[args.index("--force") + 1] if "--force" in args else (os.environ.get("IG_FORCE") or None)   # manual run from Actions
    cmd = args[0] if args else ""
    if cmd == "render":
        mode = args[args.index("--mode") + 1] if "--mode" in args else ""
        print(json.dumps(render(args[1], args[2], "mode=" + mode if mode else ""), indent=1))
    elif cmd == "due":
        sys.exit(0 if due(force) else 1)
    elif cmd == "prepare":
        prepare(force)
    elif cmd == "post":
        post()
    else:
        sys.exit(__doc__)
