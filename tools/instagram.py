#!/usr/bin/env python3
"""Instagram carousel: render static/ig.html to JPEGs and post them, twice a day, from the GitHub workflow.

  python3 tools/instagram.py render BASE_URL OUT_DIR [--mode week]   preview, e.g. http://localhost:8787
  python3 tools/instagram.py due [--force am|pm|week]                 exit 0 if a post is due now (Eastern time)
  python3 tools/instagram.py prepare [--force …]                      render into site/ig/ before the Pages deploy
  python3 tools/instagram.py post                                     after the deploy: publish the carousel + a Story
                                                                      (+ a Reel of the same slides, midday only)
  python3 tools/instagram.py reel DIR                                 build reel.mp4 from DIR's slides (preview)

Slots: 11:30–14:29 ET ("am") and 17:30–20:29 ET ("pm"), posting at the first run inside each; Sunday's pm post is the week recap. One-offs: run the
workflow by hand with ig_slot "intro" (the pinned intro post); `render … --mode about` makes the About highlight Stories. The workflow runs at
:11 and :41, so each slot is hit once (data/instagram.json records what was posted, which also stops the evening
post repeating the midday stories).

Needs repo secrets IG_USER_ID and IG_TOKEN (and IG_API_HOST if the token is a Facebook-login one:
graph.facebook.com; default graph.instagram.com). Rendering needs Playwright + Chromium."""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
STATE = os.path.join(ROOT, "data", "instagram.json")
PENDING = os.path.join(ROOT, ".ig-pending.json")
PUBLIC = "https://wallflower.news"
API = "https://%s/v26.0" % (os.environ.get("IG_API_HOST") or "graph.instagram.com")


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
    # 3-hour windows: GitHub's scheduler often runs hours late, so a late run still catches its slot (once)
    if 11 * 60 + 30 <= mins < 14 * 60 + 30:
        return "am"
    if 17 * 60 + 30 <= mins < 20 * 60 + 30:
        return "week" if t.weekday() == 6 else "pm"
    return None


def due(force=None):
    """Slot name if a post is due and not yet made today, else None."""
    s = slot(force)
    if not s or not os.environ.get("IG_TOKEN"):
        return None
    state = load(STATE, {})
    if not force and state.get("paused_until", "") > now_et().isoformat():   # Instagram blocked us: wait it out
        return None
    posted = state.get("posted", {})
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


REEL_HOLD, REEL_FADE = 4.0, 0.5   # seconds each slide holds, crossfade between slides


def make_reel(out, files):
    """The carousel as a short vertical video (Reels reach people who don't follow yet): each 4:5 slide centered
    on a 9:16 page in the site's paper color, crossfading. Silent. Needs ffmpeg."""
    n = len(files)
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    for f in files:
        args += ["-loop", "1", "-t", str(REEL_HOLD + REEL_FADE), "-i", os.path.join(out, f)]
    args += ["-f", "lavfi", "-t", str(n * REEL_HOLD + REEL_FADE), "-i", "anullsrc=r=44100:cl=stereo"]
    chain = [f"[{i}:v]scale=1080:1350,pad=1080:1920:0:285:color=0xf4efe7,fps=30,format=yuv420p,setsar=1[v{i}]" for i in range(n)]
    last = "v0"
    for i in range(1, n):
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration={REEL_FADE}:offset={i * REEL_HOLD:.2f}[x{i}]")
        last = f"x{i}"
    args += ["-filter_complex", ";".join(chain), "-map", f"[{last}]", "-map", f"{n}:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-shortest", "-movflags", "+faststart", os.path.join(out, "reel.mp4")]
    subprocess.run(args, check=True)


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
    if s == "am":   # one Reel a day, from the midday carousel
        try:
            out = os.path.join(SITE, "ig", stamp)   # opens on the Story copy of slide 1: no swipe cue in a video
            make_reel(out, (["story.jpg"] if info.get("story") else info["files"][:1]) + info["files"][1:])
            info["reel"] = True
        except Exception as e:
            print("instagram: reel skipped:", e)
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


def wait_ready(container, tries=30):
    for _ in range(tries):
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


BLOCKED = ("2207051", "action is blocked", "Application request limit reached")
PAUSE_HOURS = 24


def post():
    """Post the pending carousel. If Instagram flags the account, pause posting for a day instead of retrying
    every half hour (repeated attempts can make a block last longer) and end without a failed run."""
    info = load(PENDING, {})
    try:   # another run may have posted this slot while we were rendering: check the latest state on GitHub
        subprocess.run(["git", "fetch", "-q", "origin", "main"], capture_output=True, timeout=60)
        remote = json.loads(subprocess.run(["git", "show", "origin/main:data/instagram.json"],
                                           capture_output=True, text=True, timeout=30).stdout or "{}")
        if info.get("stamp") in remote.get("posted", {}) or remote.get("paused_until", "") > now_et().isoformat():
            print("instagram: %s already posted or paused by another run, skipping" % info.get("stamp"))
            os.remove(PENDING)
            return
    except Exception as e:
        print("instagram: could not check remote state:", e)
    try:
        publish()
    except RuntimeError as e:
        if not any(b in str(e) for b in BLOCKED):
            raise
        state = load(STATE, {})
        if "media_publish" in str(e):   # Instagram sometimes posts it anyway despite the error: never post it twice
            info = load(PENDING, {})
            state.setdefault("posted", {})[info.get("stamp", "")] = {"id": None, "keys": info.get("keys", []), "blocked": True}
        state["paused_until"] = (now_et() + timedelta(hours=PAUSE_HOURS)).isoformat()
        save(STATE, state)
        os.remove(PENDING)
        print("instagram: blocked by Instagram, paused until", state["paused_until"], "-", e)


def publish():
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
    if info.get("reel"):   # the same slides as a Reel, kept off the grid so it doesn't repeat the carousel there
        try:
            reel = api("/%s/media" % user, media_type="REELS", video_url="%s/ig/%s/reel.mp4" % (PUBLIC, info["stamp"]),
                       caption=info["caption"], share_to_feed="false")["id"]
            wait_ready(reel, tries=90)   # video processing takes a few minutes
            api("/%s/media_publish" % user, creation_id=reel)
            print("instagram: reel posted")
        except Exception as e:
            print("instagram: reel skipped:", e)
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
    elif cmd == "reel":
        make_reel(args[1], sorted(f for f in os.listdir(args[1]) if f.startswith("slide-")))
    elif cmd == "due":
        sys.exit(0 if due(force) else 1)
    elif cmd == "prepare":
        prepare(force)
    elif cmd == "post":
        post()
    else:
        sys.exit(__doc__)
