/* The Singularity Atlas — frontend.
   Polls /api/state, drives the globe.gl globe, panels, brief, radar, archive. */

"use strict";

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

let STATE = null;
let GLOBE_DATA = null;
let QUOTES = [];
let quoteIdx = 0;

/* ---------------- utils ---------------- */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function relTime(iso) {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (isNaN(t)) return "";
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

/* minimal markdown: h1, bold, italic, links, paragraphs */
function md(text) {
  const blocks = String(text || "").split(/\n\s*\n/);
  return blocks.map((b) => {
    let t = esc(b.trim());
    if (!t) return "";
    if (t.startsWith("# ")) return `<h1>${inlineMd(t.slice(2))}</h1>`;
    if (t.startsWith("## ")) return `<h1>${inlineMd(t.slice(3))}</h1>`;
    return `<p>${inlineMd(t)}</p>`;
  }).join("");
}
function inlineMd(t) {
  return t
    .replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*\n]+)\*/g, "<em>$1</em>")
    .replace(/\n/g, " ");
}

/* ---------------- header ---------------- */

function renderClock() {
  const d = new Date();
  $("#clock").textContent = d.toISOString().slice(11, 19);
}
setInterval(renderClock, 1000); renderClock();

function renderQuote() {
  if (!QUOTES.length) return;
  const [q, src] = QUOTES[quoteIdx % QUOTES.length];
  quoteIdx++;
  $("#quote-text").textContent = `“${q}”`;
  $("#quote-src").textContent = src ? `— ${src}` : "";
}
setInterval(renderQuote, 15000);

function renderSI(si) {
  const v = Math.max(0, Math.min(100, si.si ?? 0));
  $("#si-value").textContent = v.toFixed(1);
  const d = si.delta ?? 0;
  const days = STATE?.si_baseline_days ?? 7;
  $("#si-delta").textContent = `${d >= 0 ? "▲" : "▼"} ${Math.abs(d).toFixed(1)} vs ${days}d mean`;
  const arc = $("#si-arc");
  arc.setAttribute("stroke-dashoffset", String(157 * (1 - v / 100)));
  arc.setAttribute("stroke", v < 34 ? "#00e5ff" : v < 67 ? "#ffd600" : "#ff1744");

  const idx = si.epoch?.index ?? 0;
  $$(".epoch-seg").forEach((el) => el.classList.toggle("active", +el.dataset.epoch === idx));
  // marker: interpolate within segment
  const pct = idx === 0 ? v / 34 / 3 : idx === 1 ? (1 + (v - 34) / 33) / 3 : (2 + (v - 67) / 33) / 3;
  $("#epoch-marker").style.left = `${Math.min(99, Math.max(1, pct * 100))}%`;
  $("#epoch-name").textContent = si.epoch?.name ?? "—";
  $("#countdown").textContent = `${(si.countdown?.days ?? 0).toLocaleString()} days to 2045`;
}

function renderSpark(history) {
  const svg = $("#si-spark");
  if (!history || history.length < 2) { svg.innerHTML = ""; return; }
  const W = 800, H = 42;
  const vals = history.map((h) => h.si);
  const min = Math.min(...vals) - 2, max = Math.max(...vals) + 2;
  const pts = vals.map((v, i) =>
    `${(i / (vals.length - 1)) * W},${H - ((v - min) / (max - min)) * (H - 6) - 3}`).join(" ");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.innerHTML =
    `<polyline points="${pts}" fill="none" stroke="#00e5ff" stroke-width="1.2" opacity="0.9"/>` +
    `<circle cx="${W}" cy="${H - ((vals.at(-1) - min) / (max - min)) * (H - 6) - 3}" r="2.5" fill="#00e5ff"/>`;
}

/* ---------------- globe ---------------- */

const KIND_COLOR = { datacenter: "#ff6d00", fab: "#ffd600", lab: "#00e5ff", launch: "#ffffff" };
let world = null;

