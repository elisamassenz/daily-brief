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

  // one grid of stories that keep coming back: rising names and phrases across the saved headlines
  // (needs a week of history); until then, the most widely covered this month
  function renderRising(rising) {
    const cards = rising.topics.length ? rising.topics.map((t) => {
      const recentFrom = t.series.length - Math.min(7, Math.max(1, Math.floor(t.series.length / 3)));
      return { label: t.label, pubs: t.pubs, examples: t.examples,
        stat: `<span class="up">▲ ${t.growth}× earlier share</span>`,
        chart: bars(t.series, [t.days[0].slice(5), "today"], recentFrom, (v, i) => `${t.days[i]}: ${plural(v, "article")}`) };
    }) : (rising.leaders || []).map((t) => ({ label: t.label, pubs: t.pubs, examples: t.examples, stat: `${t.pubs.length} publications`, chart: "" }));
    if (!cards.length) return `<div class="collecting">Fills in after a week of saved headlines.</div>`;
    return `<div class="longview">${cards.map((c) => `
      <div class="topic">
        <div>
          <h4>${esc(c.label)}</h4>
          <div class="stat">${stack(c.pubs, 8)} ${c.stat}</div>
        </div>
        <div>${c.chart}</div>
        <ul class="ex">${c.examples.slice(0, 4).map((e) => `
          <li>${logo(e.pub)}<a ${ext(e.link)}>${esc(e.title)}</a><span class="when">${esc(e.day.slice(5))}</span></li>`).join("")}
        </ul>
      </div>`).join("")}</div>`;
  }

  // ------------------------------------------------------------ back issues (topic search)
  // Searches the last 4 weeks of saved headlines (data/archive.json, built by build.py) in the browser.
  // Searches last only for this visit: nothing is saved.
  const FOLLOW = { list: [], query: "", off: new Set(), covers: [], focus: 0 };
  let archivePromise = null;
  const archive = () => (archivePromise = archivePromise ||
    fetch(STATIC ? `data/archive.json?t=${encodeURIComponent(DATA?.generated || "")}` : "api/archive")
      .then((r) => r.json()).catch(() => (archivePromise = null)));

  // "pope leo": every word must appear (as the start of a word); "ozempic, wegovy" or "ozempic OR wegovy": either may match
  function matcher(query) {
    const tests = query.split(/\s+OR\s+|,/i).map((x) => x.trim()).filter(Boolean).map((alt) => {
      const quoted = alt.match(/^"(.+)"$/);
      const words = quoted ? [quoted[1]] : alt.replace(/[()"]/g, " ").split(/\s+/).filter((w) => w.length > 1);
      const res = words.map((w) => new RegExp(`(^|[^\\p{L}\\p{N}])${w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "iu"));
      return (text) => res.length > 0 && res.every((re) => re.test(text));
    });
    return (text) => tests.some((t) => t(text));
  }
  const dayLabel = (d, opts = { weekday: "short", month: "short", day: "numeric" }) =>
    new Date(`${d}T12:00:00`).toLocaleDateString("en-US", opts);

  function renderFollow() {
    const tries = (DATA?.rising?.topics || DATA?.rising?.leaders || []).slice(0, 4).map((t) => t.label);
    const chips = FOLLOW.list.length
      ? FOLLOW.list.map((q) => `<button type="button" class="chip ${q === FOLLOW.query ? "on" : ""}" data-follow="${esc(q)}">${esc(q)}</button>`).join("")
      : tries.map((q) => `<button type="button" class="chip" data-follow="${esc(q)}">${esc(q)}</button>`).join("");
    return `<div class="follow">
      <form class="follow-search" id="follow-form" role="search">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/></svg>
        <input name="q" placeholder="Pick a topic, e.g. Pope Leo" maxlength="80" autocomplete="off" value="${esc(FOLLOW.query)}" aria-label="Pick a topic">
        <button type="submit">Search</button>
      </form>
      <div class="follow-chips">${chips ? `<span class="kicker">${FOLLOW.list.length ? "This visit" : "Try"}</span>${chips}` : ""}</div>
      <div id="follow-results"></div>
    </div>`;
  }

  async function paintFollow() {
    const el = $("#follow-results");
    if (!el || !FOLLOW.query) return;
    el.innerHTML = `<div class="follow-note">Searching 4 weeks of headlines…</div>`;
    const arc = await archive();
    if (!arc) { el.innerHTML = `<div class="follow-note">Couldn’t load the saved headlines. Try again in a moment.</div>`; return; }
    const test = matcher(FOLLOW.query);
    const seen = new Set();
    const all = arc.items.filter(([, , title, link]) => {
      if (seen.has(link) || !test(title)) return false;
      seen.add(link);
      return true;
    }).map(([di, pi, title, link, img]) => ({ di, pub: arc.pubs[pi], title, link, img }));
    if (!all.length) {
      el.innerHTML = `<div class="follow-note">No headlines about “${esc(FOLLOW.query)}” in the last 4 weeks.</div>`;
      return;
    }
    const order = (DATA?.sources || []).map((x) => x.id);
    const pubs = [...new Set(all.map((h) => h.pub))].sort((a, b) => order.indexOf(a) - order.indexOf(b));
    const hits = all.filter((h) => !FOLLOW.off.has(h.pub));
    const covers = coverStories(hits);   // one per day, oldest → newest
    FOLLOW.covers = covers;
    FOLLOW.focus = covers.length - 1;    // open on the latest issue
    const counts = arc.days.map((_, i) => hits.filter((h) => h.di === i).length);
    const first = counts.findIndex((c) => c > 0);
    const from = Math.max(0, Math.min(first < 0 ? 0 : first, arc.days.length - 14));  // at least two weeks of bars
    const max = Math.max(1, ...counts);
    el.innerHTML = `
      <div class="follow-head">
        <div>
          <h3>${esc(FOLLOW.query)}</h3>
          <p class="stat">${plural(covers.length, "issue")} · ${plural(all.length, "headline")} from ${plural(pubs.length, "publication")}</p>
        </div>
        <div class="follow-pubs" aria-label="Filter by publication">${pubs.map((p) => `
          <button type="button" class="fpub ${FOLLOW.off.has(p) ? "off" : ""}" data-fpub="${esc(p)}" title="${esc(SRC[p]?.name || p)}">${logo(p)}</button>`).join("")}
        </div>
      </div>
      <div class="issues" tabindex="0" aria-label="Back issues: use the arrow keys to flip">
        <button type="button" class="car-btn" data-car="-1" aria-label="Older issue">←</button>
        <div class="issue-stack">${covers.map((c, i) => `
          <a class="cover" data-ci="${i}" draggable="false" ${ext(c.link)}>
            <div class="cover-body">
              <h4>${esc(c.title)}</h4>
              <div class="cover-credit">${logo(c.pub)}<span>${esc(SRC[c.pub]?.name || c.pub)}${c.n > 1 ? ` · 1 of ${c.n} headlines that day` : ""}</span></div>
              <div class="cover-issue">${esc(dayLabel(arc.days[c.di], { weekday: "long", month: "long", day: "numeric" }))}</div>
            </div>
          </a>`).join("")}
        </div>
        <button type="button" class="car-btn" data-car="1" aria-label="Newer issue">→</button>
      </div>
      <div class="follow-chart">
        <div class="bars">${counts.slice(from).map((c, k) => `
          <button type="button" class="b ${c ? "" : "zero"}" data-fday="${from + k}" style="height:${Math.max(3, (c / max) * 100)}%" data-tip="${esc(dayLabel(arc.days[from + k]))}: ${plural(c, "headline")}"></button>`).join("")}
        </div>
        <div class="bars-axis"><span>${esc(dayLabel(arc.days[from], { month: "short", day: "numeric" }))}</span><span>today</span></div>
      </div>`;
    stackCovers();
    const st = el.querySelector(".issues");
    let x0 = null;   // swipe to flip
    st.addEventListener("pointerdown", (e) => { x0 = e.clientX; });
    st.addEventListener("pointerup", (e) => {
      if (x0 !== null && Math.abs(e.clientX - x0) > 40) { flip(e.clientX < x0 ? 1 : -1); st.dataset.swiped = "1"; }
      x0 = null;
    });
    st.addEventListener("click", (e) => {   // a swipe that ends on a cover shouldn't open it
      if (st.dataset.swiped) { e.preventDefault(); e.stopPropagation(); delete st.dataset.swiped; }
    }, true);
    st.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); flip(e.key === "ArrowRight" ? 1 : -1); }
    });
  }

  // each day's cover story: the matching headline that shares the most words with that day's other
  // matching headlines (the angle most outlets ran with)
  function coverStories(hits) {
    const skip = new Set(FOLLOW.query.toLowerCase().split(/\W+/u));
    const words = (t) => new Set(t.toLowerCase().split(/[^\p{L}\p{N}]+/u).filter((w) => w.length > 3 && !skip.has(w)));
    const byDay = new Map();
    for (const h of hits) byDay.set(h.di, [...(byDay.get(h.di) || []), h]);
    return [...byDay.keys()].sort((a, b) => a - b).map((di) => {
      const day = byDay.get(di).map((h) => ({ ...h, w: words(h.title) }));
      let best = null, top = -1;
      for (const h of day) {
        let score = 0;
        for (const o of day) if (o !== h) for (const w of h.w) if (o.w.has(w)) score += 1;
        if (score > top) { top = score; best = h; }
      }
      return { ...best, n: day.length };
    });
  }

  // the stack: the issue in focus sits on top, full size; older and newer ones tuck in behind it
  function stackCovers() {
    const narrow = window.innerWidth < 620;
    const step = narrow ? 34 : 120;
    document.querySelectorAll(".cover").forEach((c) => {
      const d = Number(c.dataset.ci) - FOLLOW.focus, a = Math.abs(d);
      c.style.transform = `translateX(calc(-50% + ${d * step + Math.sign(d) * (narrow ? 26 : 70)}px)) scale(${a ? Math.max(.6, .84 - (a - 1) * .08) : 1})`;
      c.style.zIndex = 100 - a;
      c.style.opacity = a > (narrow ? 3 : 4) ? 0 : a ? 1 - a * .12 : 1;
      c.classList.toggle("on", !a);
      c.tabIndex = a ? -1 : 0;
    });
    const cur = FOLLOW.covers[FOLLOW.focus];
    document.querySelectorAll(".follow-chart .b").forEach((b) => b.classList.toggle("recent", Number(b.dataset.fday) === cur?.di));
    document.querySelectorAll('.issues [data-car]').forEach((b) => {
      b.disabled = b.dataset.car === "1" ? FOLLOW.focus >= FOLLOW.covers.length - 1 : FOLLOW.focus <= 0;
    });
  }
  function flip(by, to) {
    const n = FOLLOW.covers.length;
    FOLLOW.focus = Math.max(0, Math.min(n - 1, to ?? FOLLOW.focus + by));
    stackCovers();
  }
  window.addEventListener("resize", () => { if (FOLLOW.covers.length) stackCovers(); });

  function follow(q) {
    q = q.trim();
    if (!q) return;
    FOLLOW.query = q;
    FOLLOW.off.clear();
    FOLLOW.list = [q, ...FOLLOW.list.filter((x) => x.toLowerCase() !== q.toLowerCase())].slice(0, 8);
    const wrap = $(".follow");
    if (wrap) wrap.outerHTML = renderFollow();
    paintFollow();
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
    const LOGO = {
      apple: '<svg viewBox="0 0 24 24"><path d="M12.152 6.896c-.948 0-2.415-1.078-3.96-1.04-2.04.027-3.91 1.183-4.961 3.014-2.117 3.675-.546 9.103 1.519 12.09 1.013 1.454 2.208 3.09 3.792 3.039 1.52-.065 2.09-.987 3.935-.987 1.831 0 2.35.987 3.96.948 1.637-.026 2.676-1.48 3.676-2.948 1.156-1.688 1.636-3.325 1.662-3.415-.039-.013-3.182-1.221-3.22-4.857-.026-3.04 2.48-4.494 2.597-4.559-1.429-2.09-3.623-2.324-4.39-2.376-2-.156-3.675 1.09-4.61 1.09zM15.53 3.83c.843-1.012 1.4-2.427 1.245-3.83-1.207.052-2.662.805-3.532 1.818-.78.896-1.454 2.338-1.273 3.714 1.338.104 2.715-.688 3.559-1.701"/></svg>',
      chrome: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="10.2"/><circle cx="12" cy="12" r="4"/><path d="M12 8h9.2M8.54 14 3.94 6.03M15.46 14l-4.6 7.97"/></svg>',
    };
    const platform = (name, logo, steps) => `
      <div class="platform"><p class="platform-logo" role="img" aria-label="${name}" title="${name}">${LOGO[logo]}</p><ol class="steps">${steps}</ol></div>`;
    return `<div class="howto-card howto-install">
      ${platform("iPhone · Safari", "apple",
        step("share", "Tap <b>Share</b> at the bottom of Safari") + step("plus", "Choose <b>Add to Home Screen</b>, then <b>Add</b>"))}
      ${platform("Android · Chrome", "chrome",
        step("dots", "Tap the <b>⋮</b> menu at the top right") + step("plus", "Choose <b>Add to Home screen</b>"))}
    </div>`;
  }

  function renderSupport(data) {
    if (!data.support_url) return "";
    return `<section id="support" class="sec support">
      <div class="support-card">
        <img class="support-bloom" src="support-bloom.png" alt="" aria-hidden="true">
        <div class="support-copy">
          <p class="support-eyebrow"><span class="pill">♥</span> Keep it growing</p>
          <h3>Help ${esc(data.title)} <em>bloom</em></h3>
          <p>${esc(data.title)} is free, ad-free and made by one person. If it's become part of your morning, a coffee helps keep the news coming.</p>
          <a class="support-btn" ${ext(data.support_url)}><span>Buy me a coffee</span><span aria-hidden="true">→</span></a>
        </div>
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
        <img class="peek peek-1" src="stem-b.png" alt="" aria-hidden="true">
        ${sectionHead("02", "Front pages", "Every publication’s top two")}
        ${data.sections.map((sec) => `
          <div class="pub-section">
            ${subHead(esc(sec))}
            <div class="pubs">${data.sources.filter((s) => s.section === sec).map((s) => renderPub(s, data.headlines[s.id])).join("")}</div>
          </div>`).join("")}
      </section>

      <section id="markets" class="sec">
        <img class="peek peek-2" src="stem-c.png" alt="" aria-hidden="true">
        ${sectionHead("03", "Markets & money", "Markets")}
        <div id="markets-body"></div>
      </section>


      <section id="weeks" class="sec">
        <img class="peek peek-3" src="stem.png" alt="" aria-hidden="true">
        ${sectionHead("04", "Trending over the weeks", "Back Issues", "Pick any topic and get its cover story for each day: the headline the most outlets ran with. Flip back through them like a stack of old magazines.")}
        ${renderFollow()}
        ${renderRising(data.rising)}
      </section>

      <section id="howto" class="sec">
        ${sectionHead("05", "How to", `Add ${esc(data.title || "it")} to your Home Screen`)}
        ${renderHowTo()}
      </section>
      ${renderSupport(data)}`;
    renderMarkets();
    paintFollow();
    updateStamp();
    queueFit();
    document.querySelectorAll("section.sec").forEach((s) => navObserver.observe(s));
  }

  function fitFills() {
    document.querySelectorAll(".pad-tile").forEach((t) => t.remove());
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
    const fq = e.target.closest("[data-follow]");
    if (fq) { follow(fq.dataset.follow); return; }
    const fp = e.target.closest("[data-fpub]");
    if (fp) {
      const p = fp.dataset.fpub;
      FOLLOW.off.has(p) ? FOLLOW.off.delete(p) : FOLLOW.off.add(p);
      paintFollow();
      return;
    }
    const fd = e.target.closest("[data-fday]");
    if (fd) {
      const i = FOLLOW.covers.findIndex((c) => c.di === Number(fd.dataset.fday));
      if (i >= 0) flip(0, i);
      return;
    }
    const cb = e.target.closest("[data-car]");
    if (cb) { flip(Number(cb.dataset.car)); return; }
    const cv = e.target.closest(".cover:not(.on)");
    if (cv) { e.preventDefault(); flip(0, Number(cv.dataset.ci)); return; }   // tap a tucked-in issue to bring it up
    const ex = e.target.closest("[data-expand]");
    if (ex) {
      ex.previousElementSibling.querySelectorAll("[data-more]").forEach((li) => (li.hidden = false));
      ex.remove();
      return;
    }
  });
  app.addEventListener("submit", (e) => {
    if (e.target.id !== "follow-form") return;
    e.preventDefault();
    follow(e.target.q.value);
  });

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
