# Wallflower (formerly Daily Brief): notes for Claude

The running site uses no LLM; tokens are only spent on edits. Keep changes small and targeted, and don't re-read the whole codebase when one file will do.

## Map
- `sources.py`: SITE_TITLE, REPO_URL, SUPPORT_URL (coffee card; empty = hidden), the 24 publications (feed, wordmark style, color), mood THEMES, MARKETS tickers, FINANCE_PUBS.
- `server.py`: everything that fetches and analyzes (stdlib only, Python 3.9-compatible). It runs as the local app (http://localhost:8787) and as a library for `build.py`.
  - feeds: `fetch_source` (stale or missing feed falls back to Google News), `parse_feed`, `og_image`
  - trending: `build_docs` → `trending_stories` (pairs need 2+ shared terms) → `prune` → `merge_related`
  - history: `record_history`; `rising_topics` (needs 7+ days); tracked topics: `load_topics`/`fetch_topic` (Google News, weekly)
  - markets: `markets()` (one batched Yahoo spark call; needs UA "Mozilla/5.0"), `movers()` (Yahoo screeners, $10B+)
- `build.py`: writes the static public site to `site/` (data/news.json, markets.json, archive.json for visitor topics). It versions the CSS/JS links for cache busting.
- `static/texture.jpg`: blurred-flower texture (masthead, empty grid slots, app icon); regenerate with `python3 tools/make_icons.py --texture`, then open http://localhost:8799/tools/texture.html. Icons: `python3 tools/make_icons.py W`, then open /tools/icon.html?letter=W.
- `static/header-poppy.jpg`: header flower (Unsplash, Lorin Both), cyanotype-toned and hung from the top; rebuild with `python3 tools/make_icons.py --header`, then open http://localhost:8799/tools/header.html. Grid gaps show `static/stem.png`, an original AI-generated stem (Figma file "Wallflower – flower stem art") with its backdrop removed by `python3 tools/make_icons.py --stem`. Section flowers (.peek-1/2/3) were placed in that Figma file, page "Flower placement" (390 and 1280 wide frames); convert a flower layer's center back to CSS top/right/left with the gutter.
- `static/`: index.html, app.js (one file, all rendering; `STATIC` = public mode), style.css (tokens at top; dark mode block right below).
- `.github/workflows/publish.yml`: cron 11,41 * * * *, runs build.py, commits data/ history, deploys Pages.

## Data
- `data/` is committed and updated by GitHub every run: history/, og_cache.json, logos/, topics.txt, markets_last.json.
- The local app writes its own history to `.local/` (gitignored), so it never touches `data/`.
- `data/topics.txt`: starter topics, `Name | query`. Visitors' own topics live in their browser (localStorage).

## Gotchas
- The user publishes with GitHub Desktop (Push origin); Claude can't push (no credentials). Before committing, run `git pull --rebase origin main`, because the bot commits every run.
- style.css has one-line dark-mode overrides with the same selectors as the base rules (`.art`, `.masthead::before`). Edit the multi-line base rule by exact match, never with "first occurrence" regex. Check that braces are balanced afterwards.
- After a change to server.py, restart the local server: `pkill -f "Python server.py"; (nohup python3 server.py > .local/server.log 2>&1 &)`.
- To test the public build: `python3 build.py && python3 -m http.server 8798 --directory site`.
- Write in US English; the user wants terse replies (watchouts and questions only).
