#!/usr/bin/env python3
"""Build the public, backend-free copy of the live Atlas dashboard.

Reads the local API (127.0.0.1:8055) once, writes sanitized JSON under OUT/data/,
copies the unchanged frontend with paths rewritten, the pinned vendored globe.gl +
earth texture, and web/static-shim.js (maps /api/* -> /data/*.json in the browser).
The output is plain static files; nothing in it can reach this machine.

Never shipped: archive search snippets, Innermost Loop issue descriptions or text,
ref/, loop_issues, local model names, raw fetch errors. Story summaries (RSS/arXiv
excerpts) are shipped by design.

usage: build_live_site.py OUT_DIR [--api http://127.0.0.1:8055]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
UNAVAILABLE = "temporarily unavailable"
# Pinned vendor files (see web/vendor/README.md). Build fails if they don't match.
VENDOR = {
    "globe.gl.min.js": "2c3e445c04d121215910a89688b96091c8a72071c122a4f830081a39b636c94c",  # globe.gl 2.46.2
    "earth-night.jpg": "355ab23dd1323315b393d7b91dd2d7ee223a1cbaaba2b48dc72ba90d371ced24",  # three-globe 2.45.6
}
EDITION_KEYS = ("edition", "date", "title", "url", "mentions")   # titles/links only, never text


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "x"


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False))


def sanitize_state(st: dict) -> dict:
    for name, v in (st.get("feeds") or {}).items():
        if v.get("error"):
            print(f"feed {name} error (local log only): {v['error']}", file=sys.stderr)
            v["error"] = UNAVAILABLE
    li = st.get("last_ingest")
    if isinstance(li, dict) and li.get("errors"):
        li["errors"] = [f"{str(e).split(':', 1)[0]}: {UNAVAILABLE}" for e in li["errors"]]
    st["llm"] = {"available": False, "preferred": None, "active": None}
    br = st.get("brief")
    if isinstance(br, dict) and br.get("model") and br["model"] != "heuristic":
        br["model"] = "local LLM"                                     # no local model names
    st["ingest_running"] = False
    otd = st.get("on_this_date")
    if isinstance(otd, dict):
        st["on_this_date"] = {k: otd.get(k) for k in ("edition", "date", "title", "url")}
    return st


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--api", default="http://127.0.0.1:8055")
    a = ap.parse_args()
    out: Path = a.out

    def get(path: str):
        with urllib.request.urlopen(a.api + path, timeout=30) as r:
            return json.load(r)

    if out.exists():
        shutil.rmtree(out)
    for d in ("data/graph", "data/archive-entity", "vendor"):
        (out / d).mkdir(parents=True)

    st = sanitize_state(get("/api/state"))
    dump(out / "data" / "state.json", st)
    gl = get("/api/globe")
    dump(out / "data" / "globe.json", gl)

    ents = {c["name"] for c in st.get("convergence") or [] if c.get("name")}
    for stories in (st.get("signals") or {}).values():
        for s in stories:
            ents.update(s.get("entities") or [])
    for ev in gl.get("events") or []:
        ents.update(ev.get("entities") or [])
    index = {}
    for e in sorted(ents):
        q = urllib.parse.quote(e)
        ego = get(f"/api/graph?entity={q}")
        ego["loop_editions"] = [{k: x.get(k) for k in EDITION_KEYS} for x in ego.get("loop_editions") or []]
        arch = get(f"/api/archive/entity?name={q}")
        arch = {"entity": e, "editions": [{k: x.get(k) for k in EDITION_KEYS} for x in arch.get("editions") or []]}
        sl = slug(e)
        index[e] = sl
        dump(out / "data" / "graph" / f"{sl}.json", ego)
        dump(out / "data" / "archive-entity" / f"{sl}.json", arch)
    dump(out / "data" / "entities.json", index)

    for name, sha in VENDOR.items():
        src = WEB / "vendor" / name
        got = hashlib.sha256(src.read_bytes()).hexdigest()
        if got != sha:
            print(f"FAIL: vendor/{name} sha256 {got} != pinned {sha}", file=sys.stderr)
            return 1
        shutil.copy(src, out / "vendor" / name)

    html = (WEB / "index.html").read_text()
    html = html.replace('href="/static/', 'href="/').replace('src="/static/', 'src="/')
    cdn = '<script src="https://unpkg.com/globe.gl@2"></script>'
    if cdn not in html:
        print("FAIL: expected globe.gl CDN tag not found in web/index.html", file=sys.stderr)
        return 1
    html = html.replace(cdn, '<script src="/vendor/globe.gl.min.js"></script>\n<script src="/static-shim.js"></script>')
    html = html.replace('placeholder="search the archive…"', 'placeholder="search the archive on Substack…"')
    js = (WEB / "app.js").read_text().replace(
        '"//unpkg.com/three-globe/example/img/earth-night.jpg"', '"/vendor/earth-night.jpg"')
    for label, text in (("index.html", html), ("app.js", js)):
        if "unpkg.com" in text or "/static/" in text:
            print(f"FAIL: {label} still references a CDN or /static/", file=sys.stderr)
            return 1
    (out / "index.html").write_text(html)
    (out / "app.js").write_text(js)
    for f in ("style.css", "favicon.svg", "static-shim.js"):
        shutil.copy(WEB / f, out / f)

    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"built live app: {len(index)} entities, {total} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
