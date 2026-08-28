#!/usr/bin/env python3
"""Write a public 24h static snapshot under docs/ for GitHub Pages.

Requires the dashboard at http://127.0.0.1:8055. Never copies ref/,
Innermost Loop archive bodies, or Neo4j dumps.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
STATE_URL = "http://127.0.0.1:8055/api/state"
ET = ZoneInfo("America/New_York")

WIKI = "https://github.com/sw30labs/.github/wiki/singularity-atlas"
REPO = "https://github.com/sw30labs/singularity-atlas"


def md_lite(text: str) -> str:
    text = html.escape(text or "")
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"^# (.+)$", r"<h2>\1</h2>", text, flags=re.M)
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out = []
    for p in paras:
        if p.startswith("<h2>"):
            out.append(p)
        else:
            out.append("<p>" + p.replace("\n", "<br />") + "</p>")
    return "\n".join(out)


def slim(state: dict) -> dict:
    si = state.get("si") or {}
    brief = state.get("brief") or {}
    feeds = {}
    for k, v in (state.get("feeds") or {}).items():
        feeds[k] = {
            "ok": bool(v.get("ok")),
            "items": v.get("items"),
            "last_fetch": v.get("last_fetch"),
            "error": v.get("error"),
        }
    vectors = {}
    for k, v in (si.get("vectors") or {}).items():
        vectors[k] = {
            "label": v.get("label"),
            "score": v.get("score"),
            "blurb": v.get("blurb"),
            "color": v.get("color"),
        }
    conv = []
    for e in (state.get("convergence") or [])[:12]:
        conv.append({
            "name": e.get("name"),
            "type": e.get("type"),
            "vecs": e.get("vecs"),
            "stories": e.get("stories"),
            "heat": e.get("heat"),
        })
    now = datetime.now(timezone.utc)
    return {
        "generated_utc": now.isoformat(),
        "generated_et": now.astimezone(ET).strftime("%Y-%m-%d %H:%M %Z"),
        "si": si.get("si"),
        "epoch": (si.get("epoch") or {}).get("name"),
        "n_stories_24h": si.get("n_stories_24h"),
        "countdown": si.get("countdown"),
        "vectors": vectors,
        "graph": state.get("graph"),
        "llm": state.get("llm"),
        "brief": {
            "date": brief.get("date"),
            "model": brief.get("model"),
            "n_items": brief.get("n_items"),
            "text": brief.get("text"),
            "created_at": brief.get("created_at"),
        },
        "feeds": feeds,
        "convergence": conv,
        "last_ingest": state.get("last_ingest"),
    }


def page(snap: dict) -> str:
    vectors = snap.get("vectors") or {}
    chips = []
    for key, v in vectors.items():
        score = v.get("score")
        label = html.escape(str(v.get("label") or key))
        color = html.escape(str(v.get("color") or "#eb6c36"))
        score_s = f"{score:.1f}" if isinstance(score, (int, float)) else "—"
        chips.append(
            f'<div class="vec"><span class="dot" style="background:{color}"></span>'
            f'<span class="vlabel">{label}</span>'
            f'<span class="vscore">{score_s}</span></div>'
        )
    feeds = snap.get("feeds") or {}
    ok_n = sum(1 for v in feeds.values() if v.get("ok"))
    feed_rows = []
    for name, v in feeds.items():
        status = "ok" if v.get("ok") else "fail"
        err = html.escape(str(v.get("error") or ""))
        extra = f" · {err}" if err else ""
        feed_rows.append(
            f'<li class="{status}"><code>{html.escape(name)}</code> '
            f'{v.get("items") or 0} items{extra}</li>'
        )
    conv = []
    for e in snap.get("convergence") or []:
        conv.append(
            f'<li><strong>{html.escape(str(e.get("name")))}</strong> '
            f'<span class="muted">{html.escape(", ".join(e.get("vecs") or []))}</span></li>'
        )
    si = snap.get("si")
    si_s = f"{si:.1f}" if isinstance(si, (int, float)) else "—"
    brief = snap.get("brief") or {}
    model = html.escape(str(brief.get("model") or "heuristic"))
    graph = snap.get("graph") or {}
    if (DOCS / "board.png").exists():
        board_img = '<img class="board" src="board.png" alt="The Singularity Atlas dashboard, last capture" />'
    elif (DOCS / "dashboard.gif").exists():
        board_img = '<img class="board" src="dashboard.gif" alt="The Singularity Atlas dashboard" />'
    else:
        board_img = ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>The Singularity Atlas · last 24h</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
  <style>
    :root {{
      --paper: #f5f5f5; --ink: #2d3142; --muted: #4f5d75; --accent: #eb6c36;
      --sans: 'Geist', system-ui, sans-serif; --serif: 'Instrument Serif', serif;
      --mono: 'Geist Mono', ui-monospace, monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: var(--sans); background: var(--paper); color: var(--ink); line-height: 1.5; }}
    header {{ padding: 2.5rem 1.5rem 1.5rem; max-width: 1080px; margin: 0 auto; }}
    .eyebrow {{ font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.16em; text-transform: uppercase; color: var(--muted); }}
    h1 {{ font-family: var(--serif); font-size: 2.4rem; font-weight: 400; margin: 0.35rem 0 0.5rem; }}
    .lede {{ color: var(--muted); max-width: 42rem; }}
    .meta {{ font-family: var(--mono); font-size: 0.78rem; color: var(--muted); margin-top: 0.75rem; }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    main {{ max-width: 1080px; margin: 0 auto; padding: 0 1.5rem 4rem; }}
    .hero {{ display: grid; grid-template-columns: 180px 1fr; gap: 1.5rem; align-items: center; margin: 1.5rem 0 2rem; }}
    .si {{ font-family: var(--serif); font-size: 5rem; line-height: 0.9; color: var(--accent); }}
    .si small {{ display: block; font-family: var(--mono); font-size: 0.75rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); margin-top: 0.4rem; }}
    .vecs {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.4rem 1rem; }}
    .vec {{ display: flex; gap: 0.5rem; align-items: baseline; font-size: 0.92rem; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; }}
    .vlabel {{ flex: 1; }}
    .vscore {{ font-family: var(--mono); }}
    .board {{ width: 100%; border: 1px solid rgba(45,49,66,0.12); margin: 1.5rem 0; background: #fff; }}
    .grid {{ display: grid; grid-template-columns: 1.4fr 0.8fr; gap: 2rem; }}
    h2 {{ font-family: var(--serif); font-size: 1.4rem; font-weight: 400; margin: 1.2rem 0 0.6rem; }}
    .brief p {{ margin: 0.7rem 0; }}
    .muted {{ color: var(--muted); font-size: 0.85rem; }}
    ul {{ list-style: none; }}
    li {{ margin: 0.25rem 0; }}
    li.fail {{ color: var(--accent); }}
    footer {{ max-width: 1080px; margin: 0 auto; padding: 0 1.5rem 3rem; color: var(--muted); font-size: 0.85rem; }}
    @media (max-width: 720px) {{ .hero, .grid {{ grid-template-columns: 1fr; }} .si {{ font-size: 3.5rem; }} }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">Public 24h snapshot · not the live globe</div>
    <h1>The Singularity Atlas</h1>
    <p class="lede">Yesterday's board. The live dashboard stays on the machine that runs it. This page is replaced at least daily.</p>
    <p class="meta">Captured {html.escape(snap.get("generated_et") or "")} · {html.escape(str(snap.get("n_stories_24h") or 0))} stories in 24h · graph {graph.get("stories") or 0} stories / {graph.get("entities") or 0} entities · brief {model}</p>
  </header>
  <main>
    <div class="hero">
      <div>
        <div class="si">{si_s}<small>{html.escape(str(snap.get("epoch") or ""))} · /100</small></div>
      </div>
      <div class="vecs">{''.join(chips)}</div>
    </div>
    {board_img}
    <div class="grid">
      <section class="brief">
        <h2>The Daily Loop</h2>
        {md_lite(brief.get("text") or "")}
      </section>
      <aside>
        <h2>Crossing streams</h2>
        <ul>{''.join(conv) or '<li class="muted">none this cycle</li>'}</ul>
        <h2>Feeds {ok_n}/{len(feeds)}</h2>
        <ul>{''.join(feed_rows)}</ul>
      </aside>
    </div>
  </main>
  <footer>
    <p><a href="{WIKI}">Wiki</a> · <a href="{REPO}">Repo</a> · local live is <code>http://localhost:8055</code>. Code Apache-2.0. This snapshot is public feeds plus the on-machine brief. It does not ship the Innermost Loop corpus or <code>ref/</code>.</p>
  </footer>
</body>
</html>
"""


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default=STATE_URL)
    args = p.parse_args()
    with urllib.request.urlopen(args.url, timeout=20) as r:
        state = json.load(r)
    snap = slim(state)
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "snapshot.json").write_text(json.dumps(snap, indent=2) + "\n")
    (DOCS / "index.html").write_text(page(snap))
    print(f"wrote {DOCS / 'index.html'}  SI={snap.get('si')}  {snap.get('generated_et')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
