"""The publications on the dashboard, grouped by section.

feed:  an RSS/Atom URL, or None to use Google News (site: search) for outlets
       that no longer publish public RSS feeds.
mark:  wordmark style used next to the logo — serif | italic | black | sans | mono
color: brand accent for the block's top rule.
"""

# The name shown at the top of the page and in the browser tab.
SITE_TITLE = "Elisa’s Daily Brief"

# Shown in the "How to" section at the bottom of the page. Leave SUPPORT_URL empty to hide the coffee card.
REPO_URL = "https://github.com/elisamassenz/daily-brief"
SUPPORT_URL = ""   # e.g. "https://buymeacoffee.com/yourname" or "https://ko-fi.com/yourname"

SECTIONS = ["News", "Ideas & Analysis", "Business & Markets", "Technology"]

SOURCES = [
    # News
    dict(id="reuters", name="Reuters", domain="reuters.com", section="News", feed=None, mark="sans", color="#FA6400"),
    dict(id="ap", name="Associated Press", domain="apnews.com", section="News", feed=None, mark="sans", color="#E5202E"),
    dict(id="bbc", name="BBC News", domain="bbc.com", icon_domain="bbc.co.uk", section="News", feed="https://feeds.bbci.co.uk/news/rss.xml", mark="sans", color="#BB1919"),
    dict(id="nyt", name="The New York Times", domain="nytimes.com", section="News", feed="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml", mark="black", color="#121212"),
    dict(id="wapo", name="The Washington Post", domain="washingtonpost.com", section="News", feed="https://feeds.washingtonpost.com/rss/national", mark="black", color="#121212"),
    dict(id="guardian", name="The Guardian", domain="theguardian.com", section="News", feed="https://www.theguardian.com/international/rss", mark="serif", color="#052962"),
    dict(id="npr", name="NPR", domain="npr.org", section="News", feed="https://feeds.npr.org/1001/rss.xml", mark="sans", color="#D62021"),
    dict(id="propublica", name="ProPublica", domain="propublica.org", section="News", feed="https://www.propublica.org/feeds/propublica/main", mark="serif", color="#000000"),
    # Ideas & Analysis
    dict(id="economist", name="The Economist", domain="economist.com", section="Ideas & Analysis", feed="https://www.economist.com/latest/rss.xml", mark="serif", color="#E3120B"),
    dict(id="atlantic", name="The Atlantic", domain="theatlantic.com", section="Ideas & Analysis", feed="https://www.theatlantic.com/feed/all/", mark="italic", color="#E7131A"),
    dict(id="newyorker", name="The New Yorker", domain="newyorker.com", section="Ideas & Analysis", feed="https://www.newyorker.com/feed/everything", mark="serif", color="#000000"),
    dict(id="foreignaffairs", name="Foreign Affairs", domain="foreignaffairs.com", section="Ideas & Analysis", feed="https://www.foreignaffairs.com/rss.xml", mark="serif", color="#8A1C1C"),
    dict(id="axios", name="Axios", domain="axios.com", section="Ideas & Analysis", feed="https://api.axios.com/feed/", mark="sans", color="#1E5BF2"),
    # Business & Markets
    dict(id="wsj", name="The Wall Street Journal", domain="wsj.com", section="Business & Markets", feed="https://feeds.a.dj.com/rss/RSSWorldNews.xml", mark="serif", color="#111111"),
    dict(id="ft", name="Financial Times", domain="ft.com", section="Business & Markets", feed="https://www.ft.com/rss/home", mark="serif", color="#F2A0A0"),
    dict(id="bloomberg", name="Bloomberg", domain="bloomberg.com", section="Business & Markets", feed="https://feeds.bloomberg.com/markets/news.rss", mark="sans", color="#2800D7"),
    dict(id="barrons", name="Barron's", domain="barrons.com", section="Business & Markets", feed=None, mark="serif", color="#0A4A7A"),
    dict(id="nikkei", name="Nikkei Asia", domain="asia.nikkei.com", section="Business & Markets", feed="https://asia.nikkei.com/rss/feed/nar", mark="sans", color="#C8102E"),
    dict(id="quartz", name="Quartz", domain="qz.com", section="Business & Markets", feed="https://qz.com/rss", mark="sans", color="#111111"),
    # Technology
    dict(id="techcrunch", name="TechCrunch", domain="techcrunch.com", section="Technology", feed="https://techcrunch.com/feed/", mark="sans", color="#0A9E01"),
    dict(id="verge", name="The Verge", domain="theverge.com", section="Technology", feed="https://www.theverge.com/rss/index.xml", mark="sans", color="#5200FF"),
    dict(id="wired", name="Wired", domain="wired.com", section="Technology", feed="https://www.wired.com/feed/rss", mark="mono", color="#000000"),
    dict(id="ars", name="Ars Technica", domain="arstechnica.com", section="Technology", feed="https://feeds.arstechnica.com/arstechnica/index", mark="sans", color="#FF4E00"),
    dict(id="mittr", name="MIT Technology Review", domain="technologyreview.com", section="Technology", feed="https://www.technologyreview.com/feed/", mark="sans", color="#111111"),
]

