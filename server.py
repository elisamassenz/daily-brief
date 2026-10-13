#!/usr/bin/env python3
"""Daily Brief — a local news dashboard.

Run:  python3 server.py   then open http://localhost:8787
Standard library only. Feeds refresh every 20 minutes in the background;
every headline seen is kept in data/history/ so trends can be tracked over weeks.
"""
import html
import json
import math
import os
import re
import ssl
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from sources import DEFAULT_TOPICS, FINANCE_PUBS, MARKETS, NEGATIVE, POSITIVE, SECTIONS, SITE_TITLE, SOURCES, THEMES

ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(ROOT, "static")
DATA = os.path.join(ROOT, "data")
# GitHub's build keeps its history in the repo (data/); the local app keeps its own in .local/
# so the two never edit the same files.
CI = bool(os.environ.get("GITHUB_ACTIONS"))
RUNTIME = DATA if CI else os.path.join(ROOT, ".local")
HIST = os.path.join(RUNTIME, "history")
LOGOS = os.path.join(DATA, "logos")
TOPICS_FILE = os.path.join(DATA, "topics.json")
OG_CACHE_FILE = os.path.join(RUNTIME, "og_cache.json")
if not CI and not os.path.isdir(HIST) and os.path.isdir(os.path.join(DATA, "history")):
    import shutil
    shutil.copytree(os.path.join(DATA, "history"), HIST)  # start the local history from the repo's
for d in (DATA, HIST, LOGOS):
    os.makedirs(d, exist_ok=True)

PORT = int(os.environ.get("PORT", 8787))
REFRESH_SECONDS = 20 * 60
TOPIC_REFRESH_SECONDS = 6 * 3600
HISTORY_DAYS = 60
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")
SSL_CTX = ssl.create_default_context()
SRC = {s["id"]: s for s in SOURCES}
DOMAIN_TO_ID = {s["domain"]: s["id"] for s in SOURCES}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def http_get(url, timeout=12, maxbytes=4_000_000, ua=UA):
    req = urllib.request.Request(url, headers={
        "User-Agent": ua, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
        return r.read(maxbytes), r.headers.get_content_type()


def google_news_url(query):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(
        {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)


# ---------------------------------------------------------------- feed parsing

TAG_RE = re.compile(r"<[^>]+>")
IMG_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)
OG_RE = re.compile(r"<meta[^>]+(?:property|name)=[\"'](?:og:image|twitter:image)(?::src)?[\"'][^>]*>", re.I)
CONTENT_ATTR_RE = re.compile(r"content=[\"']([^\"']+)[\"']", re.I)


def clean_text(s, limit=None):
    s = html.unescape(TAG_RE.sub(" ", html.unescape(s or "")))
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        d = parsedate_to_datetime(s)
    except Exception:
        d = None
    if d is None:
        try:
            iso = re.sub(r"\.\d+", "", s.replace("Z", "+00:00"))
            d = datetime.fromisoformat(iso)
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def local(tag):
    return tag.split("}", 1)[-1]


def pick_image(item, html_blobs):
    best, best_w = None, -1
    for el in item.iter():
        t = local(el.tag)
        url = el.get("url")
        if not url:
            continue
        typ = (el.get("type") or "").lower()
        medium = (el.get("medium") or "").lower()
        is_img = (typ.startswith("image") or medium == "image" or
                  re.search(r"\.(jpe?g|png|webp|gif)(\?|$)", url, re.I) or
                  (t in ("thumbnail", "content") and not typ and medium not in ("video", "audio")))
        if t in ("content", "thumbnail", "enclosure") and is_img:
            try:
                w = int(el.get("width") or 0)
            except ValueError:
                w = 0
            if w > best_w:
                best, best_w = url, w
    if best:
        return best
    for blob in html_blobs:
        m = IMG_RE.search(html.unescape(blob or ""))
        if m and not m.group(1).startswith("data:"):
            return m.group(1)
    return None


def parse_feed(raw, google=False):
    root = ET.fromstring(raw.strip())
    out = []
    for it in root.iter():
        if local(it.tag) not in ("item", "entry"):
            continue
        title = link = desc = content = None
        date = None
        source_url = None
        for ch in it:
            t = local(ch.tag)
            txt = (ch.text or "").strip()
            if t == "title":
                title = txt
            elif t == "link":
                href = ch.get("href")
                if href:
                    if ch.get("rel") in (None, "alternate") and not link:
                        link = href
                elif txt:
                    link = txt
            elif t in ("description", "summary"):
                desc = txt
            elif t in ("encoded", "content") and not ch.get("url"):
                content = txt
            elif t in ("pubDate", "published", "updated", "date") and not date:
                date = parse_date(txt)
            elif t == "source":
                source_url = ch.get("url")
        if not title or not link:
            continue
        title = clean_text(title)
        if desc and "appeared first on" in desc:
            desc = None  # WordPress boilerplate ("The post X appeared first on Y.")
        if google:
            title = re.sub(r"\s+-\s+[^-]+$", "", title)  # strip " - Reuters"
            desc = ""
        out.append({
            "title": title,
            "link": link.strip(),
            "desc": clean_text(desc or content, 280),
            "date": date.isoformat() if date else None,
            "image": None if google else pick_image(it, [content, desc]),
            "source_url": source_url,
        })
    return out


# ------------------------------------------------------------------ text tools

STOP = set("""a about above across after again against all almost also am among an and any are aren't around as at be because been
before being below between both but by can can't could did didn't do does doesn't doing don't down during each either else even ever
every few for from further get gets getting got had has hasn't have haven't having he her here hers him his how however i if in inside
into is isn't it it's its itself just last least less let like made make makes many may me might more most much must my near need needs
new news next no nor not now of off on once one only onto or other others our out over own per perhaps rather really said same say says
see seen she should since so some still such take takes than that that's the their them then there these they thing things this those
though through to too toward two under until up upon us use used very via want wants was wasn't way ways we well were what what's when
where whether which while who whom whose why will with within without won't would yet you your year years week weeks day days today
time times first after amid back big top best report reports live latest update updates according people world help know look
going goes come comes came here's isn't opinion analysis video photos watch podcast listen review newsletter could should might
three four five six seven ten more most part story stories ahead exclusive record records warn warns warning
here's could get set amid key behind""".split())

WORD_RE = re.compile(r"[a-z0-9][a-z0-9'’.&-]*[a-z0-9]|[a-z0-9]")


def stem(w):
    w = w.replace("’", "'")
    if w.endswith("'s"):
        w = w[:-2]
    w = w.strip("'.-&")
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def tokens(text):
    out = []
    for w in WORD_RE.findall((text or "").lower()):
        s = stem(w)
        if len(s) < 2 or s in STOP or s.isdigit():
            continue
        out.append(s)
    return out


def surface_forms(text):
    """Map stem -> original casing, preferring Capitalized forms (names)."""
    forms = {}
    for w in re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.&-]*[A-Za-z0-9]|[A-Za-z0-9]", text or ""):
        s = stem(w.lower())
        clean = re.sub(r"['’]s$", "", w).strip("'.-&")
        if s not in forms or (clean[:1].isupper() and not forms[s][:1].isupper()):
            forms[s] = clean
    return forms


def bigrams(text):
    toks = [stem(w) for w in WORD_RE.findall((text or "").lower())]
    out = []
    for a, b in zip(toks, toks[1:]):
        if a in STOP or b in STOP or a.isdigit() or b.isdigit() or len(a) < 2 or len(b) < 2:
            continue
        out.append(a + " " + b)
    return out


def phrase_in(text_lc, phrase):
    return re.search(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])", text_lc) is not None


