"""The publications on the dashboard, grouped by section.

feed:  an RSS/Atom URL, or None to use Google News (site: search) for outlets
       that no longer publish public RSS feeds.
exclude: optional regex; headlines matching it are dropped (e.g. press releases hosted on a wire's site)
mark:  wordmark style used next to the logo — serif | italic | black | sans | mono
color: brand accent for the block's top rule.
optional: True = an extra newsroom readers can switch on in "Choose newsrooms" (off by default). The default page,
       Instagram, Rising topics and the Sunday recap use only the core outlets.
"""

# The name shown at the top of the page and in the browser tab.
SITE_TITLE = "Wallflower"

# Shown in the "How to" section at the bottom of the page. Leave SUPPORT_URL empty to hide the coffee card.
REPO_URL = ""   # set to your repo URL to show a "Make your own" card
SUPPORT_URL = "https://buymeacoffee.com/wallflowernews"
# Google Analytics 4 measurement ID ("G-XXXXXXXXXX"); empty = no analytics. Only the public site gets it.
GA_ID = "G-XSBQG2JKS5"
# "Report a problem" form (e.g. a Google Form link, so no email address is public); empty hides the link.
REPORT_URL = "https://forms.gle/tuqskG5WR36Tq4wd6"
# Instagram profile; empty hides the "Follow on Instagram" button. Set it once the intro post is live.
INSTAGRAM_URL = "https://www.instagram.com/wallflower.news/"

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
    dict(id="afp", name="Agence France-Presse", domain="afp.com", section="News", feed=None, mark="sans", color="#0A3D91",
         icon_url="https://www.afp.com/themes/custom/afp9/assets/images/favicon_afp.com_201120.ico",
         # afp.com also hosts companies' press releases (Title Case "Announces", trademarks, earnings): keep the news
         sentence_case=True, exclude=r"^\W|^(Fact Check|Inside AFP)$|AFP Fakty|Checamos|™|®|\b(Announces|Introduces|Launches|Unveils|Completes|Appoints|Expands|Partners|Reports|Declares|Celebrates|Recognized|Selected|Webinar|Phase [1-3]|Quarter|Fiscal|Dividend|Earnings)\b"),
    dict(id="dw", name="Deutsche Welle", domain="dw.com", section="News", feed="https://rss.dw.com/xml/rss-en-top", mark="sans", color="#05B2FC"),
    dict(id="abcau", name="ABC News Australia", domain="abc.net.au", section="News", feed="https://www.abc.net.au/news/feed/51120/rss.xml", mark="sans", color="#000000"),
    dict(id="cbc", name="CBC News", domain="cbc.ca", section="News", feed="https://www.cbc.ca/webfeed/rss/rss-topstories", mark="sans", color="#E60505"),
    dict(id="propublica", name="ProPublica", domain="propublica.org", section="News", feed="https://www.propublica.org/feeds/propublica/main", mark="serif", color="#000000"),
    # News: extra newsrooms, off by default (center-right and international range)
    dict(id="telegraph", name="The Telegraph", domain="telegraph.co.uk", section="News", feed=None, mark="black", color="#1A1A1A", optional=True),
    dict(id="times", name="The Times", domain="thetimes.com", section="News", feed=None, mark="black", color="#1A1A1A", optional=True),
    dict(id="natpost", name="National Post", domain="nationalpost.com", section="News", feed=None, mark="serif", color="#D0021B", optional=True),
    dict(id="japannews", name="The Japan News", domain="japannews.yomiuri.co.jp", section="News", feed=None, mark="sans", color="#1C3F94", optional=True),
    # Ideas & Analysis
    dict(id="economist", name="The Economist", domain="economist.com", section="Ideas & Analysis", feed="https://www.economist.com/latest/rss.xml", mark="serif", color="#E3120B"),
    dict(id="atlantic", name="The Atlantic", domain="theatlantic.com", section="Ideas & Analysis", feed="https://www.theatlantic.com/feed/all/", mark="italic", color="#E7131A"),
    dict(id="axios", name="Axios", domain="axios.com", section="Ideas & Analysis", feed="https://api.axios.com/feed/", mark="sans", color="#1E5BF2"),
    # Ideas & Analysis: extra newsrooms, off by default
    dict(id="dispatch", name="The Dispatch", domain="thedispatch.com", section="Ideas & Analysis", feed="https://thedispatch.com/feed/", mark="serif", color="#1B2A4A", optional=True),
    dict(id="natreview", name="National Review", domain="nationalreview.com", section="Ideas & Analysis", feed="https://www.nationalreview.com/feed/", mark="serif", color="#C8102E", optional=True),
    dict(id="reason", name="Reason", domain="reason.com", section="Ideas & Analysis", feed="https://reason.com/feed/", mark="sans", color="#E8571F", optional=True,
         exclude=r"^\S+$|^Open Thread$|^Today in Supreme Court History"),   # its feed also lists bare image names
    dict(id="vox", name="Vox", domain="vox.com", section="Ideas & Analysis", feed="https://www.vox.com/rss/index.xml", mark="black", color="#E5D80F", optional=True),
    dict(id="nation", name="The Nation", domain="thenation.com", section="Ideas & Analysis", feed=None, mark="serif", color="#C8102E", optional=True),
    # Business & Markets
    dict(id="wsj", name="The Wall Street Journal", domain="wsj.com", section="Business & Markets", feed="https://feeds.a.dj.com/rss/RSSWorldNews.xml", mark="serif", color="#111111"),
    dict(id="ft", name="Financial Times", domain="ft.com", section="Business & Markets", feed="https://www.ft.com/rss/home", mark="serif", color="#F2A0A0"),
    dict(id="bloomberg", name="Bloomberg", domain="bloomberg.com", section="Business & Markets", feed="https://feeds.bloomberg.com/markets/news.rss", mark="sans", color="#2800D7"),
    dict(id="nikkei", name="Nikkei Asia", domain="asia.nikkei.com", section="Business & Markets", feed="https://asia.nikkei.com/rss/feed/nar", mark="sans", color="#C8102E"),
    dict(id="afr", name="Australian Financial Review", domain="afr.com", section="Business & Markets", feed="https://www.afr.com/rss/feed.xml", mark="serif", color="#0B3C5D", optional=True),
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


# (symbol, display name, group). "index" shows in the top ticker; everything shows in Markets & Money.
MARKETS = [
    ("^GSPC", "S&P 500", "index"), ("^DJI", "Dow", "index"), ("^IXIC", "Nasdaq", "index"),
    ("^RUT", "Russell 2000", "index"), ("^VIX", "VIX", "index"), ("^TNX", "10-Yr Yield", "index"),
    ("CL=F", "Crude Oil", "other"), ("GC=F", "Gold", "other"), ("BTC-USD", "Bitcoin", "other"),
    ("NVDA", "Nvidia", "watch"), ("AAPL", "Apple", "watch"), ("MSFT", "Microsoft", "watch"), ("GOOGL", "Alphabet", "watch"),
    ("AMZN", "Amazon", "watch"), ("META", "Meta", "watch"), ("TSLA", "Tesla", "watch"),
]

# Publications whose whole feed counts as finance news in Markets & Money.
FINANCE_PUBS = ["wsj", "ft", "bloomberg", "nikkei"]
