(() => {
  const $ = (s) => document.querySelector(s);
  const app = $("#app");
  let DATA = null;
  let MKT = null;
  let SRC = {};
  let lastGenerated = null;
  // The public site (built by build.py) is plain files: no refresh endpoint, no topic editing.
  const STATIC = !!document.querySelector('meta[name="static-build"]');

  // ------------------------------------------------------------ helpers
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const safeUrl = (u) => (/^https?:\/\//i.test(u || "") ? esc(u) : "#");
  const ext = (u) => `href="${safeUrl(u)}" target="_blank" rel="noopener noreferrer"`;

  function ago(iso) {
    if (!iso) return "";
    const s = (Date.now() - new Date(iso).getTime()) / 1000;
    if (s < 60) return "just now";
    if (s < 3600) return `${Math.round(s / 60)} min ago`;
    if (s < 86400) return `${Math.round(s / 3600)} hr ago`;
    const d = Math.round(s / 86400);
    return d === 1 ? "yesterday" : `${d} days ago`;
  }
  const logo = (pid, cls = "") => `<img class="logo ${cls}" src="${esc(SRC[pid]?.icon || `logo/${pid}.png`)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">`;
  const pubtag = (pid) => `<span class="pubtag">${logo(pid)}<span class="pn">${esc(SRC[pid]?.name || pid)}</span></span>`;
  const image = (src, alt = "") => src
    ? `<div class="img-wrap"><img src="${safeUrl(src)}" alt="${esc(alt)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.closest('.img-wrap').remove()"></div>`
    : "";
  // soft abstract gradients stand in for missing photos and fill empty space
  const PALETTES = [["#F4BE94", "#DCCFF0"], ["#C4BEF0", "#F5CDB6"], ["#B9CDA4", "#F3DF9C"], ["#F2D97E", "#F1B9A4"],
    ["#AFCDE8", "#CFE0BC"], ["#EFAE9C", "#D8D2F2"], ["#BFD3A9", "#B8D2EC"]];
  function hash(str) { let h = 0; for (const c of String(str)) h = (h * 31 + c.charCodeAt(0)) | 0; return Math.abs(h); }
  function art(seed, cls = "") {
    const h = hash(seed);
    const [a, b] = PALETTES[h % PALETTES.length];
    const x1 = 20 + (h % 30), y1 = 25 + ((h >> 3) % 30), x2 = 60 + ((h >> 5) % 25), y2 = 50 + ((h >> 7) % 30);
    return `<div class="art ${cls}" aria-hidden="true" style="--a:${a};--b:${b};--x1:${x1}%;--y1:${y1}%;--x2:${x2}%;--y2:${y2}%"></div>`;
  }
  const stack = (pids, max = 8) => `<span class="logo-stack">${pids.slice(0, max).map((p) => logo(p)).join("")}</span>`;
  const plural = (n, w) => `${n} ${n === 1 ? w : w.endsWith("y") ? w.slice(0, -1) + "ies" : w + "s"}`;

  function sectionHead(num, eyebrow, title, dek, aside = "") {
    return `<header class="sec-head">
      <div class="sec-num">${num}</div>
      <div class="sec-text">
        <div class="sec-eyebrow">${esc(eyebrow)}</div>
        <h2 class="sec-title">${title}</h2>
        <p class="sec-dek">${dek || ""}</p>
      </div>
      ${aside ? `<div class="sec-aside">${aside}</div>` : ""}
    </header>`;
  }
  const subHead = (title) => `<div class="sub-head"><h3>${title}</h3></div>`;

  // ------------------------------------------------------------ tooltip (bars & charts)
  const tip = document.createElement("div");
  tip.className = "tip";
  document.body.appendChild(tip);
  document.addEventListener("mousemove", (e) => {
    const chart = e.target.closest("svg[data-vals]");
    document.querySelectorAll(".hover-dot").forEach((d) => { if (!chart || !chart.contains(d)) d.style.display = "none"; });
    if (chart) {
      const vals = JSON.parse(chart.dataset.vals);
      const pts = chart.dataset.pts.split(" ");
      const r = chart.getBoundingClientRect();
      const i = Math.max(0, Math.min(vals.length - 1, Math.round(((e.clientX - r.left) / r.width) * (vals.length - 1))));
      const [x, y] = pts[i].split(",");
      const dot = chart.querySelector(".hover-dot");
      dot.setAttribute("cx", x); dot.setAttribute("cy", y); dot.style.display = "block";
      tip.textContent = `${chart.dataset.label} ${fmt(vals[i], chart.dataset.sym)}`;
      tip.style.display = "block";
      tip.style.left = `${r.left + (Number(x) / 200) * r.width}px`;
      tip.style.top = `${r.top + (Number(y) / 64) * r.height}px`;
      return;
    }
    const b = e.target.closest("[data-tip]");
    if (!b) { tip.style.display = "none"; return; }
    tip.textContent = b.dataset.tip;
    tip.style.display = "block";
    const r = b.getBoundingClientRect();
    tip.style.left = `${r.left + r.width / 2}px`;
    tip.style.top = `${r.top}px`;
  });

  // ------------------------------------------------------------ 01 trending today
  function coverage(angles, show) {
    const items = angles.map((a, i) => `
      <li class="angle" ${i >= show ? "hidden data-more" : ""}>
        ${pubtag(a.pub)}
        <a class="t" ${ext(a.link)}>${esc(a.title)}</a>
      </li>`).join("");
    const more = angles.length > show
      ? `<button class="more-btn" data-expand>+ ${plural(angles.length - show, "more outlet")}</button>` : "";
    return `<div class="coverage">
      <div class="coverage-label">How it’s covered</div>
      <ul class="angles">${items}</ul>${more}
    </div>`;
  }

  const leadLink = (s) => (s.angles.find((x) => x.title === s.headline) || s.angles[0] || {}).link;
  const storyEyebrow = (s, n) => `<div class="eyebrow"><span class="${n === 1 ? "acc" : "num"}">${n === 1 ? "Top story" : n}</span> · ${s.pub_count} publications</div>`;
  const meta = (s) => `<div class="story-meta">${stack(s.angles.map((a) => a.pub))}</div>`;

  function renderTrending(stories) {
    if (!stories.length) return `<p class="collecting">No single story is being covered by three or more publications right now.</p>`;
    const [lead, ...rest] = stories;
    const top = rest.slice(0, 6);
    let n = 1;
    return `
    <article class="story story-lead">
      ${lead.image ? `<a class="lead-img" ${ext(leadLink(lead))}>${image(lead.image)}</a>` : ""}
      ${storyEyebrow(lead, 1)}
      <h3><a class="hl" ${ext(leadLink(lead))}>${esc(lead.headline)}</a></h3>
      ${lead.summary ? `<p class="summary">${esc(lead.summary)}</p>` : ""}
      ${meta(lead)}
      ${coverage(lead.angles, lead.angles.length)}
    </article>
    <div class="story-grid">${top.map((s, i) => `
      <article class="story card ${i >= 2 ? "extra" : ""}">
        <div class="card-top ${s.image ? "" : "no-thumb"}">
          <div>
            ${storyEyebrow(s, ++n)}
            <h3><a class="hl" ${ext(leadLink(s))}>${esc(s.headline)}</a></h3>
          </div>
          ${s.image ? `<a class="thumb" ${ext(leadLink(s))}>${image(s.image)}</a>` : ""}
        </div>
        ${coverage(s.angles, 3)}
      </article>`).join("")}
    </div>
    ${top.length > 2 ? `<button class="show-more" data-show-more>Show ${plural(top.length - 2, "more story")}</button>` : ""}`;
  }

  // ------------------------------------------------------------ 02 markets & money
  function fmt(n, sym) {
    if (n == null) return "—";
    const digits = n >= 1000 ? 0 : 2;
    return n.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }
  const pct = (p) => (p == null ? "" : `${p >= 0 ? "▲" : "▼"} ${Math.abs(p).toFixed(2)}%`);
  const dir = (p) => ((p ?? 0) >= 0 ? "up" : "down");
  const quote = (sym) => (MKT?.quotes || []).find((x) => x.symbol === sym);

  function marketVerdict() {
    const sp = quote("^GSPC"), nq = quote("^IXIC"), dj = quote("^DJI"), vix = quote("^VIX");
    if (!sp || sp.pct == null) return null;
    const p = sp.pct;
    let head, level = "calm";
    if (p <= -2) { head = "Stocks are taking a nosedive"; level = "alarm"; }
    else if (p <= -1) { head = "Stocks are sliding"; level = "down"; }
    else if (p < -0.3) head = "Stocks are edging lower";
    else if (p <= 0.3) head = "Stocks are roughly flat";
    else if (p < 1) head = "Stocks are edging higher";
    else if (p < 2) { head = "Stocks are rallying"; level = "up"; }
    else { head = "Stocks are surging"; level = "up"; }
    if (nq && dj && nq.pct != null && dj.pct != null) {
      const gap = nq.pct - dj.pct;
      if (gap <= -0.6) head += ", with tech lagging";
      else if (gap >= 0.6) head += ", led by tech";
    }
    let dek = [sp, nq, dj].filter(Boolean).map((x) => `${esc(x.name)} <b class="${dir(x.pct)}">${pct(x.pct)}</b>`).join(" &nbsp;·&nbsp; ");
    if (vix && vix.price != null && (vix.pct >= 10 || vix.price >= 25)) {
      dek += ` &nbsp;·&nbsp; <b class="down">Volatility is spiking</b> (VIX ${vix.price.toFixed(1)})`;
      if (vix.price >= 30) level = "alarm";
    }
    return { head, dek, level };
  }

  function lineChart(m) {
    const vals = m.spark || [];
    if (vals.length < 2) return "";
    const all = m.prev ? vals.concat([m.prev]) : vals;
    const min = Math.min(...all), max = Math.max(...all), rng = max - min || 1;
    const y = (v) => (4 + (1 - (v - min) / rng) * 56).toFixed(1);
    const pts = vals.map((v, i) => `${((i / (vals.length - 1)) * 200).toFixed(1)},${y(v)}`).join(" ");
    const base = m.prev ? `<line x1="0" x2="200" y1="${y(m.prev)}" y2="${y(m.prev)}" class="baseline" vector-effect="non-scaling-stroke"/>` : "";
    return `<svg class="chart" viewBox="0 0 200 64" preserveAspectRatio="none" data-vals="${esc(JSON.stringify(vals))}" data-pts="${pts}" data-sym="${esc(m.symbol)}" data-label="${esc(m.name)}" role="img" aria-label="${esc(m.name)} today">
      ${base}<polyline points="${pts}" class="line ${dir(m.pct)}" vector-effect="non-scaling-stroke"/>
      <circle class="hover-dot" r="3" style="display:none"/></svg>`;
  }

  function marketStateLabel() {
    const st = MKT?.movers?.market_state || "";
    // Yahoo states: PRE / REGULAR / POST are live sessions; PREPRE, POSTPOST and CLOSED mean closed
    if (st === "REGULAR") return "Open";
    if (st === "PRE") return "Pre-market";
    if (st === "POST") return "After hours";
    if (st) return "Closed";
    return "";
  }

  function moverList(title, rows) {
    if (!rows || !rows.length) return "";
    return `<div class="movers-col">
      <h4>${title}</h4>
      <ul class="movers">${rows.map((r) => `
        <li>
          <div class="mover-row">
            <span class="sym">${esc(r.symbol)}</span>
            <span class="mname">${esc(r.name)}</span>
            <span class="pill ${dir(r.pct)}">${pct(r.pct)}</span>
          </div>
          ${r.news ? `<a class="mnews" ${ext(r.news.link)}>${logo(r.news.pub)}<span>${esc(r.news.title)}</span></a>` : ""}
        </li>`).join("")}
      </ul></div>`;
  }

  function renderMarkets() {
    const el = $("#markets-body");
    if (!el) return;
    if (!MKT) { el.innerHTML = `<p class="collecting">Loading market data…</p>`; return; }
    const v = marketVerdict();
    if (v) {
      $("#markets .sec-title").textContent = v.head;
      $("#markets .sec-dek").innerHTML = `${v.dek}${marketStateLabel() ? ` &nbsp;·&nbsp; <span class="muted">${esc(marketStateLabel())}</span>` : ""}`;
      $("#markets").dataset.level = v.level;
    }
    const cards = (MKT.quotes || []).filter((m) => m.group === "index");
    const other = (MKT.quotes || []).filter((m) => m.group === "other");
    const watch = (MKT.quotes || []).filter((m) => m.group === "watch");
    const chips = (list) => list.map((m) => `<span class="chip">${esc(m.name)} <b class="${dir(m.pct)}">${pct(m.pct)}</b></span>`).join("");
    const mv = MKT.movers || {};
    el.innerHTML = `
      <div class="index-cards">${cards.map((m) => `
        <div class="index-card">
          <div class="ic-name">${esc(m.name)}</div>
          <div class="ic-price">${fmt(m.price, m.symbol)}</div>
          <div class="ic-ch ${dir(m.pct)}">${pct(m.pct)}</div>
          ${lineChart(m)}
        </div>`).join("")}
      </div>
      <div class="watch">
        <span class="kicker">Big tech</span>${chips(watch)}
        <span class="kicker" style="margin-left:14px">Other</span>${chips(other)}
      </div>
      <div class="money-grid">
        <div>
          ${subHead("Hot stocks", "The day’s biggest moves among companies worth $10B+, with a headline from your publications when one explains it")}
          <div class="movers-grid">
            ${moverList("Biggest gainers", mv.day_gainers)}
            ${moverList("Biggest decliners", mv.day_losers)}
            ${moverList("Most traded", mv.most_actives)}
          </div>
        </div>
        <div>
          ${subHead("Market headlines", "Markets and economy coverage from the financial press and beyond")}
          <ul class="ex fin-news">${(DATA?.finance || []).slice(0, 10).map((e) => `
            <li>${logo(e.pub)}<a ${ext(e.link)}>${esc(e.title)}</a><span class="when">${esc(ago(e.date))}</span></li>`).join("")}
          </ul>
        </div>
      </div>`;
  }

  function renderTicker() {
    const idx = (MKT?.quotes || []).filter((m) => m.group === "index");
    $("#ticker").innerHTML = idx.map((m) => `
      <a class="tick" href="#markets"><span class="nm">${esc(m.name)}</span><span class="px">${fmt(m.price, m.symbol)}</span><span class="ch ${dir(m.pct)}">${pct(m.pct)}</span></a>`).join("");
  }

  // ------------------------------------------------------------ 04 over the weeks
  function bars(values, labels, recentFrom, tipFor) {
    const max = Math.max(1, ...values);
    return `<div class="bars">${values.map((v, i) => `
      <div class="b ${i >= recentFrom ? "recent" : ""}" style="height:${Math.max(3, (v / max) * 100)}%" data-tip="${esc(tipFor(v, i))}"></div>`).join("")}
    </div><div class="bars-axis"><span>${esc(labels[0])}</span><span>${esc(labels[1])}</span></div>`;
  }

  function trendStat(recent, prior) {
    if (recent < 3 && prior < 3) return "";  // too few articles for a ratio to mean anything
    if (!prior) return recent ? `<span class="up">New this week</span>` : "";
    const r = recent / prior;
    if (r >= 1.15) return `<span class="up">▲ ${r.toFixed(1)}× usual</span>`;
    if (r <= 0.85) return `<span class="down">▼ ${r.toFixed(1)}× usual</span>`;
    return `steady`;
  }

  function renderTopics(topics, mine = false) {
    const weekLabel = ["3 weeks ago", "2 weeks ago", "Last week", "This week"];
    return topics.map((t) => `
      <div class="topic">
        <div>
          <h4>${esc(t.name)}<button class="remove ${mine ? "mine" : ""}" ${mine ? "data-remove-mine" : "data-remove"}="${esc(t.name)}" title="Stop tracking">✕</button></h4>
          <div class="stat">${stack(t.pubs, 8)} ${[plural(t.last7, "article") + " this week", trendStat(t.last7, t.prior7_avg)].filter(Boolean).join(" · ")}</div>
        </div>
        <div>${bars(t.weekly, ["4 wks ago", "this wk"], 3, (v, i) =>
          `${weekLabel[i]}: ${plural(v, "headline")} in your publications${t.web_weekly ? ` · ${t.web_weekly[i]}${t.capped[i] ? "+" : ""} across the web` : ""}`)}</div>
        <ul class="ex">${t.examples.slice(0, 4).map((e) => `
          <li>${logo(e.pub)}<a ${ext(e.link)}>${esc(e.title)}</a><span class="when">${esc(ago(e.date).replace(" ago", ""))}</span></li>`).join("") ||
          `<li class="none">No matching headlines in the last 4 weeks yet.</li>`}
        </ul>
      </div>`).join("");
  }

  // Visitors to the public site track their own topics: saved in their browser, matched against the
  // last 4 weeks of headlines the site has saved (data/archive.json, built by build.py).
  const MY_KEY = "dailyBrief.myTopics";
  const loadMine = () => { try { return JSON.parse(localStorage.getItem(MY_KEY)) || []; } catch { return []; } };
  const saveMine = (list) => { try { localStorage.setItem(MY_KEY, JSON.stringify(list)); } catch { /* private mode */ } };
  let archivePromise = null;
  const archive = () => (archivePromise = archivePromise ||
    fetch(`data/archive.json?t=${encodeURIComponent(DATA?.generated || "")}`).then((r) => r.json()).catch(() => (archivePromise = null)));

  // "ozempic, wegovy, \"GLP-1\"" or "ozempic OR wegovy": any alternative may match; words in one alternative must all appear
  function matcher(name, query) {
    const alts = [name, ...(query || "").split(/\s+OR\s+|,/i)].map((x) => x.trim()).filter(Boolean);
    const tests = alts.map((alt) => {
      const quoted = alt.match(/^"(.+)"$/);
      const words = quoted ? [quoted[1]] : alt.replace(/[()"]/g, " ").split(/\s+/).filter((w) => w.length > 1);
      const res = words.map((w) => new RegExp(`(^|[^\\p{L}\\p{N}])${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "iu"));
      return (text) => res.length > 0 && res.every((re) => re.test(text));
    });
    return (text) => tests.some((t) => t(text));
  }

  function computeMine(t, arc) {
    const test = matcher(t.name, t.query);
    const last = arc.days.length - 1;
    const weekly = [0, 0, 0, 0];
    const hits = [];
    for (const [di, pi, title, desc, link] of arc.items) {
      const age = last - di;
      if (age > 27 || !test(`${title} ${desc}`)) continue;
      weekly[3 - Math.floor(age / 7)] += 1;
      hits.push({ di, pub: arc.pubs[pi], title, link });
    }
    hits.sort((a, b) => b.di - a.di);
    const seen = new Set(), examples = [];
    for (const h of hits) {
      if (seen.has(h.pub)) continue;
      seen.add(h.pub);
      examples.push({ pub: h.pub, title: h.title, link: h.link, date: arc.days[h.di] + "T12:00:00Z" });
    }
    const order = DATA.sources.map((x) => x.id);
    return { name: t.name, query: t.query, weekly, last7: weekly[3], prior7_avg: (weekly[0] + weekly[1] + weekly[2]) / 3,
      pubs: [...seen].sort((a, b) => order.indexOf(a) - order.indexOf(b)), examples };
  }

  async function renderTopicList() {
    const el = $("#topics");
    if (!el) return;
    let html = renderTopics(DATA.topics);
    const mine = STATIC ? loadMine() : [];
    if (mine.length) {
      const arc = await archive();
      if (arc) html += renderTopics(mine.map((t) => computeMine(t, arc)), true);
    }
    el.innerHTML = html;
  }

  function renderRising(rising) {
    const need = 7;
    if (rising.topics.length) {
      return subHead("Rising in your feeds", "Names and phrases taking up a growing share of headlines") + rising.topics.map((t) => {
        const recentFrom = t.series.length - Math.min(7, Math.max(1, Math.floor(t.series.length / 3)));
        return `
        <div class="topic">
          <div>
            <h4>${esc(t.label)}</h4>
            <div class="stat">${stack(t.pubs, 8)} <span class="up">▲ ${t.growth}× earlier share</span></div>
          </div>
          <div>${bars(t.series, [t.days[0].slice(5), "today"], recentFrom, (v, i) => `${t.days[i]}: ${plural(v, "article")}`)}</div>
          <ul class="ex">${t.examples.slice(0, 4).map((e) => `
            <li>${logo(e.pub)}<a ${ext(e.link)}>${esc(e.title)}</a><span class="when">${esc(e.day.slice(5))}</span></li>`).join("")}
          </ul>
        </div>`;
      }).join("");
    }
    const n = Math.min(rising.days_collected, need);
    return `${subHead("Rising in your feeds", "Detected automatically from the headlines the dashboard saves each day")}
      <div class="collecting">
        Fills in after a week of saved headlines.
        <div class="progress"><div style="width:${(n / need) * 100}%"></div></div>
        <div class="kicker" style="margin-top:8px">${n} of ${need} days collected</div>
      </div>
      ${(rising.leaders || []).length ? `
      ${subHead("Most widely covered this month")}
      ${rising.leaders.map((t) => `
        <div class="topic">
          <div>
            <h4>${esc(t.label)}</h4>
            <div class="stat">${stack(t.pubs, 8)} ${t.pubs.length} publications</div>
          </div>
          <div></div>
          <ul class="ex">${t.examples.map((e) => `
            <li>${logo(e.pub)}<a ${ext(e.link)}>${esc(e.title)}</a><span class="when">${esc(e.day.slice(5))}</span></li>`).join("")}
          </ul>
        </div>`).join("")}` : ""}`;
  }

  // ------------------------------------------------------------ 05 front pages
  function pubHead(src) {
    const mark = src.wordmark
      ? `<img class="wm" src="logos/${esc(src.id)}.svg" alt="${esc(src.name)}">`
      : `${logo(src.id, "lg")}<span class="wordmark ${esc(src.mark)}">${esc(src.name)}</span>`;
    return `<div class="pub-head" data-pub="${esc(src.id)}" style="--brand:${esc(src.color)}">${mark}</div>`;
  }

  function renderPub(src, items) {
    const [a, b] = items || [];
    if (!a) return `<article class="pub">${pubHead(src)}<p class="empty">Couldn’t reach this feed right now.</p></article>`;
    return `
    <article class="pub">
      ${pubHead(src)}
      <a class="lead hl" ${ext(a.link)}>
        ${image(a.image)}
        <h3 class="hl-text">${esc(a.title)}</h3>
        ${a.desc ? `<p class="dek">${esc(a.desc)}</p>` : ""}
        <div class="when">${esc(ago(a.date))}</div>
      </a>
      ${b ? `
      <a class="second hl ${b.image ? "" : "noimg"}" ${ext(b.link)}>
        <div><h4 class="hl-text">${esc(b.title)}</h4><div class="when">${esc(ago(b.date))}</div></div>
        ${image(b.image)}
      </a>` : ""}
    </article>`;
  }

  // ------------------------------------------------------------ 05 how to
  const ICON = {
    share: '<svg viewBox="0 0 24 24"><path d="M12 3v12M7.5 7.5 12 3l4.5 4.5"/><path d="M8 11H6a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1h-2"/></svg>',
    plus: '<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="4"/><path d="M12 8.5v7M8.5 12h7"/></svg>',
    dots: '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1.4"/><circle cx="12" cy="12" r="1.4"/><circle cx="12" cy="19" r="1.4"/></svg>',
    phone: '<svg viewBox="0 0 24 24"><rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/></svg>',
    copy: '<svg viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2.5"/><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2"/></svg>',
    cup: '<svg viewBox="0 0 24 24"><path d="M5 9h11v6a5 5 0 0 1-5 5h-1a5 5 0 0 1-5-5z"/><path d="M16 11h1.5a2.5 2.5 0 0 1 0 5H16"/><path d="M8.5 3.5c-.6 1 .6 1.5 0 2.5M12 3.5c-.6 1 .6 1.5 0 2.5"/></svg>',
  };
  const step = (icon, html) => `<li><span class="step-icon">${ICON[icon]}</span><span>${html}</span></li>`;

  function renderHowTo() {
    const platform = (name, app, steps) => `
      <div class="platform"><p class="kicker">${name} · ${app}</p><ol class="steps">${steps}</ol></div>`;
    return `<div class="howto-card howto-install">
      ${platform("iPhone", "Safari",
        step("share", "Tap <b>Share</b> at the bottom of Safari") + step("plus", "Choose <b>Add to Home Screen</b>, then <b>Add</b>"))}
      ${platform("Android", "Chrome",
        step("dots", "Tap the <b>⋮</b> menu at the top right") + step("plus", "Choose <b>Add to Home screen</b>"))}
    </div>`;
  }

  function renderSupport(data) {
    if (!data.support_url) return "";
    return `<section id="support" class="sec support">
      <div class="howto-card support-card">
        <div class="howto-head"><span class="howto-icon">${ICON.cup}</span><h3>Support ${esc(data.title)}</h3></div>
        <p>This brief is a free side project. If it's part of your morning, you can buy me a coffee.</p>
        <a class="howto-btn" ${ext(data.support_url)}>Buy me a coffee →</a>
      </div>
    </section>`;
  }

  // ------------------------------------------------------------ page
  function render(data) {
    DATA = data;
    if (data.title) { document.title = data.title; $(".masthead-title").textContent = data.title; }
    const navSupport = $("#nav-support");
    navSupport.hidden = !data.support_url;
    navSupport.lastChild.textContent = `Support ${data.title || ""}`.trim();
    SRC = Object.fromEntries(data.sources.map((s) => [s.id, s]));
    app.innerHTML = `
      <section id="today" class="sec">
        ${sectionHead("01", "Trending today", "What everyone is covering")}
        ${renderTrending(data.trending)}
      </section>

      <section id="fronts" class="sec">
        ${sectionHead("02", "Front pages", "Every publication’s top two")}
        ${data.sections.map((sec) => `
          <div class="pub-section">
            ${subHead(esc(sec))}
            <div class="pubs">${data.sources.filter((s) => s.section === sec).map((s) => renderPub(s, data.headlines[s.id])).join("")}</div>
          </div>`).join("")}
      </section>

      <section id="markets" class="sec">
        ${sectionHead("03", "Markets & money", "Markets")}
        <div id="markets-body"></div>
      </section>


      <section id="weeks" class="sec">
        ${sectionHead("04", "Trending over the weeks", "Stories that keep coming back")}
        <div class="longview">
          <div class="lv-col">
            ${subHead("Topics you’re tracking")}
            <div id="topics">${renderTopics(data.topics)}</div>
            <form class="add-topic" id="add-topic">
              <input name="name" placeholder="Track a topic, e.g. Ozempic" required maxlength="80">
              <input name="query" placeholder='Other words (optional), e.g. wegovy, "GLP-1"' maxlength="300">
              <button type="submit">Track</button>
            </form>
          </div>
          <div class="lv-col">${renderRising(data.rising)}</div>
        </div>
      </section>

      <section id="howto" class="sec">
        ${sectionHead("05", "How to", `Add ${esc(data.title || "it")} to your Home Screen`)}
        ${renderHowTo()}
      </section>
      ${renderSupport(data)}`;
    renderMarkets();
    if (STATIC && loadMine().length) renderTopicList();
    updateStamp();
    queueFit();
    document.querySelectorAll("section.sec").forEach((s) => navObserver.observe(s));
  }

  // Blurred, closely cropped flower photos (free Unsplash licence) for gaps at the end of a grid row.
  const BLOOMS = [
    { id: "1749587452511-d615311b854d", pos: "58% 33%", size: "320%" },   // pink poppy petals, Lorin Both
    { id: "1649219088222-33f44270bdcb", pos: "55% 44%", size: "380%" },   // pink cluster, Nile Pereira
    { id: "1580411788274-e75779dc08f2", pos: "70% 64%", size: "360%" },   // pale tulip, Annie Spratt
    { id: "1770650776137-d9e749697fc4", pos: "50% 27%", size: "520%" },   // blurred red tulip, Danielle Suijkerbuijk
  ];

  function fitFills() {
    // pad the last row of each publication grid with a blurred flower crop
    let k = 0;
    document.querySelectorAll(".pubs").forEach((grid) => {
      grid.querySelectorAll(".pad-tile").forEach((t) => t.remove());
      const cols = getComputedStyle(grid).gridTemplateColumns.split(" ").length;
      const n = grid.querySelectorAll(".pub").length;
      const empty = (cols - (n % cols)) % cols;
      if (!empty) return;
      const b = BLOOMS[k++ % BLOOMS.length];
      grid.insertAdjacentHTML("beforeend", `<div class="pad-tile" aria-hidden="true" style="grid-column: span ${empty}">
        <div class="pad-photo" style="background-image:url('https://images.unsplash.com/photo-${b.id}?w=1200&q=70&auto=format');background-position:${b.pos};background-size:${b.size} auto"></div></div>`);
    });
  }
  let fitTimer;
  const queueFit = () => { clearTimeout(fitTimer); fitTimer = setTimeout(fitFills, 120); };
  document.addEventListener("load", (e) => { if (e.target.tagName === "IMG") queueFit(); }, true);
  window.addEventListener("resize", queueFit);
  document.addEventListener("error", (e) => { if (e.target.tagName === "IMG") queueFit(); }, true);

  function updateStamp() {
    if (DATA) $("#updated").textContent = `Updated ${ago(DATA.generated)}`;
  }

  // section nav: highlight the section in view
  const navObserver = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) {
        document.querySelectorAll("#secnav a").forEach((a) => {
          const on = a.getAttribute("href") === `#${en.target.id}`;
          a.classList.toggle("on", on);
          // on narrow screens the bar scrolls sideways: keep the active tab visible
          if (on) a.parentElement.scrollTo({ left: a.offsetLeft - 16, behavior: "smooth" });
        });
      }
    });
  }, { rootMargin: "-30% 0px -65% 0px" });

  // expand / remove / add (delegated)
  app.addEventListener("click", async (e) => {
    const sm = e.target.closest("[data-show-more]");
    if (sm) {
      sm.previousElementSibling.classList.add("expanded");
      sm.remove();
      return;
    }
    const ex = e.target.closest("[data-expand]");
    if (ex) {
      ex.previousElementSibling.querySelectorAll("[data-more]").forEach((li) => (li.hidden = false));
      ex.remove();
      return;
    }
    const rmMine = e.target.closest("[data-remove-mine]");
    if (rmMine) {
      saveMine(loadMine().filter((t) => t.name !== rmMine.dataset.removeMine));
      renderTopicList();
      return;
    }
    const rm = e.target.closest("[data-remove]");
    if (rm) {
      rm.disabled = true;
      const topics = await post({ action: "remove", name: rm.dataset.remove });
      if (topics) { DATA.topics = topics; $("#topics").innerHTML = renderTopics(topics); }
    }
  });
  app.addEventListener("submit", async (e) => {
    if (e.target.id !== "add-topic") return;
    e.preventDefault();
    const f = e.target;
    const btn = f.querySelector("button");
    btn.textContent = "Searching…";
    btn.disabled = true;
    if (STATIC) {
      const name = f.name.value.trim(), query = f.query.value.trim();
      saveMine(loadMine().filter((t) => t.name !== name).concat([{ name, query }]));
      await renderTopicList();
      f.reset();
      btn.textContent = "Track";
      btn.disabled = false;
      return;
    }
    const topics = await post({ action: "add", name: f.name.value, query: f.query.value });
    if (topics) { DATA.topics = topics; $("#topics").innerHTML = renderTopics(topics); f.reset(); }
    btn.textContent = "Track";
    btn.disabled = false;
  });
  async function post(body) {
    try {
      const r = await fetch("api/topics", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      return r.ok ? r.json() : null;
    } catch { return null; }
  }

  // ------------------------------------------------------------ data loading
  async function loadNews(refresh = false) {
    try {
      const r = await fetch(STATIC ? `data/news.json?t=${Date.now()}` : `api/news${refresh ? "?refresh=1" : ""}`);
      const j = STATIC ? { data: await r.json(), refreshing: false } : await r.json();
      $("#refresh").classList.toggle("busy", j.refreshing || refresh);
      if (j.data && j.data.generated !== lastGenerated) {
        lastGenerated = j.data.generated;
        const y = window.scrollY;
        render(j.data);
        window.scrollTo(0, y);
      }
      if (!STATIC && (j.refreshing || !j.data || refresh)) setTimeout(() => loadNews(), 3000);
    } catch {
      $("#updated").textContent = "Can’t reach the Wallflower server — is it running?";
      setTimeout(() => loadNews(), 10000);
    }
  }

  async function loadMarkets() {
    try {
      const j = await (await fetch(STATIC ? `data/markets.json?t=${Date.now()}` : "api/markets")).json();
      if (!j.quotes || !j.quotes.length) return;
      MKT = j;
      renderTicker();
      renderMarkets();
    } catch { /* keep the last data */ }
  }

  $("#today-date").textContent = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  $("#refresh").addEventListener("click", () => (STATIC ? checkForUpdate() : loadNews(true)));

  // Public site: there's no server to rebuild on demand, so Refresh fetches the newest published edition.
  async function checkForUpdate() {
    const btn = $("#refresh");
    btn.classList.add("busy");
    const before = lastGenerated;
    await Promise.all([loadNews(), loadMarkets()]);
    btn.classList.remove("busy");
    btn.textContent = lastGenerated !== before ? "✓ Updated" : "✓ Up to date";
    setTimeout(() => (btn.textContent = "↻ Refresh"), 2500);
  }
  if (STATIC) document.body.classList.add("static");
  loadNews();
  loadMarkets();
  setInterval(loadNews, 5 * 60 * 1000);
  setInterval(loadMarkets, 60 * 1000);
  setInterval(updateStamp, 30 * 1000);
})();