function initGlobe() {
  world = Globe()($("#globe"))
    .globeImageUrl("//unpkg.com/three-globe/example/img/earth-night.jpg")
    .backgroundColor("rgba(0,0,0,0)")
    .showAtmosphere(true)
    .atmosphereColor("#0a3a4a")
    .atmosphereAltitude(0.18)
    .pointOfView({ lat: 28, lng: -30, altitude: 2.1 })
    .pointsMerge(false)
    .pointLabel((d) => `<div style="font-family:monospace;font-size:11px">${d.tip}</div>`)
    .onPointClick((d) => onGlobePoint(d));

  world.controls().autoRotate = true;
  world.controls().autoRotateSpeed = 0.32;
  world.controls().enableZoom = true;
  // ?demo=1: slightly faster globe + ticker so a short README gif shows motion
  // without looking frantic (production rotate is 0.32; ticker is 120s).
  if (new URLSearchParams(location.search).get("demo") === "1") {
    document.body.classList.add("demo");
    world.controls().autoRotateSpeed = 1.1;
  }

  const resize = () => world.width($("#globe").clientWidth).height($("#globe").clientHeight);
  window.addEventListener("resize", resize);
  setTimeout(resize, 50);
}

function activeLayers() {
  const m = {};
  $$(".layer-toggles input").forEach((i) => { m[i.dataset.layer] = i.checked; });
  return m;
}

function rebuildGlobeLayers() {
  if (!world || !GLOBE_DATA) return;
  const on = activeLayers();
  const pts = [];

  for (const s of GLOBE_DATA.sites || []) {
    if (!on[s.kind]) continue;   // layer names match kinds: datacenter/fab/lab/launch
    pts.push({ lat: s.lat, lon: s.lon, kind: s.kind, color: KIND_COLOR[s.kind] || "#fff",
      r: 0.42, alt: 0.015, tip: `<b>${esc(s.name)}</b><br>${esc(s.note || "")}` });
  }

  if (on.launch) {
    for (const L of GLOBE_DATA.launches || []) {
      const e = L.extra || {};
      if (e.lat == null || e.lon == null) continue;
      pts.push({ lat: e.lat, lon: e.lon, kind: "launch-upcoming", color: "#ffffff", r: 0.45,
        alt: 0.02, pulse: true,
        tip: `<b>${esc(L.title)}</b><br>NET ${esc((L.published_at || "").slice(0, 16).replace("T", " "))} UTC` });
    }
  }

  const rings = [];
  if (on.events) {
    for (const ev of GLOBE_DATA.events || []) {
      if (ev.lat == null || ev.lon == null) continue;
      pts.push({ lat: ev.lat, lon: ev.lon, kind: "event", color: "#00e676", r: 0.28, alt: 0.01,
        tip: `<b>${esc(ev.place)}</b><br>${esc(ev.title)}`, story: ev });
      rings.push({ lat: ev.lat, lon: ev.lon });
    }
  }

  world
    .pointsData(pts)
    .pointLat((d) => d.lat).pointLng((d) => d.lon)
    .pointColor((d) => d.color).pointRadius((d) => d.r).pointAltitude((d) => d.alt)
    .ringsData(rings)
    .ringColor(() => (t) => `rgba(0,230,118,${Math.max(0, 0.8 - t * 0.8)})`)
    .ringMaxRadius(3.2).ringPropagationSpeed(0.9).ringRepeatPeriod(2600);

  if (on.arcs) {
    world
      .arcsData(GLOBE_DATA.arcs || [])
      .arcStartLat((d) => d.from_lat).arcStartLng((d) => d.from_lon)
      .arcEndLat((d) => d.to_lat).arcEndLng((d) => d.to_lon)
      .arcColor(() => ["rgba(213,0,249,0.55)", "rgba(0,229,255,0.35)"])
      .arcStroke(0.55).arcDashLength(0.45).arcDashGap(0.25)
      .arcDashAnimateTime(4200).arcAltitudeAutoScale(0.35)
      .arcLabel((d) => `${esc(d.from_name)} ⇄ ${esc(d.to_name)} · ${d.n} signals`);
  } else {
    world.arcsData([]);
  }

  const gs = $("#globe-stats");
  if (gs && STATE) {
    const g = STATE.graph || {};
    gs.innerHTML =
      `<b>${(g.stories || 0).toLocaleString()}</b> stories · <b>${(g.entities || 0).toLocaleString()}</b> entities<br>` +
      `<b>${(g.edges || 0).toLocaleString()}</b> edges · <b>${(GLOBE_DATA.launches || []).length}</b> launches queued`;
  }
}