# ------------------------------------------------------------------- fetching

og_cache = load_json(OG_CACHE_FILE, {})
og_lock = threading.Lock()


def og_image(url):
    with og_lock:
        if url in og_cache:
            return og_cache[url]
    img = None
    if "news.google.com" not in url:
        try:
            raw, _ = http_get(url, timeout=8, maxbytes=600_000)
            s = raw.decode("utf-8", "ignore")
            for m in OG_RE.finditer(s):
                c = CONTENT_ATTR_RE.search(m.group(0))
                if c:
                    img = html.unescape(c.group(1))
                    break
        except Exception:
            img = None
    with og_lock:
        og_cache[url] = img
    return img


def is_stale(items, days=7):
    dates = [parse_date(i["date"]) for i in items if i["date"]]
    return bool(dates) and max(dates) < datetime.now(timezone.utc) - timedelta(days=days)


def fetch_source(src):
    """A publication's feed; falls back to Google News if the feed is missing, broken or stale."""
    google = src["feed"] is None
    items, err = [], None
    if not google:
        try:
            raw, _ = http_get(src["feed"])
            items = parse_feed(raw)
            if not items or is_stale(items):
                log("feed stale or empty, using Google News:", src["id"])
                google = True
        except Exception as e:
            log("feed failed, using Google News:", src["id"], e)
            google = True
    if google:
        try:
            raw, _ = http_get(google_news_url("site:%s when:1d" % src["domain"]))
            items = parse_feed(raw, google=True)
        except Exception as e:
            log("feed failed", src["id"], e)
            return src["id"], [], str(e)
        items = [i for i in items if not i["source_url"] or src["domain"].split(".")[-2] in i["source_url"]]
    for i in items:
        i["pub"] = src["id"]
    return src["id"], items[:40], None


def ensure_logo(src):
    path = os.path.join(LOGOS, src["id"] + ".png")
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return
    candidates = [
        "https://%s/apple-touch-icon.png" % ("www." + src["domain"] if src["domain"].count(".") == 1 else src["domain"]),
        "https://www.google.com/s2/favicons?domain=%s&sz=128" % src.get("icon_domain", src["domain"]),
        "https://icons.duckduckgo.com/ip3/%s.ico" % src["domain"],
    ]
    for u in candidates:
        try:
            raw, ctype = http_get(u, timeout=8, maxbytes=500_000)
            if ctype.startswith("image") and len(raw) > 150:
                with open(path, "wb") as f:
                    f.write(raw)
                return
        except Exception:
            continue


