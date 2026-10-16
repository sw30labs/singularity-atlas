/* Static mode for the public site: map the dashboard's /api/* calls to baked JSON
   under ./data/. Read-only: no server, no writes, nothing reaches the machine that
   built it. Loaded only by the static build (scripts/build_live_site.py). */
(() => {
  const realFetch = window.fetch.bind(window);
  const slug = (s) => (String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "x");
  const json = (o) => Promise.resolve(new Response(JSON.stringify(o), { headers: { "Content-Type": "application/json" } }));
  const orEmpty = (empty) => (r) => (r.ok ? r : json(empty));
  window.ATLAS_STATIC = true;
  window.fetch = (input, init) => {
    const u = new URL(typeof input === "string" ? input : input.url, location.href);
    if (u.origin !== location.origin || !u.pathname.startsWith("/api/")) return realFetch(input, init);
    if ((init?.method || "GET").toUpperCase() !== "GET") return json({ error: "read-only snapshot" });
    const p = u.pathname, q = u.searchParams;
    switch (p) {
      case "/api/state": return realFetch("/data/state.json", { cache: "no-cache" });
      case "/api/globe": return realFetch("/data/globe.json", { cache: "no-cache" });
      case "/api/ingest": return json({ running: false, last: null });
      case "/api/graph":
        return realFetch(`/data/graph/${slug(q.get("entity") || "")}.json`).then(orEmpty({ nodes: [], edges: [], loop_editions: [] }));
      case "/api/archive/entity":
        return realFetch(`/data/archive-entity/${slug(q.get("name") || "")}.json`).then(orEmpty({ editions: [] }));
      case "/api/archive/search": {
        const s = q.get("q") || "";
        return json({ q: s, hits: [{
          edition: "↗", date: "full-text search lives on the newsletter",
          title: `search “${s}” on The Innermost Loop`, snippet: "",
          url: `https://theinnermostloop.substack.com/archive?sort=search&search=${encodeURIComponent(s)}`,
        }] });
      }
      default: return json({});
    }
  };
})();
