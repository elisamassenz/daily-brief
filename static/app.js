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
  const plural = (n, w) => `${n} ${n === 1 ? w : /[^aeiou]y$/.test(w) ? w.slice(0, -1) + "ies" : w + "s"}`;

  function sectionHead(num, eyebrow, title, dek, aside = "") {
    return `<header class="sec-head">
      ${num ? `<div class="sec-num">${num}</div>` : ""}
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
  // show: outlets listed up front; phoneShow: fewer on phones (the lead story lists all of them on bigger screens)
  function coverage(angles, show, phoneShow = show) {
    const items = angles.map((a, i) => `
      <li class="angle ${i >= phoneShow && i < show ? "m-extra" : ""}" ${i >= show ? "hidden data-more" : ""}>
        ${pubtag(a.pub)}
        <a class="t" ${ext(a.link)}>${esc(a.title)}</a>
      </li>`).join("");
    const more = angles.length > show
      ? `<button class="more-btn" data-expand>+ ${plural(angles.length - show, "more outlet")}</button>`
      : angles.length > phoneShow ? `<button class="more-btn m-only" data-expand>+ ${plural(angles.length - phoneShow, "more outlet")}</button>` : "";
    return `<div class="coverage">
      <div class="coverage-label">How it’s covered</div>
      <ul class="angles">${items}</ul>${more}
    </div>`;
  }

  // the big headline is one outlet's own (the one closest to everyone's coverage): credit it, and leave it out of the list below
  const leadAngle = (s) => s.angles.find((x) => x.title === s.headline);
  const leadLink = (s) => (leadAngle(s) || s.angles[0] || {}).link;
  const credit = (s) => { const a = leadAngle(s); return a ? `<div class="hl-credit">${logo(a.pub)}<span>Headline from ${esc(SRC[a.pub]?.name || a.pub)}</span></div>` : ""; };
  const others = (s) => s.angles.filter((x) => x !== leadAngle(s));
  const storyEyebrow = (s, n) => `<div class="eyebrow"><span class="${n === 1 ? "acc" : "num"}">${n === 1 ? "Top story" : n}</span> · ${s.pub_count} publications</div>`;
  const meta = (s) => `<div class="story-meta">${stack(s.angles.map((a) => a.pub))}</div>`;

  function renderTrending(stories) {
    if (!stories.length) return `<p class="collecting">No single story is being covered by three or more publications right now.</p>`;
    const [lead, ...rest] = stories;
    const top = rest.slice(0, 6);
    return `
    <article class="story story-lead">
      ${lead.image ? `<a class="lead-img" ${ext(leadLink(lead))}>${image(lead.image)}</a>` : ""}
      ${storyEyebrow(lead, 1)}
      <h3><a class="hl" ${ext(leadLink(lead))}>${esc(lead.headline)}</a></h3>
      ${credit(lead)}
      ${lead.summary ? `<p class="summary">${esc(lead.summary)}</p><button type="button" class="read-more" data-read-more hidden>Read more</button>` : ""}
      ${meta(lead)}
      ${coverage(others(lead), others(lead).length, 5)}
    </article>
    <div class="story-grid">${top.map((s, i) => `
      <article class="story card ${i >= 2 ? "extra" : ""}">
        <div class="card-top ${s.image ? "" : "no-thumb"}">
          <div>
            <h3><a class="hl" ${ext(leadLink(s))}>${esc(s.headline)}</a></h3>
            ${credit(s)}
          </div>
          ${s.image ? `<a class="thumb" ${ext(leadLink(s))}>${image(s.image)}</a>` : ""}
        </div>
        ${coverage(others(s), 3)}
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

  // which trading session the numbers are from, e.g. "Closed · as of Friday, Oct 30 close"
  function sessionLabel() {
    const st = marketStateLabel();
    const t = quote("^GSPC")?.time;
    if (!t) return st;
    const day = new Date(t * 1000).toLocaleDateString("en-US", { timeZone: "America/New_York", weekday: "long", month: "short", day: "numeric" });
    if (st === "Open") return `Open · ${day} session`;
    return `${st || "Closed"} · as of ${day} close`;
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
      $("#markets .sec-dek").innerHTML = `${v.dek}${sessionLabel() ? `<span class="session">${esc(sessionLabel())}</span>` : ""}`;
      $("#markets").dataset.level = v.level;
    }
    const cards = (MKT.quotes || []).filter((m) => m.group === "index");
    const other = (MKT.quotes || []).filter((m) => m.group === "other");
    const watch = (MKT.quotes || []).filter((m) => m.group === "watch");
    const chip = (m) => `<span class="chip">${esc(m.name)} <b class="${dir(m.pct)}">${pct(m.pct)}</b></span>`;
    // each label stays on a line with its first pill (the shortest one, so it fits beside it)
    const chips = (label, list, style = "", shortestFirst = false) => {
      const first = shortestFirst ? list.reduce((a, b) => (b.name.length < a.name.length ? b : a), list[0]) : list[0];
      const more = list.filter((m) => m !== first);
      return first ? `<span class="chip-lead"${style}><span class="kicker">${label}</span>${chip(first)}</span>${more.map(chip).join("")}` : "";
    };
    const mv = MKT.movers || {};
    el.innerHTML = `
      <div class="index-cards">${cards.map((m) => `
        <div class="index-card">
          <div class="ic-name">${esc(m.name)}</div>
          <div class="ic-price">${fmt(m.price, m.symbol)}</div>
          <div class="ic-ch ${dir(m.pct)}">${pct(m.pct)}</div>
          ${lineChart(m)}
          ${m.spark?.length > 1 ? `<div class="ic-range" title="Dashed line: the previous close">${marketStateLabel() === "Open" ? "Today" : "Last session"}</div>` : ""}
        </div>`).join("")}
      </div>
      <div class="watch">
        ${chips("Big tech", watch)}
        ${chips("Other", other, ' style="margin-left:14px"', true)}
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
    const cards = rising.topics.length ? rising.topics.map((t, i) => {
      const recent = Math.min(7, Math.max(1, Math.floor(t.series.length / 3)));
      const recentFrom = t.series.length - recent;
      // growth (server.rising_topics): its share of all saved headlines in the recent days ÷ its share in the days before
      const why = `Over the last ${plural(recent, "day")}, “${esc(t.label)}” turned up in ${t.growth}× as large a share of all the headlines we save as it did in the days before that (the lighter bars). A share, not a count, so a busy news day doesn’t inflate it.`;
      return { label: t.label, pubs: t.pubs, examples: t.examples,
        stat: `<span class="up">▲ ${t.growth}× earlier share</span>
          <button type="button" class="info-btn" data-info aria-expanded="false" aria-controls="why-${i}" aria-label="What does ${t.growth}× earlier share mean?">i</button>`,
        why: `<p class="info-pop" id="why-${i}" hidden>${why}</p>`,
        chart: bars(t.series, [t.days[0].slice(5), "today"], recentFrom, (v, i) => `${t.days[i]}: ${plural(v, "article")}`) };
    }) : (rising.leaders || []).map((t) => ({ label: t.label, pubs: t.pubs, examples: t.examples, stat: `${t.pubs.length} publications`, chart: "" }));
    if (!cards.length) return `<div class="collecting">Fills in after a week of saved headlines.</div>`;
    return `<div class="longview">${cards.map((c, i) => `
      <div class="topic ${i >= 4 ? "extra" : ""}">
        <div>
          <h4>${esc(c.label)}</h4>
          <div class="stat">${stack(c.pubs, 8)} ${c.stat}</div>
          ${c.why || ""}
        </div>
        <div>${c.chart}</div>
        <ul class="ex">${c.examples.slice(0, 4).map((e) => `
          <li>${logo(e.pub)}<a ${ext(e.link)}>${esc(e.title)}</a><span class="when">${esc(e.day.slice(5))}</span></li>`).join("")}
        </ul>
      </div>`).join("")}</div>
      ${cards.length > 4 ? `<button class="show-more lv-more" data-show-more>Show ${plural(cards.length - 4, "more story")}</button>` : ""}`;
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
    if (!FOLLOW.query && tries.length) FOLLOW.query = tries[0];   // land on an example stack, so the section shows what it does
    const chips = FOLLOW.list.length
      ? FOLLOW.list.map((q) => `<button type="button" class="chip ${q === FOLLOW.query ? "on" : ""}" data-follow="${esc(q)}">${esc(q)}</button>`).join("")
      : tries.map((q) => `<button type="button" class="chip ${q === FOLLOW.query ? "on" : ""}" data-follow="${esc(q)}">${esc(q)}</button>`).join("");
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
          <button type="button" class="fpub-all ${FOLLOW.off.size ? "" : "on"}" data-fpub-all title="${FOLLOW.off.size ? "Show all publications" : "Hide all publications"}"><svg viewBox="0 0 24 24"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg></button>
        </div>
      </div>
      <div class="issues" tabindex="0" aria-label="Back issues: use the arrow keys to flip">
        <div class="issue-stack">${covers.length ? "" : `<div class="follow-note issues-empty">Pick a publication above to see its issues.</div>`}${covers.map((c, i) => `
          <a class="cover" data-ci="${i}" draggable="false" ${ext(c.link)}>
            <div class="cover-body">
              <h4>${esc(c.title)}</h4>
              <div class="cover-credit">${logo(c.pub)}<span>${esc(SRC[c.pub]?.name || c.pub)}${c.n > 1 ? ` · 1 of ${c.n} headlines that day` : ""}</span></div>
              <div class="cover-issue">${esc(dayLabel(arc.days[c.di], { weekday: "long", month: "long", day: "numeric" }))}</div>
            </div>
          </a>`).join("")}
        </div>
      </div>
      <div class="follow-chart">
        <div class="bars">${counts.slice(from).map((c, k) => `
          <button type="button" class="b ${c ? "" : "zero"}" data-fday="${from + k}" style="height:${Math.max(3, (c / max) * 100)}%" data-tip="${esc(dayLabel(arc.days[from + k]))}: ${plural(c, "headline")}"></button>`).join("")}
        </div>
        <div class="bars-axis"><span>${esc(dayLabel(arc.days[from], { month: "short", day: "numeric" }))}</span><span>today</span></div>
      </div>
      <div class="issue-nav">
        <button type="button" class="car-btn" data-car="-1" aria-label="Older issue">←</button>
        <button type="button" class="car-btn" data-car="1" aria-label="Newer issue">→</button>
      </div>`;
    stackCovers();
    const st = el.querySelector(".issues");
    // drag (mouse or finger) and sideways trackpad scrolling move the stack continuously; letting go settles on the nearest issue
    const px = () => (window.innerWidth < 620 ? 60 : 130);   // pointer travel per issue
    let drag = null, settle;
    const live = (on) => st.classList.toggle("live", on);   // no easing while following the pointer
    st.addEventListener("pointerdown", (e) => {
      if (e.button) return;
      drag = { x: e.clientX, pos: FOLLOW.focus, moved: false, id: e.pointerId, t: e.timeStamp, v: 0, lx: e.clientX };
    });
    st.addEventListener("pointermove", (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x;
      if (!drag.moved && Math.abs(dx) < 6) return;
      if (!drag.moved) { drag.moved = true; st.setPointerCapture(e.pointerId); live(true); }
      const dt = Math.max(1, e.timeStamp - drag.t);
      drag.v = (e.clientX - drag.lx) / dt; drag.lx = e.clientX; drag.t = e.timeStamp;
      flip(0, drag.pos - dx / px(), true);
    });
    const end = () => {
      if (!drag) return;
      if (drag.moved) {
        st.dataset.swiped = "1";
        live(false);
        flip(0, Math.round(FOLLOW.focus - Math.max(-3, Math.min(3, drag.v * 2.5))));   // a quick flick carries up to 3 issues further
      }
      drag = null;
    };
    st.addEventListener("pointerup", end);
    st.addEventListener("pointercancel", end);
    st.addEventListener("click", (e) => {   // a drag that ends on a cover shouldn't open it
      if (st.dataset.swiped) { e.preventDefault(); e.stopPropagation(); delete st.dataset.swiped; }
    }, true);
    st.addEventListener("wheel", (e) => {
      if (Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return;   // vertical scrolling still scrolls the page
      e.preventDefault();
      live(true);
      flip(0, FOLLOW.focus + e.deltaX / px(), true);
      clearTimeout(settle);
      settle = setTimeout(() => { live(false); flip(0, Math.round(FOLLOW.focus)); }, 140);
    }, { passive: false });
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

  // the stack: the issue in focus sits on top, full size; older and newer ones tuck in behind it.
  // FOLLOW.focus can sit between two issues while dragging, so every value here changes smoothly with it.
  function stackCovers() {
    const narrow = window.innerWidth < 620;
    const step = narrow ? 34 : 120, gap = narrow ? 26 : 70, far = narrow ? 3 : 4;
    const near = Math.round(FOLLOW.focus);
    document.querySelectorAll(".cover").forEach((c) => {
      const d = Number(c.dataset.ci) - FOLLOW.focus, a = Math.abs(d);
      const scale = a < 1 ? 1 - a * .16 : Math.max(.6, .84 - (a - 1) * .08);
      c.style.transform = `translateX(calc(-50% + ${d * step + Math.max(-1, Math.min(1, d)) * gap}px)) scale(${scale})`;
      c.style.zIndex = 1000 - Math.round(a * 10);
      c.style.opacity = Math.max(0, Math.min(1 - a * .12, far + 1 - a));
      c.classList.toggle("on", Number(c.dataset.ci) === near);
      c.tabIndex = Number(c.dataset.ci) === near ? 0 : -1;
    });
    const cur = FOLLOW.covers[near];
    document.querySelectorAll(".follow-chart .b").forEach((b) => b.classList.toggle("recent", Number(b.dataset.fday) === cur?.di));
    document.querySelectorAll('.issue-nav [data-car]').forEach((b) => {
      b.disabled = b.dataset.car === "1" ? near >= FOLLOW.covers.length - 1 : near <= 0;
    });
  }
  function flip(by, to, free = false) {
    const n = FOLLOW.covers.length;
    const pos = to ?? Math.round(FOLLOW.focus) + by;
    FOLLOW.focus = free ? Math.max(-.4, Math.min(n - .6, pos)) : Math.max(0, Math.min(n - 1, pos));
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
  const FRONT_KEY = "wallflower.front";
  const FRONT_TABS = { "Ideas & Analysis": "Ideas", "Business & Markets": "Business", "Technology": "Tech" };
  let FRONT = (() => { try { return localStorage.getItem(FRONT_KEY); } catch { return null; } })();
  function frontTabs(sections) {
    if (FRONT !== "all" && !sections.includes(FRONT)) FRONT = sections[0];
    return `<div class="front-tabs" role="tablist" aria-label="Front pages by category">${[...sections, "all"].map((sec) => `
      <button type="button" role="tab" data-front="${esc(sec)}">${esc(sec === "all" ? "All" : FRONT_TABS[sec] || sec)}</button>`).join("")}
    </div>`;
  }
  function applyFront() {
    $("#fronts").dataset.front = FRONT;
    document.querySelectorAll("[data-front]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.front === FRONT)));
    document.querySelectorAll(".pub-section").forEach((s) => s.classList.toggle("off", FRONT !== "all" && s.dataset.sec !== FRONT));
  }

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

  // Home Screen how-to: hidden once someone says they've added it, or after they open the Home Screen app.
  // (On Android the app shares this site's storage, so opening it once is remembered in the browser too;
  // on iPhone the Home Screen app keeps separate storage, so the "already have it" button covers that.)
  const INSTALLED_KEY = "wallflower.installed";
  const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const installed = () => { try { return standalone || localStorage.getItem(INSTALLED_KEY) === "1"; } catch { return standalone; } };
  if (standalone) try { localStorage.setItem(INSTALLED_KEY, "1"); } catch { /* private mode */ }

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

  // ------------------------------------------------------------ about
  const reportHref = (email) => `mailto:${email}?subject=${encodeURIComponent("Wallflower: problem report")}&body=${encodeURIComponent("What looks wrong (a headline, a link, two stories grouped together, a market number)?\n\n")}`;
  function renderAbout(data) {
    return `<section id="about" class="sec about">
      ${sectionHead("", "About", "How Wallflower works")}
      <div class="about-grid">
        <div><h4>An independent news page</h4><p>${esc(data.title)} doesn’t write or edit the news, and isn’t affiliated with any of the publications. It reads the public feeds of ${data.sources.length} newsrooms every half hour.</p></div>
        <div><h4>Ranked by coverage</h4><p>Stories are grouped automatically by matching headlines across outlets, and ranked by how many newsrooms are covering them. No one picks them by hand, so now and then a grouping can be off.</p></div>
        <div><h4>Their words, their links</h4><p>Every headline appears exactly as the outlet wrote it, credited, and links to the original article. Read the full story at the source.</p></div>
        <div><h4>Markets</h4><p>Prices come from Yahoo Finance and may be delayed. The date shows which trading session they’re from.</p></div>
      </div>
      ${data.report_email ? `<p class="about-report">Spot a wrong grouping, a broken link or a headline that looks off? <a href="${esc(reportHref(data.report_email))}">Report a problem</a></p>` : ""}
    </section>`;
  }

  // ------------------------------------------------------------ page
  function render(data) {
    DATA = data;
    if (data.title) { document.title = data.title; $(".masthead-title").textContent = data.title; }
    const ig = $("#follow-ig");
    ig.hidden = !data.instagram_url;
    if (data.instagram_url) ig.href = data.instagram_url;
    const navSupport = $("#nav-support");
    navSupport.hidden = !data.support_url;
    navSupport.lastChild.textContent = `Support ${data.title || ""}`.trim();
    SRC = Object.fromEntries(data.sources.map((s) => [s.id, s]));
    app.innerHTML = `
      <section id="today" class="sec">
        ${sectionHead("01", "Trending today", "What everyone is covering")}
        ${renderTrending(data.trending)}
      </section>
      ${installed() ? "" : `
      <section id="howto" class="sec">
        ${sectionHead("", "How to", `Add ${esc(data.title || "it")} to your Home Screen`)}
        ${renderHowTo()}
        <button type="button" class="howto-done" data-howto-done>I already have it on my Home Screen</button>
      </section>`}

      <section id="fronts" class="sec">
        <img class="peek peek-1" src="stem-b.png" alt="" aria-hidden="true">
        ${sectionHead("02", "Front pages", `<span class="line">Every publication’s</span> top two`)}
        ${frontTabs(data.sections)}
        ${data.sections.map((sec) => `
          <div class="pub-section" data-sec="${esc(sec)}">
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
        ${sectionHead("04", "Trending over the weeks", "Back Issues", "Pick a topic and flip through four weeks of its cover stories.")}
        ${renderFollow()}
        ${renderRising(data.rising)}
      </section>

      ${renderSupport(data)}
      ${renderAbout(data)}`;
    const rep = $("#foot-report");
    rep.hidden = !data.report_email;
    if (data.report_email) rep.querySelector("a").href = reportHref(data.report_email);
    applyFront();
    renderMarkets();
    paintFollow();
    updateStamp();
    queueFit();
    document.querySelectorAll("section.sec").forEach((s) => navObserver.observe(s));
  }

  function fitFills() {
    document.querySelectorAll(".pad-tile").forEach((t) => t.remove());
    document.querySelectorAll(".summary:not(.open)").forEach((p) => {
      const btn = p.nextElementSibling;
      if (btn?.matches("[data-read-more]")) btn.hidden = p.scrollHeight <= p.clientHeight + 1;
    });
  }
  let fitTimer;
  const queueFit = () => { clearTimeout(fitTimer); fitTimer = setTimeout(fitFills, 120); };
  document.addEventListener("load", (e) => { if (e.target.tagName === "IMG") queueFit(); }, true);
  window.addEventListener("resize", queueFit);
  document.addEventListener("error", (e) => { if (e.target.tagName === "IMG") queueFit(); }, true);

  // a manual Refresh that finds nothing newer still counts as "updated": the page is as current as it can be
  let checkedAt = null;
  function updateStamp() {
    if (!DATA) return;
    const t = checkedAt && checkedAt > new Date(DATA.generated) ? checkedAt.toISOString() : DATA.generated;
    $("#updated").textContent = `Updated ${ago(t)}`;
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
    if (e.target.closest("[data-howto-done]")) {
      try { localStorage.setItem(INSTALLED_KEY, "1"); } catch { /* private mode */ }
      $("#howto")?.remove();
      return;
    }
    const rm = e.target.closest("[data-read-more]");
    if (rm) { rm.previousElementSibling.classList.add("open"); rm.remove(); return; }
    const ft = e.target.closest("[data-front]");
    if (ft) {
      FRONT = ft.dataset.front;
      try { localStorage.setItem(FRONT_KEY, FRONT); } catch { /* private mode */ }
      applyFront();
      return;
    }
    const ib = e.target.closest("[data-info]");
    if (ib) {
      const pop = document.getElementById(ib.getAttribute("aria-controls"));
      pop.hidden = !pop.hidden;
      ib.setAttribute("aria-expanded", String(!pop.hidden));
      return;
    }
    const fq = e.target.closest("[data-follow]");
    if (fq) { follow(fq.dataset.follow); return; }
    if (e.target.closest("[data-fpub-all]")) {   // all on → all off; otherwise all back on
      if (FOLLOW.off.size) FOLLOW.off.clear();
      else document.querySelectorAll("[data-fpub]").forEach((b) => FOLLOW.off.add(b.dataset.fpub));
      paintFollow();
      return;
    }
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
      ex.previousElementSibling.querySelectorAll("[data-more], .m-extra").forEach((li) => { li.hidden = false; li.classList.remove("m-extra"); });
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
  // "Share Wallflower": the phone's share sheet where there is one, otherwise copy the link
  $("#share").addEventListener("click", async (e) => {
    const url = "https://wallflower.news/";
    try {
      if (navigator.share) { await navigator.share({ title: "Wallflower", text: "The day’s biggest stories from 24 newsrooms, side by side.", url }); return; }
      await navigator.clipboard.writeText(url);
      e.target.textContent = "✓ Link copied";
      setTimeout(() => (e.target.textContent = "Share Wallflower"), 2200);
    } catch { /* share sheet dismissed */ }
  });

  // Public site: there's no server to rebuild on demand, so Refresh fetches the newest published edition.
  async function checkForUpdate() {
    const btn = $("#refresh");
    btn.classList.add("busy");
    const before = lastGenerated;
    await Promise.all([loadNews(), loadMarkets()]);
    btn.classList.remove("busy");
    btn.textContent = lastGenerated !== before ? "✓ Updated" : "✓ Up to date";
    checkedAt = new Date();
    updateStamp();
    setTimeout(() => (btn.textContent = "↻ Refresh"), 2500);
  }
  if (STATIC) document.body.classList.add("static");
  loadNews();
  loadMarkets();
  setInterval(loadNews, 5 * 60 * 1000);
  setInterval(loadMarkets, 60 * 1000);
  setInterval(updateStamp, 30 * 1000);
})();