# ------------------------------------------------------------------ analysis

def build_docs(items):
    docs = []
    for it in items:
        tv = Counter()
        for t in tokens(it["title"]):
            tv[t] += 2
        for t in tokens(it["desc"])[:40]:
            tv[t] += 1
        if tv:
            docs.append({"item": it, "tf": tv,
                         "forms": surface_forms(it["title"] + " " + it["desc"])})
    n = len(docs)
    df = Counter()
    for d in docs:
        df.update(d["tf"].keys())
    idf = {t: math.log((n + 1) / (c + 0.5)) for t, c in df.items()}
    for d in docs:
        v = {t: (1 + math.log(c)) * idf[t] for t, c in d["tf"].items() if df[t] > 1 and df[t] < n * 0.15}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        d["vec"] = {t: x / norm for t, x in v.items()}
    return docs, idf


def cosine(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b[t] for t, x in a.items() if t in b)


def cluster(docs, idxs, sims, threshold):
    parent = {i: i for i in idxs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    idset = set(idxs)
    for (i, j), s in sims.items():
        if s >= threshold and i in idset and j in idset:
            parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in idxs:
        groups[find(i)].append(i)
    out = []
    for g in groups.values():
        if len(g) > 14 and threshold < 0.7:
            out.extend(cluster(docs, g, sims, threshold + 0.06))
        else:
            out.append(g)
    return out


def prune(docs, g, floor=0.28):
    """Drop members that only joined via a chain — each must resemble the rest of its cluster."""
    g = list(g)
    while len(g) > 2:
        total = Counter()
        for i in g:
            total.update(docs[i]["vec"])
        keep = []
        for i in g:
            rest = {t: v - docs[i]["vec"].get(t, 0) for t, v in total.items()}
            norm = math.sqrt(sum(v * v for v in rest.values() if v > 0)) or 1
            if cosine(docs[i]["vec"], {t: v for t, v in rest.items() if v > 0}) / norm >= floor:
                keep.append(i)
        if len(keep) == len(g):
            break
        g = keep
    return g


def merge_related(docs, groups, threshold=0.4):
    """Join clusters that are two angles on one story (e.g. a deal and the fighting it was meant to stop)."""
    def centroid(g):
        c = Counter()
        for i in g:
            c.update(docs[i]["vec"])
        norm = math.sqrt(sum(v * v for v in c.values())) or 1
        return {t: v / norm for t, v in c.items()}

    groups = [g for g in groups if g]
    merged = True
    while merged:
        merged = False
        big = [i for i, g in enumerate(groups) if len(g) >= 3]
        cents = {i: centroid(groups[i]) for i in big}
        best = None
        for a in big:
            for b in big:
                if a < b:
                    sim = cosine(cents[a], cents[b])
                    if sim >= threshold and (best is None or sim > best[0]):
                        best = (sim, a, b)
        if best:
            _, a, b = best
            groups[a] = groups[a] + groups[b]
            groups.pop(b)
            merged = True
    return groups


def trending_stories(docs):
    n = len(docs)
    sims = {}
    for i in range(n):
        vi = docs[i]["vec"]
        pi = docs[i]["item"]["pub"]
        for j in range(i + 1, n):
            if docs[j]["item"]["pub"] == pi:
                continue
            vj = docs[j]["vec"]
            if len(vi.keys() & vj.keys()) < 2:
                continue  # one shared word ("record", "ahead") isn't a shared story
            s = cosine(vi, vj)
            if s >= 0.24:
                sims[(i, j)] = s
    groups = merge_related(docs, [prune(docs, g) for g in cluster(docs, list(range(n)), sims, 0.26)])
    stories = []
    for g in groups:
        pubs = {docs[i]["item"]["pub"] for i in g}
        if len(pubs) < 3:
            continue
        centroid = Counter()
        for i in g:
            centroid.update(docs[i]["vec"])

        def centrality(i):
            return cosine(docs[i]["vec"], centroid)

        forms = {}
        for i in g:
            for k, v in docs[i]["forms"].items():
                if k not in forms or (v[:1].isupper() and not forms[k][:1].isupper()):
                    forms[k] = v
        doc_freq = Counter()
        for i in g:
            doc_freq.update(set(docs[i]["vec"]))
        key_terms = [t for t, _ in sorted(centroid.items(), key=lambda kv: -kv[1] * doc_freq[kv[0]])
                     if doc_freq[t] >= max(2, len(g) * 0.3)][:4]
        best_per_pub = {}
        for i in sorted(g, key=centrality, reverse=True):
            p = docs[i]["item"]["pub"]
            best_per_pub.setdefault(p, i)
        lead = max(g, key=centrality)
        angles = []
        for p, i in best_per_pub.items():
            it = docs[i]["item"]
            angles.append({"pub": p, "title": it["title"], "link": it["link"], "desc": it["desc"],
                           "date": it["date"], "tone": tone_of(it["title"] + " " + it["desc"])})
        angles.sort(key=lambda a: SOURCES.index(SRC[a["pub"]]))
        image = next((docs[i]["item"].get("image") for i in sorted(g, key=centrality, reverse=True)
                      if docs[i]["item"].get("image")), None)
        stories.append({
            "headline": docs[lead]["item"]["title"],
            "summary": docs[lead]["item"]["desc"],
            "terms": [forms.get(t, t) for t in key_terms],
            "pub_count": len(pubs),
            "article_count": len(g),
            "angles": angles,
            "image": image,
            "score": len(pubs) * 3 + len(g),
        })
    stories.sort(key=lambda s: -s["score"])
    return stories[:12]


def tone_of(text):
    toks = [stem(w) for w in WORD_RE.findall(text.lower())]
    raw = WORD_RE.findall(text.lower())
    neg = sum(1 for w in raw if w in NEGATIVE) + sum(1 for w in toks if w in NEGATIVE and w not in raw)
    pos = sum(1 for w in raw if w in POSITIVE)
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return "neutral"


def theme_moods(items):
    out = []
    for theme, words in THEMES.items():
        hits = []
        for it in items:
            text = " " + (it["title"] + " " + it["desc"]).lower() + " "
            if any(phrase_in(text, w) for w in words):
                hits.append(it)
        pubs = {h["pub"] for h in hits}
        if len(pubs) < 3:
            continue
        tones = Counter()
        per_pub = {}
        for h in hits:
            t = tone_of(h["title"] + " " + h["desc"])
            tones[t] += 1
            per_pub.setdefault(h["pub"], dict(h, tone=t))
        total = sum(tones.values())
        lean = (tones["positive"] - tones["negative"]) / total
        label = ("mostly negative" if lean <= -0.25 else "leaning negative" if lean < -0.08 else
                 "mostly positive" if lean >= 0.25 else "leaning positive" if lean > 0.08 else "mixed")
        examples = sorted(per_pub.values(), key=lambda h: (h["tone"] == "neutral", SOURCES.index(SRC[h["pub"]])))
        out.append({
            "theme": theme, "pub_count": len(pubs), "article_count": total,
            "tones": {k: tones[k] for k in ("negative", "neutral", "positive")},
            "lean": round(lean, 2), "label": label,
            "examples": [{"pub": h["pub"], "title": h["title"], "link": h["link"], "tone": h["tone"]}
                         for h in examples[:8]],
        })
    out.sort(key=lambda m: -m["pub_count"])
    return out


# --------------------------------------------------------------- history store

hist_lock = threading.Lock()


def history_path(day):
    return os.path.join(HIST, day + ".json")


def proper_nouns(title, desc):
    """Stems that are capitalised mid-sentence (names, places, acronyms).

    Title-case headlines capitalise every word, so titles only count when they
    are written in sentence case."""
    out = set()
    words_t = title.split()
    blobs = [desc]
    if words_t and sum(w[:1].isupper() for w in words_t) / len(words_t) < 0.5:
        blobs.append(title)
    for blob in blobs:
        for sentence in re.split(r"(?<=[.!?:;])\s+|\s[—–-]\s", blob or ""):
            for w in sentence.split()[1:]:
                w = w.strip("\"'“”‘’(),.!?:;")
                if len(w) > 1 and (w[:1].isupper() and w[1:2].islower() or w.isupper()):
                    s = stem(w.lower())
                    if s not in STOP:
                        out.add(s)
    return sorted(out)


def record_history(items):
    now = datetime.now(timezone.utc)
    by_day = defaultdict(dict)
    for it in items:
        d = parse_date(it["date"]) if it["date"] else now
        if d > now + timedelta(hours=2) or d < now - timedelta(days=HISTORY_DAYS):
            continue
        day = d.astimezone().strftime("%Y-%m-%d")
        text = it["title"] + " " + it["desc"]
        by_day[day][it["link"]] = {
            "pub": it["pub"], "title": it["title"], "link": it["link"],
            "terms": sorted(set(tokens(it["title"] + " " + it["desc"][:200]))),
            "bigrams": sorted(set(bigrams(it["title"]) + bigrams(it["desc"][:200]))),
            "forms": {k: v for k, v in surface_forms(text).items() if v[:1].isupper()},
            "proper": proper_nouns(it["title"], it["desc"]),
        }
    with hist_lock:
        for day, entries in by_day.items():
            existing = load_json(history_path(day), {})
            existing.update(entries)
            save_json(history_path(day), existing)
        cutoff = (now - timedelta(days=HISTORY_DAYS)).strftime("%Y-%m-%d")
        for f in os.listdir(HIST):
            if f.endswith(".json") and f[:-5] < cutoff:
                os.remove(os.path.join(HIST, f))


GENERIC = set("""state united company security tech u.s america american government president house white senate congress
city country war market markets business health science group report police court officials official national federal
north south east west new york london europe european china chinese trump donald republican republicans democrat democrats
people life work home family school family data money global international news media social policy party film show
united state white house supreme court prime minister forces force games game team teams players season league
leaders leader workers children women men students officials minister ministers army military troops police campaign election
company companies market stocks shares investors economy officials agency department court judge city state states""".split()) | {"white house", "united state", "prime minister",
                                                         "supreme court", "new york", "donald trump", "wall street"}


def rising_topics(window=28, recent=7):
    today = datetime.now().date()
    days = [(today - timedelta(days=k)).strftime("%Y-%m-%d") for k in range(window - 1, -1, -1)]
    with hist_lock:
        loaded = {d: load_json(history_path(d), {}) for d in days}
    days_with_data = [d for d in days if len(loaded[d]) >= 20]
    all_articles = [a for d in days for a in loaded[d].values()]
    total = len(all_articles)
    if total < 200:
        return {"days_collected": len(days_with_data), "topics": [], "leaders": []}
    term_days = defaultdict(lambda: [0] * window)
    term_pubs = defaultdict(set)
    term_articles = defaultdict(list)
    forms = {}
    proper = Counter()
    for d in days:
        for a in loaded[d].values():
            proper.update(a.get("proper", []))
    for di, d in enumerate(days):
        for a in loaded[d].values():
            # single words only count when they're names; otherwise use two-word phrases
            uni = {t for t in a["terms"] if proper[t] >= 2}
            for t in set(a["bigrams"]) | uni:
                term_days[t][di] += 1
                term_pubs[t].add(a["pub"])
                term_articles[t].append((di, a))
            for k, v in a.get("forms", {}).items():
                forms.setdefault(k, v)
    day_totals = [len(loaded[d]) for d in days]
    first_day = next((i for i, d in enumerate(days) if len(loaded[d]) >= 20), 0)
    span = window - first_day
    recent_n = min(recent, max(1, span // 3))
    results = []
    for t, series in term_days.items():
        n = sum(series)
        pubs = term_pubs[t]
        if n < 6 or len(pubs) < 4 or n > total * 0.04:
            continue
        active_days = sum(1 for x in series if x)
        if active_days < 3:
            continue
        if t in GENERIC:
            continue
        # share of each day's articles, so days with more stored history don't look "rising"
        r_tot = sum(day_totals[-recent_n:]) or 1
        e_tot = sum(day_totals[first_day:window - recent_n]) or 1
        r = sum(series[-recent_n:]) / r_tot
        e = sum(series[first_day:window - recent_n]) / e_tot
        growth = (r + 0.002) / (e + 0.002)
        score = math.log(n) * len(pubs) ** 0.5 * min(growth, 6) * (1.6 if " " in t else 1.0)
        results.append((score, t, series, pubs, growth, n))
    results.sort(reverse=True)
    chosen = []
    for score, t, series, pubs, growth, n in results:
        parts = t.split(" ")
        if any(t in c["key"].split(" ") or (len(parts) > 1 and c["key"] in parts) for c in chosen):
            continue
        if growth < 1.3:
            continue
        label = " ".join(forms.get(p, p) for p in parts)
        arts = sorted(term_articles[t], key=lambda x: -x[0])
        seen_pubs, examples = set(), []
        for di, a in arts:
            if a["pub"] in seen_pubs:
                continue
            seen_pubs.add(a["pub"])
            examples.append({"pub": a["pub"], "title": a["title"], "link": a["link"], "day": days[di]})
            if len(examples) == 5:
                break
        chosen.append({"key": t, "label": label, "series": series[first_day:], "days": days[first_day:],
                       "article_count": n, "pubs": sorted(pubs, key=lambda p: SOURCES.index(SRC[p])),
                       "growth": round(growth, 1), "examples": examples})
        if len(chosen) == 8:
            break
    # growth needs a week of history; "most widely covered this month" is always shown
    if len(days_with_data) < 7:
        chosen = []
    leaders = []
    if True:
        last7 = 0  # whole window (~4 weeks)
        ranked = []
        for t, series in term_days.items():
            if t in GENERIC:
                continue
            pubs = {a["pub"] for di, a in term_articles[t] if di >= last7}
            n = sum(series[last7:])
            if len(pubs) >= 5 and n <= total * 0.05:
                ranked.append((len(pubs) * (1.3 if " " in t else 1), n, t, pubs))
        ranked.sort(reverse=True)
        for _, n, t, pubs in ranked:
            parts = t.split(" ")
            if any(t in c["key"].split(" ") or (len(parts) > 1 and c["key"] in parts)
                   or t.startswith(c["key"]) or c["key"].startswith(t) for c in leaders):
                continue
            arts = sorted((x for x in term_articles[t] if x[0] >= last7), key=lambda x: -x[0])
            seen, ex = set(), []
            for di, a in arts:
                if a["pub"] not in seen:
                    seen.add(a["pub"])
                    ex.append({"pub": a["pub"], "title": a["title"], "link": a["link"], "day": days[di]})
            leaders.append({"key": t, "label": " ".join(forms.get(p, p) for p in parts), "article_count": n,
                            "pubs": sorted(pubs, key=lambda p: SOURCES.index(SRC[p])), "examples": ex[:3]})
            if len(leaders) == 6:
                break
    return {"days_collected": len(days_with_data), "topics": chosen, "leaders": leaders}


# ------------------------------------------------------------ tracked topics

topics_lock = threading.Lock()
topic_cache = {}  # name -> (fetched_at, result)


def load_topics():
    topics = load_json(TOPICS_FILE, None)
    if topics is None:
        topics = DEFAULT_TOPICS
        save_json(TOPICS_FILE, topics)
    return topics


def fetch_topic(topic):
    """Coverage of a topic week by week for 4 weeks, via Google News.

    Google News returns its 100 most relevant results per query (site: filters
    make matching sloppy), so each week is one query across all outlets, and
    the dashboard counts the ones from our publications. web_weekly is the
    all-outlet count; a week that hits 100 is flagged as capped."""
    today = datetime.now().date()
    items = {}
    capped = [False] * 4
    web_counts = [0] * 4

    def week(w):
        after = today - timedelta(days=7 * (w + 1) - 1)
        before = today - timedelta(days=7 * w - 1)
        q = "%s after:%s before:%s" % (topic["query"], after.isoformat(), before.isoformat())
        try:
            raw, _ = http_get(google_news_url(q))
            return w, parse_feed(raw, google=True)
        except Exception as e:
            log("topic fetch failed", topic["name"], e)
            return w, []

    with ThreadPoolExecutor(4) as ex:
        for w, got in ex.map(week, range(4)):
            web_counts[3 - w] = len(got)
            capped[3 - w] = len(got) >= 100
            for it in got:
                items[it["link"]] = it
    weekly = [0, 0, 0, 0]  # oldest -> most recent 7 days
    pubs = set()
    arts = []
    for it in items.values():
        su = (it.get("source_url") or "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        pid = DOMAIN_TO_ID.get(su) or next((v for k, v in DOMAIN_TO_ID.items() if su.endswith(k) or k.endswith(su)), None)
        if not pid or not it["date"]:
            continue
        d = parse_date(it["date"]).astimezone().date()
        age = (today - d).days
        if age < 0 or age >= 28:
            continue
        weekly[3 - age // 7] += 1
        pubs.add(pid)
        it["pub"] = pid
        arts.append(it)
    arts.sort(key=lambda i: i["date"], reverse=True)
    seen, examples = set(), []
    for a in arts:
        if a["pub"] in seen:
            continue
        seen.add(a["pub"])
        examples.append({"pub": a["pub"], "title": a["title"], "link": a["link"], "date": a["date"]})
        if len(examples) == 6:
            break
    prior = sum(weekly[:3]) / 3
    return {"name": topic["name"], "query": topic["query"], "weekly": weekly, "capped": capped,
            "web_weekly": web_counts,
            "article_count": len(arts), "last7": weekly[3], "prior7_avg": round(prior, 1),
            "pubs": sorted(pubs, key=lambda p: SOURCES.index(SRC[p])), "examples": examples}


def tracked_topics(force=False):
    topics = load_topics()
    out = []
    now = time.time()
    todo = [t for t in topics if force or t["name"] not in topic_cache
            or now - topic_cache[t["name"]][0] > TOPIC_REFRESH_SECONDS
            or topic_cache[t["name"]][1]["query"] != t["query"]]
    with ThreadPoolExecutor(4) as ex:
        for t, res in zip(todo, ex.map(fetch_topic, todo)):
            topic_cache[t["name"]] = (now, res)
    for t in topics:
        if t["name"] in topic_cache:
            out.append(topic_cache[t["name"]][1])
    return out


# ------------------------------------------------------------------- markets

market_cache = {"at": 0, "data": []}


def markets():
    """Index/watchlist quotes in one batched Yahoo "spark" call; cached for a minute."""
    if time.time() - market_cache["at"] < 60 and market_cache["data"]:
        return market_cache["data"]
    meta_by = {sym: (name, group) for sym, name, group in MARKETS}
    url = ("https://query1.finance.yahoo.com/v7/finance/spark?range=1d&interval=5m&symbols="
           + ",".join(urllib.parse.quote(s, safe="") for s, _, _ in MARKETS))
    try:
        raw, _ = http_get(url, timeout=10, ua="Mozilla/5.0")  # Yahoo throttles full browser UAs
        by_sym = {}
        for r in json.loads(raw)["spark"]["result"]:
            resp = (r.get("response") or [{}])[0]
            meta = resp.get("meta", {})
            price = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            closes = [c for c in (resp.get("indicators", {}).get("quote", [{}])[0].get("close") or []) if c is not None]
            change = price - prev if price is not None and prev else None
            name, group = meta_by.get(r["symbol"], (r["symbol"], "other"))
            by_sym[r["symbol"]] = {"symbol": r["symbol"], "name": name, "group": group,
                                   "price": price, "change": change,
                                   "pct": (change / prev * 100) if change is not None else None,
                                   "spark": closes[::2][-80:], "prev": prev}
        data = [by_sym[s] for s, _, _ in MARKETS if s in by_sym]
        if data:
            market_cache.update(at=time.time(), data=data)
    except Exception as e:
        log("markets failed", e)
    return market_cache["data"]


movers_cache = {"at": 0, "data": None}
NAME_SUFFIX = re.compile(r"[,.]?\s+(inc|corp|corporation|company|co|holdings?|group|plc|ltd|limited|n\.?v|s\.?a|ag|se|technologies|"
                         r"technology|systems|platforms|incorporated|class [a-c]|sponsored|adr|the)\b.*$", re.I)


def company_key(name):
    name = re.sub(r"^The\s+", "", (name or "").strip())
    key = NAME_SUFFIX.sub("", name).strip(" ,.")
    return key if len(key) >= 3 else None


def headline_for(quote, items):
    """A headline from our publications that mentions this company, if any."""
    key = company_key(quote.get("shortName") or quote.get("longName"))
    pats = [re.compile(r"\(%s\)" % re.escape(quote["symbol"]))]
    if key:
        pats.append(re.compile(r"(?<![A-Za-z])%s(?![a-z])" % re.escape(key)))
    for it in items:
        if any(p.search(it["title"]) for p in pats):
            return {"pub": it["pub"], "title": it["title"], "link": it["link"], "date": it["date"]}
    return None


def movers():
    """Large-cap gainers/losers and most-traded stocks (Yahoo screeners), each with a matching headline."""
    if time.time() - movers_cache["at"] < 300 and movers_cache["data"]:
        return movers_cache["data"]
    out = {}
    state_label = None
    with state_lock:
        items = list(state.get("finance_items") or [])
    for scr in ("day_gainers", "day_losers", "most_actives"):
        url = ("https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=60&scrIds=" + scr)
        try:
            raw, _ = http_get(url, timeout=10, ua="Mozilla/5.0")
            quotes = json.loads(raw)["finance"]["result"][0]["quotes"]
        except Exception as e:
            log("movers failed", scr, e)
            continue
        big = [q for q in quotes if (q.get("marketCap") or 0) >= 10e9 and q.get("quoteType", "EQUITY") == "EQUITY"]
        rows = []
        for q in big[:6]:
            state_label = state_label or q.get("marketState")
            rows.append({"symbol": q["symbol"], "name": q.get("displayName") or company_key(q.get("shortName")) or q.get("shortName") or q["symbol"],
                         "price": q.get("regularMarketPrice"), "pct": q.get("regularMarketChangePercent"),
                         "cap": q.get("marketCap"), "news": headline_for(q, items)})
        out[scr] = rows
    out["market_state"] = state_label
    if any(out.get(k) for k in ("day_gainers", "day_losers", "most_actives")):
        movers_cache.update(at=time.time(), data=out)
    return movers_cache["data"] or out


def finance_news(by_pub, corpus):
    """Market & economy headlines: everything from finance publications plus market-themed stories elsewhere."""
    words = THEMES["Stock market"] + THEMES["Economy"] + THEMES["Trade & tariffs"] + THEMES["Crypto"]
    pool = []
    for it in corpus:
        text = " " + (it["title"] + " " + it["desc"]).lower() + " "
        is_market = any(phrase_in(text, w) for w in words)
        if it["pub"] in FINANCE_PUBS or is_market:
            pool.append(dict(it, tone=tone_of(it["title"] + " " + it["desc"]), market=is_market))
    pool.sort(key=lambda i: (not i["market"], -(parse_date(i["date"]).timestamp() if i["date"] else 0)))
    seen, out, per_pub = [], [], Counter()
    for it in pool:
        if per_pub[it["pub"]] >= 3:
            continue
        toks = set(tokens(it["title"]))
        if any(len(toks & s) >= max(3, len(toks) * 0.5) for s in seen):
            continue
        seen.append(toks)
        per_pub[it["pub"]] += 1
        out.append({k: it[k] for k in ("pub", "title", "link", "desc", "date", "image", "tone")})
        if len(out) == 12:
            break
    return out


# ------------------------------------------------------------------ refresh

state = {"generated": None, "payload": None, "refreshing": False, "error": None}
state_lock = threading.Lock()


def source_info(s):
    """What the page needs to know about a publication, including where its icons live (relative URLs)."""
    has_icon = os.path.exists(os.path.join(STATIC, "icons", s["id"] + ".svg"))
    return dict({k: s[k] for k in ("id", "name", "domain", "section", "mark", "color")},
                wordmark=os.path.exists(os.path.join(STATIC, "logos", s["id"] + ".svg")),
                icon=("icons/%s.svg" if has_icon else "logo/%s.png") % s["id"])


def refresh():
    with state_lock:
        if state["refreshing"]:
            return
        state["refreshing"] = True
    t0 = time.time()
    try:
        with ThreadPoolExecutor(12) as ex:
            results = list(ex.map(fetch_source, SOURCES))
            list(ex.map(ensure_logo, SOURCES))
        by_pub = {pid: items for pid, items, _ in results}
        errors = {pid: err for pid, _, err in results if err}

        # top two per publication: prefer items from the last 48h, in feed order
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        tops = {}
        for pid, items in by_pub.items():
            fresh = [i for i in items if not i["date"] or parse_date(i["date"]) >= cutoff]
            tops[pid] = (fresh or items)[:2]
        need_img = [i for pair in tops.values() for i in pair if not i.get("image")]
        with ThreadPoolExecutor(12) as ex:
            for it, img in zip(need_img, ex.map(lambda i: og_image(i["link"]), need_img)):
                it["image"] = img
        with og_lock:
            if len(og_cache) > 3000:
                for k in list(og_cache)[:1000]:
                    og_cache.pop(k)
            save_json(OG_CACHE_FILE, og_cache)

        # analysis corpus: up to 25 items per pub from the last 36h
        recent_cut = datetime.now(timezone.utc) - timedelta(hours=36)
        corpus = []
        for pid, items in by_pub.items():
            fresh = [i for i in items if i["date"] and parse_date(i["date"]) >= recent_cut]
            if not fresh:
                fresh = items[:10]
            corpus.extend(fresh[:25])
        docs, _ = build_docs(corpus)
        stories = trending_stories(docs)
        moods = theme_moods(corpus)
        fin = finance_news(by_pub, corpus)
        with state_lock:
            state["finance_items"] = [i for items in by_pub.values() for i in items]
        movers_cache["at"] = 0
        record_history([i for items in by_pub.values() for i in items])
        rising = rising_topics()
        topics = tracked_topics()

        payload = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "title": SITE_TITLE,
            "sections": SECTIONS,
            "sources": [source_info(s) for s in SOURCES],
            "headlines": tops,
            "errors": errors,
            "trending": stories,
            "moods": moods,
            "finance": fin,
            "rising": rising,
            "topics": topics,
        }
        with state_lock:
            state.update(generated=payload["generated"], payload=payload, error=None)
        log("refreshed in %.1fs — %d stories, %d moods, %d articles analysed"
            % (time.time() - t0, len(stories), len(moods), len(corpus)))
    except Exception as e:
        import traceback
        traceback.print_exc()
        with state_lock:
            state["error"] = str(e)
    finally:
        with state_lock:
            state["refreshing"] = False


def refresher():
    while True:
        refresh()
        time.sleep(REFRESH_SECONDS)


# -------------------------------------------------------------------- server

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=STATIC, **kw)

    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(path.query)
        if path.path == "/api/news":
            if qs.get("refresh"):
                threading.Thread(target=refresh, daemon=True).start()
            with state_lock:
                self.send_json({"refreshing": state["refreshing"], "error": state["error"],
                                "data": state["payload"]})
            return
        if path.path == "/api/markets":
            self.send_json({"quotes": markets(), "movers": movers()})
            return
        m = re.match(r"^/logo/([a-z0-9]+)\.png$", path.path)
        if m:
            f = os.path.join(LOGOS, m.group(1) + ".png")
            if os.path.exists(f):
                with open(f, "rb") as fh:
                    body = fh.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "max-age=86400")
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404)
            return
        return super().do_GET()

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        if path != "/api/topics":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self.send_json({"error": "bad json"}, 400)
            return
        with topics_lock:
            topics = load_topics()
            if body.get("action") == "remove":
                topics = [t for t in topics if t["name"] != body.get("name")]
                topic_cache.pop(body.get("name"), None)
            elif body.get("action") == "add" and body.get("name"):
                name = body["name"].strip()[:80]
                query = (body.get("query") or "").strip()[:300] or '"%s"' % name
                topics = [t for t in topics if t["name"] != name] + [{"name": name, "query": query}]
            save_json(TOPICS_FILE, topics)
        result = tracked_topics()
        with state_lock:
            if state["payload"]:
                state["payload"]["topics"] = result
        self.send_json(result)


def main():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        log("Port %d is in use — Daily Brief is probably already running." % PORT)
        sys.exit(0)
    threading.Thread(target=refresher, daemon=True).start()
    log("Daily Brief running at http://localhost:%d" % PORT)
    server.serve_forever()


if __name__ == "__main__":
    main()
