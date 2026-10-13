# The Daily Brief

A local news dashboard in five sections:
1. **Trending today**: stories that 3+ publications are covering, with each outlet's headline.
2. **Markets & money**: a plain-English market verdict, index charts, hot stocks (large-cap gainers, decliners and most traded, with a related headline) and market headlines.
3. **The mood**: whether coverage of recurring themes leans negative or positive.
4. **Over the weeks**: tracked topics plus automatically detected rising stories.
5. **Front pages**: the top two headlines from each of the 24 publications.

## Open it
- Double-click **Daily Brief.app** (drag it to your Dock). It starts the server if needed and opens http://localhost:8787.
- Or run `python3 server.py` and open http://localhost:8787.

The server refreshes feeds every 20 minutes while it runs. The page checks for new data every 5 minutes, and markets update every minute.

## How it works
- `sources.py`: publications, feeds, mood themes, default tracked topics, ticker symbols. Edit this to add or remove sources.
- `server.py`: fetches the feeds (standard-library Python only), clusters headlines into shared stories, scores the tone of each theme, saves every headline to `data/history/`, and serves the page.
- **Trending**: headlines are matched by word overlap. A story appears once 3+ publications cover it.
- **Rising in your feeds**: compares each name or phrase's share of headlines over the last week with the weeks before. It needs about 7 days of saved history, so keep the server running daily.
- **Tracked topics**: weekly counts from Google News, filtered to your 24 publications. Add or remove topics on the page.

Publication wordmarks are SVGs from Wikimedia Commons in `static/logos/`. Small icons are site favicons, with hand-made overrides in `static/icons/`. A feed that goes stale for more than a week switches to Google News automatically.

Data stays in `data/`. Delete `data/history` to reset trend history.

## Public site (GitHub Pages)
`.github/workflows/publish.yml` runs `build.py` every 30 minutes on GitHub. That fetches everything, writes a read-only copy of the page to `site/`, and publishes it to GitHub Pages. It also commits the headline history back to the repo so trends keep building.

On the public site, tracked topics are read-only. To change them, edit `data/topics.json` (or add them in the local app) and push. To refresh right away, open the repo's **Actions** tab, choose **Publish Daily Brief**, then **Run workflow**.