function onGlobePoint(d) {
  if (d.story) openStoryDrawer(d.story);
}

$$(".layer-toggles input").forEach((i) => i.addEventListener("change", rebuildGlobeLayers));

/* ---------------- vector panels ---------------- */

function renderVectors() {
  if (!STATE) return;
  const wrap = $("#vector-panels");
  const vecScores = STATE.si?.vectors || {};
  wrap.innerHTML = "";
  for (const [name, meta] of Object.entries(STATE.vectors || {})) {
    const stories = (STATE.signals?.[name]) || [];
    const score = vecScores[name]?.score ?? 0;
    const div = document.createElement("div");
    div.className = "panel vector-panel";
    div.innerHTML =
      `<div class="panel-head">
         <span class="panel-title"><span class="vector-dot" style="color:${meta.color};background:${meta.color}"></span>${esc(meta.label.toUpperCase())}</span>
         <span class="vector-score">${score.toFixed(0)}</span>
       </div>
       <div class="panel-body">${
         stories.slice(0, 4).map((s) =>
           `<div class="story" data-sid="${esc(s.id)}">
              <div class="story-title"><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></div>
              <div class="story-meta">${esc(s.source_label || s.source)} · ${relTime(s.published_at)}</div>
            </div>`).join("") || '<div class="loading">quiet…</div>'
       }</div>`;
    wrap.appendChild(div);
  }
}

/* ---------------- brief ---------------- */

function renderBrief() {
  const b = STATE?.brief;
  if (!b) { $("#brief-body").innerHTML = '<div class="loading">no edition yet — ingest pending</div>'; return; }
  $("#brief-body").innerHTML = md(b.text);
  $("#brief-meta").textContent = `${b.date} · ${b.model === "heuristic" ? "heuristic" : "qwen3 local"}`;
}

/* ---------------- convergence ---------------- */

