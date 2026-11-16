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

# Local news: readers pick a city (or type a zip code) under "+ Newsrooms" and get a Local group in Front pages,
# plus the story 3+ of its newsrooms are all covering. zips = the first three digits of the zip codes it covers.
# Outlets: (id, name, domain, feed or None for Google News, mark). Prefer outlets with a working feed: every
# Google News fallback is one more request to Google each run.
def _city(cid, name, zips, outlets):
    return dict(id=cid, name=name, zips=zips, outlets=[dict(id=o[0], name=o[1], domain=o[2], feed=o[3], mark=o[4]) for o in outlets])

CITIES = [
    _city("atl", "Atlanta", "300-303 311 399", [
        ("ajc", "The Atlanta Journal-Constitution", "ajc.com", None, "serif"),
        ("atlnewsfirst", "Atlanta News First", "atlantanewsfirst.com", "https://www.atlantanewsfirst.com/arc/outboundfeeds/rss/?outputType=xml", "sans"),
        ("11alive", "11Alive", "11alive.com", "https://www.11alive.com/feeds/syndication/rss/news/local", "sans"),
        ("capitalbatl", "Capital B Atlanta", "capitalbnews.org", "https://atlanta.capitalbnews.org/feed/", "sans")]),
    _city("atx", "Austin", "786-787", [
        ("statesman", "Austin American-Statesman", "statesman.com", None, "serif"),
        ("texastrib", "The Texas Tribune", "texastribune.org", "https://www.texastribune.org/feeds/main/", "serif"),
        ("kxan", "KXAN", "kxan.com", "https://www.kxan.com/feed/", "sans"),
        ("kvue", "KVUE", "kvue.com", "https://www.kvue.com/feeds/syndication/rss/news/local", "sans")]),
    _city("bal", "Baltimore", "210-212 214", [
        ("balbanner", "The Baltimore Banner", "thebanner.com", "https://www.thebanner.com/arc/outboundfeeds/rss/?outputType=xml", "serif"),
        ("balsun", "The Baltimore Sun", "baltimoresun.com", None, "serif"),
        ("wbal", "WBAL-TV 11", "wbaltv.com", "https://www.wbaltv.com/topstories-rss", "sans"),
        ("balfishbowl", "Baltimore Fishbowl", "baltimorefishbowl.com", "https://baltimorefishbowl.com/feed/", "sans")]),
    _city("bos", "Boston", "017-027", [
        ("bosglobe", "The Boston Globe", "bostonglobe.com", "https://www.bostonglobe.com/arc/outboundfeeds/rss/?outputType=xml", "black"),
        ("wbur", "WBUR", "wbur.org", "https://www.wbur.org/rss", "sans"),
        ("bostoncom", "Boston.com", "boston.com", "https://www.boston.com/feed/", "sans"),
        ("uhub", "Universal Hub", "universalhub.com", "https://www.universalhub.com/rss.xml", "sans")]),
    _city("chi", "Chicago", "600-608", [
        ("chitrib", "Chicago Tribune", "chicagotribune.com", None, "black"),
        ("suntimes", "Chicago Sun-Times", "suntimes.com", "https://chicago.suntimes.com/rss/index.xml", "serif"),
        ("blockclub", "Block Club Chicago", "blockclubchicago.org", "https://blockclubchicago.org/feed/", "sans"),
        ("chireader", "Chicago Reader", "chicagoreader.com", "https://chicagoreader.com/feed/", "serif")]),
    _city("dfw", "Dallas–Fort Worth", "750-754 760-762", [
        ("dmn", "The Dallas Morning News", "dallasnews.com", None, "black"),
        ("wfaa", "WFAA", "wfaa.com", "https://www.wfaa.com/feeds/syndication/rss/news/local", "sans"),
        ("fwreport", "Fort Worth Report", "fortworthreport.org", "https://fortworthreport.org/feed/", "serif"),
        ("dallasobs", "Dallas Observer", "dallasobserver.com", "https://www.dallasobserver.com/dallas/Rss.xml", "sans")]),
    _city("den", "Denver", "800-806", [
        ("denpost", "The Denver Post", "denverpost.com", None, "black"),
        ("cosun", "The Colorado Sun", "coloradosun.com", "https://coloradosun.com/feed/", "serif"),
        ("denverite", "Denverite", "denverite.com", "https://denverite.com/feed/", "sans"),
        ("cpr", "CPR News", "cpr.org", "https://www.cpr.org/feed/", "sans")]),
    _city("det", "Detroit", "480-485", [
        ("detnews", "The Detroit News", "detroitnews.com", None, "black"),
        ("bridgedet", "BridgeDetroit", "bridgedetroit.com", "https://www.bridgedetroit.com/feed/", "sans"),
        ("wdet", "WDET", "wdet.org", "https://wdet.org/feed/", "sans"),
        ("wxyz", "WXYZ Detroit", "wxyz.com", "https://www.wxyz.com/news/local-news.rss", "sans")]),
    _city("hou", "Houston", "770-775", [
        ("houchron", "Houston Chronicle", "houstonchronicle.com", None, "black"),
        ("hpm", "Houston Public Media", "houstonpublicmedia.org", "https://www.houstonpublicmedia.org/feed/", "sans"),
        ("click2hou", "KPRC 2 Click2Houston", "click2houston.com", "https://www.click2houston.com/arc/outboundfeeds/rss/?outputType=xml", "sans"),
        ("khou", "KHOU 11", "khou.com", "https://www.khou.com/feeds/syndication/rss/news/local", "sans")]),
    _city("lv", "Las Vegas", "889-891", [
        ("lvrj", "Las Vegas Review-Journal", "reviewjournal.com", "https://www.reviewjournal.com/feed/", "serif"),
        ("nvindy", "The Nevada Independent", "thenevadaindependent.com", "https://thenevadaindependent.com/feed", "serif"),
        ("lvsun", "Las Vegas Sun", "lasvegassun.com", "https://lasvegassun.com/feeds/headlines/all/", "serif")]),
    _city("la", "Los Angeles", "900-918 923-928 935", [
        ("latimes", "Los Angeles Times", "latimes.com", "https://www.latimes.com/california/rss2.0.xml", "black"),
        ("laist", "LAist", "laist.com", "https://laist.com/index.atom", "sans"),
        ("ktla", "KTLA 5", "ktla.com", "https://ktla.com/feed/", "sans")]),
    _city("mia", "Miami", "330-334", [
        ("miamiherald", "Miami Herald", "miamiherald.com", None, "black"),
        ("wsvn", "WSVN 7News", "wsvn.com", "https://wsvn.com/feed/", "sans"),
        ("cbsmiami", "CBS News Miami", "cbsnews.com", "https://www.cbsnews.com/miami/latest/rss/main", "sans")]),
    _city("msp", "Minneapolis–St. Paul", "550-551 553-555", [
        ("startrib", "Star Tribune", "startribune.com", "https://www.startribune.com/local/index.rss2", "black"),
        ("sahan", "Sahan Journal", "sahanjournal.com", "https://sahanjournal.com/feed/", "sans"),
        ("minnpost", "MinnPost", "minnpost.com", "https://www.minnpost.com/feed/", "serif"),
        ("kare11", "KARE 11", "kare11.com", "https://www.kare11.com/feeds/syndication/rss/news/local", "sans")]),
    _city("nash", "Nashville", "370-372", [
        ("tennessean", "The Tennessean", "tennessean.com", None, "black"),
        ("nashbanner", "Nashville Banner", "nashvillebanner.com", "https://www.nashvillebanner.com/feed/", "serif"),
        ("wpln", "WPLN News", "wpln.org", "https://wpln.org/feed/", "sans"),
        ("wkrn", "WKRN News 2", "wkrn.com", "https://www.wkrn.com/feed/", "sans")]),
    _city("nola", "New Orleans", "700-701", [
        ("nola", "The Times-Picayune", "nola.com", None, "black"),
        ("thelens", "The Lens", "thelensnola.org", "https://thelensnola.org/feed/", "sans"),
        ("verite", "Verite News", "veritenews.org", "https://veritenews.org/feed/", "serif"),
        ("wwl", "WWL-TV", "wwltv.com", "https://www.wwltv.com/feeds/syndication/rss/news/local", "sans")]),
    _city("nyc", "New York", "070-076 078-079 088-089 100-119", [
        ("nydn", "New York Daily News", "nydailynews.com", None, "black"),
        ("gothamist", "Gothamist", "gothamist.com", "https://gothamist.com/feed", "sans"),
        ("thecity", "THE CITY", "thecity.nyc", "https://www.thecity.nyc/feed/", "sans"),
        ("amny", "amNY", "amny.com", "https://www.amny.com/feed/", "sans")]),
    _city("phl", "Philadelphia", "080-085 190-199", [
        ("inquirer", "The Philadelphia Inquirer", "inquirer.com", "https://www.inquirer.com/arc/outboundfeeds/rss/?outputType=xml", "black"),
        ("whyy", "WHYY", "whyy.org", "https://whyy.org/feed/", "sans"),
        ("billypenn", "Billy Penn", "billypenn.com", "https://billypenn.com/feed/", "sans"),
        ("phillyvoice", "PhillyVoice", "phillyvoice.com", "https://www.phillyvoice.com/feed/", "sans")]),
    _city("phx", "Phoenix", "850-853", [
        ("azcentral", "The Arizona Republic", "azcentral.com", None, "black"),
        ("azmirror", "Arizona Mirror", "azmirror.com", "https://azmirror.com/feed/", "serif"),
        ("azfamily", "Arizona's Family", "azfamily.com", "https://www.azfamily.com/arc/outboundfeeds/rss/?outputType=xml", "sans"),
        ("12news", "12News", "12news.com", "https://www.12news.com/feeds/syndication/rss/news/local", "sans")]),
    _city("pgh", "Pittsburgh", "150-152 156", [
        ("postgazette", "Pittsburgh Post-Gazette", "post-gazette.com", "https://www.post-gazette.com/rss/local", "black"),
        ("triblive", "TribLive", "triblive.com", "https://triblive.com/feed/", "sans"),
        ("publicsource", "PublicSource", "publicsource.org", "https://www.publicsource.org/feed/", "sans"),
        ("cbspgh", "CBS News Pittsburgh", "cbsnews.com", "https://www.cbsnews.com/pittsburgh/latest/rss/main", "sans")]),
    _city("pdx", "Portland", "970-972 986", [
        ("oregonian", "The Oregonian", "oregonlive.com", "https://www.oregonlive.com/arc/outboundfeeds/rss/?outputType=xml", "black"),
        ("opb", "OPB", "opb.org", "https://www.opb.org/arc/outboundfeeds/rss/?outputType=xml", "sans"),
        ("kgw", "KGW8", "kgw.com", "https://www.kgw.com/feeds/syndication/rss/news/local", "sans"),
        ("koin", "KOIN 6", "koin.com", "https://www.koin.com/feed/", "sans")]),
    _city("stl", "St. Louis", "620 622 630-631 633", [
        ("stltoday", "St. Louis Post-Dispatch", "stltoday.com", "https://www.stltoday.com/search/?f=rss&t=article&c=news/local&l=50&s=start_time&sd=desc", "black"),
        ("stlpr", "St. Louis Public Radio", "stlpr.org", None, "sans"),
        ("ksdk", "KSDK", "ksdk.com", "https://www.ksdk.com/feeds/syndication/rss/news/local", "sans"),
        ("fox2stl", "FOX 2 St. Louis", "fox2now.com", "https://fox2now.com/feed/", "sans")]),
    _city("slc", "Salt Lake City", "840-841 843-847", [
        ("sltrib", "The Salt Lake Tribune", "sltrib.com", "https://www.sltrib.com/arc/outboundfeeds/rss/?outputType=xml", "black"),
        ("deseret", "Deseret News", "deseret.com", "https://www.deseret.com/arc/outboundfeeds/rss/?outputType=xml", "serif"),
        ("ksl", "KSL", "ksl.com", "https://www.ksl.com/rss/news", "sans")]),
    _city("sd", "San Diego", "919-921", [
        ("vosd", "Voice of San Diego", "voiceofsandiego.org", "https://voiceofsandiego.org/feed/", "sans"),
        ("kpbs", "KPBS", "kpbs.org", None, "sans"),
        ("timesofsd", "Times of San Diego", "timesofsandiego.com", "https://timesofsandiego.com/feed/", "serif"),
        ("fox5sd", "FOX 5 San Diego", "fox5sandiego.com", "https://fox5sandiego.com/feed/", "sans")]),
    _city("sf", "San Francisco Bay Area", "940-951", [
        ("sfchron", "San Francisco Chronicle", "sfchronicle.com", None, "black"),
        ("sfstandard", "The San Francisco Standard", "sfstandard.com", "https://sfstandard.com/feed/", "serif"),
        ("kqed", "KQED", "kqed.org", "https://ww2.kqed.org/news/feed/", "sans"),
        ("missionlocal", "Mission Local", "missionlocal.org", "https://missionlocal.org/feed/", "sans")]),
    _city("sea", "Seattle", "980-985", [
        ("seatimes", "The Seattle Times", "seattletimes.com", "https://www.seattletimes.com/seattle-news/feed/", "black"),
        ("king5", "KING 5", "king5.com", "https://www.king5.com/feeds/syndication/rss/news/local", "sans"),
        ("stranger", "The Stranger", "thestranger.com", "https://www.thestranger.com/feed", "sans"),
        ("publicola", "PubliCola", "publicola.com", "https://publicola.com/feed/", "sans")]),
    _city("dc", "Washington, D.C.", "200-209 220-223", [
        ("wapolocal", "The Washington Post · Local", "washingtonpost.com", "https://feeds.washingtonpost.com/rss/local", "black"),
        ("wtop", "WTOP News", "wtop.com", "https://wtop.com/feed/", "sans"),
        ("wamu", "WAMU", "wamu.org", "https://wamu.org/feed/", "sans"),
        ("dccitypaper", "Washington City Paper", "washingtoncitypaper.com", "https://washingtoncitypaper.com/feed/", "sans")]),
]

# each city's newsrooms join SOURCES (section "Local", off by default; the page shows them only for the chosen city)
SOURCES += [dict(o, section="Local", city=c["id"], optional=True, color="#2B2B2B") for c in CITIES for o in c["outlets"]]

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
