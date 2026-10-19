# The Daily Brief

**Make your own** (free, about 10 minutes, no coding needed)

1. **Copy this project.** Sign in to GitHub, click the green **Use this template** button at the top of this page, then **Create a new repository**. Name it `daily-brief` and set it to **Public**.
2. **Turn on the website.** In your new repository, go to **Settings → Pages**. Under "Source", choose **GitHub Actions**.
3. **Make it yours.** Click a file, then the pencil icon to edit it, then **Commit changes**:
   - `sources.py`: change `SITE_TITLE` to your own name, e.g. `"Sam’s Daily Brief"`. You can also add or remove publications in the `SOURCES` list, or change the stock ticker in `MARKETS`.
   - `data/topics.txt` (optional): the starter topics everyone sees in "Over the weeks", one per line, like `Ozempic | wegovy OR "GLP-1"`.
4. **Publish.** Saving a file starts a build automatically. Watch it in the **Actions** tab (about 2 minutes). Your site will be at `https://YOUR-USERNAME.github.io/daily-brief/`. From then on, it refreshes itself every 30 minutes; nothing needs to stay running on your computer.

Optional: to start your trend history from scratch, delete the files in `data/history/`.

### Tracking topics
Anyone can track a topic right on the page. In "Over the weeks", type a topic (and, optionally, other words to look for) and click **Track**. It's saved in that person's browser, so everyone keeps their own list.

---

A news dashboard in four sections:
1. **Trending today**: stories that 3+ publications are covering, with each outlet's headline.
2. **Front pages**: the top two headlines from each of the 24 publications.
3. **Markets & money**: a plain-English market verdict, index charts, hot stocks and market headlines.
4. **Over the weeks**: tracked topics, plus stories rising across your feeds.

## Open it
- Double-click **Daily Brief.app** (drag it to your Dock). It starts the server if needed and opens http://localhost:8787.
- Or run `python3 server.py` and open http://localhost:8787.

The server refreshes feeds every 20 minutes while it runs. The page checks for new data every 5 minutes, and markets update every minute.

## How it works
- `sources.py`: site name, publications, feeds, ticker symbols. Edit this to add or remove sources.
- `server.py`: fetches the feeds (standard-library Python only), clusters headlines into shared stories, scores the tone of each theme, saves every headline to `data/history/`, and serves the page.
- **Trending**: headlines are matched by word overlap. A story appears once 3+ publications cover it.
- **Rising in your feeds**: compares each name or phrase's share of headlines over the last week with the weeks before. It needs about 7 days of saved history, so keep the server running daily.
- **Tracked topics**: weekly counts from Google News, filtered to your 24 publications. Add or remove topics on the page.

Publication wordmarks are SVGs from Wikimedia Commons in `static/logos/`. Small icons are site favicons, with hand-made overrides in `static/icons/`. A feed that goes stale for more than a week switches to Google News automatically.

Data stays in `data/`. Delete `data/history` to reset trend history.

## Public site (GitHub Pages)
`.github/workflows/publish.yml` runs `build.py` every 30 minutes on GitHub. That fetches everything, writes a read-only copy of the page to `site/`, and publishes it to GitHub Pages. It also commits the headline history back to the repo so trends keep building.

On the public site, visitors' own topics are saved in their browser and matched against the last 4 weeks of saved headlines (`data/archive.json`). The starter topics in `data/topics.txt` are searched more widely through Google News. To refresh right away, open the repo's **Actions** tab, choose **Publish Daily Brief**, then **Run workflow**.