# Themes watched for "mood" — when 3+ publications touch a theme on the same day,
# the dashboard reports how many and whether coverage leans negative or positive.
THEMES = {
    "Stock market": ["stock", "stocks", "wall street", "s&p", "dow", "nasdaq", "shares", "equities", "selloff", "sell-off", "investors", "bull market", "bear market"],
    "Economy": ["inflation", "recession", "jobs report", "unemployment", "gdp", "interest rate", "interest rates", "federal reserve", "the fed", "consumer spending", "layoffs", "economy", "economic"],
    "Trade & tariffs": ["tariff", "tariffs", "trade war", "trade deal", "export controls"],
    "AI": ["ai", "a.i.", "artificial intelligence", "openai", "chatgpt", "anthropic", "claude", "gemini", "chatbot", "chatbots", "llm", "nvidia"],
    "Crypto": ["bitcoin", "crypto", "cryptocurrency", "ethereum", "stablecoin", "stablecoins"],
    "Climate & weather": ["climate", "hurricane", "wildfire", "wildfires", "heat wave", "heatwave", "flood", "flooding", "emissions", "drought"],
    "Housing": ["housing", "mortgage", "mortgages", "home prices", "rent", "renters", "homebuyers"],
    "Health": ["vaccine", "vaccines", "measles", "covid", "fda", "cdc", "glp-1", "ozempic", "wegovy", "outbreak"],
}

NEGATIVE = set("""fall falls fell falling drop drops dropped plunge plunges plunged slump slumps slumped slide slides slid tumble tumbles tumbled
sink sinks sank crash crashes crashed selloff sell-off rout losses loss lose loses losing worst fear fears feared worry worries worried
warn warns warning warned risk risks risky crisis threat threatens threatened decline declines declined weak weaker weakness cut cuts
layoffs layoff recession bubble collapse collapses collapsed turmoil volatile volatility slowdown slows slowing struggle struggles struggling
plummet plummets plummeted retreat retreats retreated downturn panic chaos fraud scandal probe lawsuit sued bankrupt bankruptcy default
deadly dead death deaths killed kills attack attacks war fails failed failure shortfall miss misses missed doubts doubt concern concerns
alarm alarming grim bleak trouble troubled pressure squeeze hit hits jitters""".split())

POSITIVE = set("""rise rises rose rising rally rallies rallied surge surges surged soar soars soared jump jumps jumped gain gains gained
record records high highs boost boosts boosted climb climbs climbed rebound rebounds rebounded recover recovers recovery growth grows grew
strong stronger strength beat beats optimism optimistic upbeat win wins won breakthrough boom booming best improve improves improved
easing eases eased relief deal deals cheers hope hopes hopeful upgrade upgrades""".split())

# Tracked topics seeded on first run (editable from the dashboard).
DEFAULT_TOPICS = [
    {"name": "Brain rot & the decline of reading", "query": "\"brain rot\" OR doomscrolling OR \"reading for pleasure\" OR \"attention spans\" OR \"stopped reading\" OR \"can't read\""},
    {"name": "AI and jobs", "query": "AI (layoffs OR \"entry-level\" OR \"white-collar\" OR \"job losses\")"},
    {"name": "AI bubble", "query": "\"AI bubble\" OR \"AI spending\" OR \"AI capex\""},
    {"name": "Loneliness", "query": "loneliness OR \"social isolation\""},
]

# (symbol, display name, group). "index" shows in the top ticker; everything shows in Markets & Money.
MARKETS = [
    ("^GSPC", "S&P 500", "index"), ("^DJI", "Dow", "index"), ("^IXIC", "Nasdaq", "index"),
    ("^RUT", "Russell 2000", "index"), ("^VIX", "VIX", "index"), ("^TNX", "10-Yr Yield", "index"),
    ("CL=F", "Crude Oil", "other"), ("GC=F", "Gold", "other"), ("BTC-USD", "Bitcoin", "other"),
    ("NVDA", "Nvidia", "watch"), ("AAPL", "Apple", "watch"), ("MSFT", "Microsoft", "watch"), ("GOOGL", "Alphabet", "watch"),
    ("AMZN", "Amazon", "watch"), ("META", "Meta", "watch"), ("TSLA", "Tesla", "watch"),
]

# Publications whose whole feed counts as finance news in Markets & Money.
FINANCE_PUBS = ["wsj", "ft", "bloomberg", "barrons", "nikkei", "quartz"]