const VEC_COLORS = {};
function renderConvergence() {
  const rows = STATE?.convergence || [];
  const el = $("#convergence-body");
  if (!rows.length) { el.innerHTML = '<div class="loading">no cross-stream entities</div>'; return; }
  const maxHeat = Math.max(...rows.map((r) => r.heat || 1));
  el.innerHTML = rows.map((r) =>
    `<div class="conv-row" data-ent="${esc(r.name)}">
       <span class="conv-name">${esc(r.name)}</span>
       <span class="conv-heat"><i style="width:${Math.round(100 * (r.heat || 1) / maxHeat)}%"></i></span>
       <span class="conv-vecs">${(r.vecs || []).map((v) =>
         `<span class="conv-chip" title="${esc(v)}" style="background:${VEC_COLORS[v] || "#888"}"></span>`).join("")}</span>
       <span class="conv-count">${r.stories}×</span>
     </div>`).join("");
  el.querySelectorAll(".conv-row").forEach((row) =>
    row.addEventListener("click", () => openEntityDrawer(row.dataset.ent)));
}

/* ---------------- archive ---------------- */

function renderOnThisDate() {
  const o = STATE?.on_this_date;
  const el = $("#on-this-date");
  if (!o) { el.innerHTML = ""; return; }
  el.innerHTML =
    `<div class="otd-label">ON THIS DATE IN THE LOOP · #${o.edition}</div>
     <a href="${esc(o.url)}" target="_blank" rel="noopener">${esc(o.title)}</a>
     <div class="otd-desc">${esc(o.description || "")}</div>`;
}

let archTimer = null;
$("#archive-q").addEventListener("input", (e) => {
  clearTimeout(archTimer);
  const q = e.target.value.trim();
  if (q.length < 3) { $("#archive-hits").innerHTML = ""; return; }
  archTimer = setTimeout(async () => {
    const r = await fetch(`/api/archive/search?q=${encodeURIComponent(q)}`).then((x) => x.json());
    $("#archive-hits").innerHTML = (r.hits || []).map((h) =>
      `<div class="arch-hit">
         <a href="${esc(h.url)}" target="_blank" rel="noopener">#${h.edition} · ${esc(h.title)}</a>
         <div class="arch-meta">${esc(h.date)}</div>
         <div class="arch-snippet">…${esc(h.snippet)}…</div>
       </div>`).join("") || '<div class="loading">nothing in the loop</div>';
  }, 250);
});

/* ---------------- ticker ---------------- */

function renderTicker() {
  if (!STATE) return;
  const items = [];
  for (const stories of Object.values(STATE.signals || {})) {
    for (const s of stories.slice(0, 3)) items.push(s);
  }
  const seen = new Set();
  const uniq = items.filter((s) => !seen.has(s.id) && seen.add(s.id))
    .sort((a, b) => String(b.published_at).localeCompare(String(a.published_at)));
  $("#ticker").innerHTML = uniq.map((s) =>
    `<span><b>${esc(s.source_label || s.source)}</b> ${esc(s.title)}</span>`).join("");
}

/* ---------------- drawer ---------------- */

$("#drawer-close").addEventListener("click", () => $("#drawer").classList.add("hidden"));

const ACCEL_URL = "https://www.antipope.org/charlie/blog-static/fiction/accelerando/accelerando-intro.html";

$("#lobster").addEventListener("click", () => {
  openDrawer("THE LOBSTERS", `
    <p>First uploads in <em>Accelerando</em>: California spiny lobsters, mapped
    neuron by neuron, then dropped into a human internet they were never built
    for. They crew the early deep-space factories. They are the ones who hear
    the extrasolar signal. Manfred figures he will be a lobster too, one day.</p>
    <h2>SOURCE</h2>
    <p><a href="${ACCEL_URL}" target="_blank" rel="noopener">Charles Stross — Accelerando</a></p>
    <p class="dim">CC BY-NC-ND 2.5 · free from the author. The glyph is original
    to this dashboard, not a reproduction of the book.</p>
  `);
});

function setAineko(watching) {
  const el = $("#aineko");
  if (!el) return;
  el.classList.toggle("watching", watching);
  el.title = watching ? "Aineko · watching the ingest" : "Aineko · idle";
  const lab = el.querySelector(".aineko-label");
  if (lab) lab.textContent = watching ? "WATCH" : "IDLE";
}

async function pollIngest() {
  try {
    const r = await fetch("/api/ingest").then((x) => x.json());
    setAineko(!!r.running);
  } catch (e) {
    /* leave the last state; the 30s state poll will catch up */
  }
}

function openDrawer(title, html) {
  $("#drawer-title").textContent = title;
  $("#drawer-body").innerHTML = html;
  $("#drawer").classList.remove("hidden");
}

function openStoryDrawer(s) {
  const ents = (s.entities || []).map((e) =>
    `<span class="ent-chip" data-ent="${esc(e)}">${esc(e)}</span>`).join("");
  openDrawer("SIGNAL", `
    <div><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}</a></div>
    <div class="dim">${esc(s.source_label || "")} · ${relTime(s.published_at)}</div>
    <p style="margin-top:8px">${esc(s.summary || "")}</p>
    ${ents ? `<h2>ENTITIES</h2><div>${ents}</div>` : ""}
  `);
  $("#drawer-body").querySelectorAll(".ent-chip").forEach((c) =>
    c.addEventListener("click", () => openEntityDrawer(c.dataset.ent)));
}

async function openEntityDrawer(name) {
  openDrawer(name.toUpperCase(), '<div class="loading">tracing the graph…</div>');
  const [ego, arch] = await Promise.all([
    fetch(`/api/graph?entity=${encodeURIComponent(name)}`).then((x) => x.json()),
    fetch(`/api/archive/entity?name=${encodeURIComponent(name)}`).then((x) => x.json()),
  ]);
  const editions = (arch.editions || []).map((e) =>
    `<div class="arch-hit"><a href="${esc(e.url)}" target="_blank" rel="noopener">#${e.edition} · ${esc(e.title)}</a>
     <div class="arch-meta">${esc(e.date)} · ${e.mentions} mentions</div></div>`).join("");
  $("#drawer-body").innerHTML = `
    <h2>CONSTELLATION · 7 DAYS</h2>
    <canvas id="ego-canvas" width="430" height="300"></canvas>
    <h2>ALEX WROTE ABOUT THIS</h2>
    ${editions || '<div class="dim">no editions mention this yet</div>'}`;
  drawEgo($("#ego-canvas"), name, ego);
}

function drawEgo(canvas, center, ego) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  ctx.clearRect(0, 0, W, H);

  const stories = (ego.nodes || []).filter((n) => n.kind === "story").slice(0, 12);
  const others = (ego.nodes || []).filter((n) => n.kind === "entity").slice(0, 10);
  const pos = {};

  // ring 1: stories; ring 2: entities
  stories.forEach((n, i) => {
    const a = (i / stories.length) * Math.PI * 2 - Math.PI / 2;
    pos[n.id] = { x: cx + Math.cos(a) * 88, y: cy + Math.sin(a) * 88, n };
  });
  others.forEach((n, i) => {
    const a = (i / others.length) * Math.PI * 2 - Math.PI / 2 + 0.3;
    pos[n.id] = { x: cx + Math.cos(a) * 135, y: cy + Math.sin(a) * 135, n };
  });

  // edges
  ctx.strokeStyle = "rgba(0,229,255,0.22)";
  for (const e of ego.edges || []) {
    const a = e.from === `ent-${center}` ? { x: cx, y: cy } : pos[e.from];
    const b = pos[e.to];
    if (!a || !b) continue;
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
  }
  // nodes
  const dot = (x, y, r, c) => { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); };
  for (const n of stories) dot(pos[n.id].x, pos[n.id].y, 3, "#00e676");
  for (const n of others) {
    dot(pos[n.id].x, pos[n.id].y, 3, "#d500f9");
    ctx.fillStyle = "#5d7285"; ctx.font = "8px monospace"; ctx.textAlign = "center";
    ctx.fillText(n.label.slice(0, 18), pos[n.id].x, pos[n.id].y + 12);
  }
  dot(cx, cy, 6, "#00e5ff");
  ctx.fillStyle = "#eaf7ff"; ctx.font = "bold 10px monospace";
  ctx.fillText(center.slice(0, 24), cx, cy + 20);
}

/* ---------------- polling ---------------- */

async function pollState() {
  try {
    const r = await fetch("/api/state");
    STATE = await r.json();
    for (const [v, meta] of Object.entries(STATE.vectors || {})) VEC_COLORS[v] = meta.color;
    if (STATE.quotes && STATE.quotes.length !== QUOTES.length) {
      QUOTES = STATE.quotes;
      if (quoteIdx === 0) renderQuote();
    }
    renderSI(STATE.si || {});
    renderSpark(STATE.si_history || []);
    renderVectors();
    renderBrief();
    renderConvergence();
    renderOnThisDate();
    renderTicker();
    rebuildGlobeLayers();
    setAineko(!!STATE.ingest_running);
  } catch (e) {
    console.warn("state poll failed", e);
  }
}

async function pollGlobe() {
  try {
    GLOBE_DATA = await fetch("/api/globe").then((x) => x.json());
    rebuildGlobeLayers();
  } catch (e) {
    console.warn("globe poll failed", e);
  }
}

try {
  initGlobe();
} catch (e) {
  console.warn("globe unavailable (WebGL?)", e);
  $("#globe-stats").textContent = "globe unavailable — WebGL disabled";
}
pollState();
pollGlobe();
pollIngest();
setInterval(pollState, 30000);
setInterval(pollGlobe, 300000);
setInterval(pollIngest, 2000);
