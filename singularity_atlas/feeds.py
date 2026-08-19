"""Async feed fetchers. Every source is public: no auth, no registration.

Item shape (normalized):
    id, source, source_label, title, url, summary, published_at,
    vectors_hint, extra (feed-specific: hn points, launch pad geo, gdelt geo)
"""

from __future__ import annotations

import asyncio
import hashlib
import html
import json
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
import re

from . import config

_HEALTH: dict[str, dict] = {}
if config.FEED_HEALTH_FILE.exists():
    try:
        _HEALTH = json.loads(config.FEED_HEALTH_FILE.read_text())
    except Exception:
        _HEALTH = {}


def _record_health(feed_id: str, ok: bool, n_items: int, error: str | None = None) -> None:
    h = _HEALTH.setdefault(feed_id, {})
    h["last_fetch"] = datetime.now(timezone.utc).isoformat()
    h["ok"] = ok
    h["items"] = n_items
    h["error"] = error
    h["fetches"] = h.get("fetches", 0) + 1
    try:
        config.FEED_HEALTH_FILE.write_text(json.dumps(_HEALTH, indent=1))
    except Exception:
        pass


def feed_health() -> dict[str, dict]:
    return _HEALTH


def _mkid(*parts: str) -> str:
    return hashlib.sha1("‖".join(p for p in parts if p).encode()).hexdigest()[:16]


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _parse_date(entry) -> str | None:
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return _iso(datetime.fromtimestamp(time.mktime(t), tz=timezone.utc))
            except Exception:
                pass
    raw = entry.get("published") or entry.get("updated")
    if raw:
        try:
            return _iso(parsedate_to_datetime(raw))
        except Exception:
            return None
    return None


def _clean(s: str | None) -> str:
    """Unescape HTML entities (&amp; &#8217; …) and collapse whitespace."""
    if not s:
        return ""
    return html.unescape(re.sub(r"\s+", " ", s)).strip()


def _strip_html(s: str | None, limit: int = 600) -> str:
    if not s:
        return ""
    txt = re.sub(r"<[^>]+>", " ", s)
    txt = re.sub(r"\s+", " ", txt).strip()
    return html.unescape(txt)[:limit]


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

async def fetch_rss(client: httpx.AsyncClient, feed: dict) -> list[dict]:
    r = await client.get(feed["url"])
    r.raise_for_status()
    parsed = feedparser.parse(r.text)
    items = []
    for e in parsed.entries[:25]:
        title = _clean(e.get("title"))
        url = e.get("link") or ""
        if not title or not url:
            continue
        items.append({
            "id": _mkid(feed["id"], url or title),
            "source": feed["id"], "source_label": feed["label"],
            "title": title, "url": url,
            "summary": _strip_html(e.get("summary") or e.get("description")),
            "published_at": _parse_date(e),
            "vectors_hint": feed.get("vectors", []),
            "extra": {},
        })
    return items


async def fetch_arxiv(client: httpx.AsyncClient, feed: dict) -> list[dict]:
    cats = "+OR+".join(f"cat:{c}" for c in feed["categories"])
    url = ("https://export.arxiv.org/api/query?search_query=" + cats +
           "&sortBy=submittedDate&sortOrder=descending&max_results=12")
    r = await client.get(url)
    r.raise_for_status()
    parsed = feedparser.parse(r.text)
    items = []
    for e in parsed.entries:
        title = _clean(e.get("title")).replace("\n", " ")
        link = e.get("link") or ""
        if not title or not link:
            continue
        items.append({
            "id": _mkid(feed["id"], link),
            "source": feed["id"], "source_label": feed["label"],
            "title": title, "url": link,
            "summary": _strip_html(e.get("summary"), 500),
            "published_at": _parse_date(e),
            "vectors_hint": feed.get("vectors", []),
            "extra": {"kind": "paper"},
        })
    return items


async def fetch_hn(client: httpx.AsyncClient, feed: dict) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for q in feed.get("queries", []):
        r = await client.get("https://hn.algolia.com/api/v1/search",
                             params={"query": q, "tags": "story", "hitsPerPage": 12})
        r.raise_for_status()
        for h in r.json().get("hits", []):
            oid = h.get("objectID")
            if not oid or oid in seen:
                continue
            if (h.get("points") or 0) < feed.get("min_points", 0):
                continue
            seen.add(oid)
            url = h.get("url") or f"https://news.ycombinator.com/item?id={oid}"
            items.append({
                "id": _mkid("hn", oid),
                "source": feed["id"], "source_label": feed["label"],
                "title": _clean(h.get("title")), "url": url,
                "summary": f"{h.get('points', 0)} points · {h.get('num_comments', 0)} comments on HN",
                "published_at": h.get("created_at"),
                "vectors_hint": feed.get("vectors", []),
                "extra": {"points": h.get("points", 0), "comments": h.get("num_comments", 0),
                          "hn_id": oid},
            })
    return items


async def fetch_launches(client: httpx.AsyncClient, feed: dict) -> list[dict]:
    r = await client.get(feed["url"])
    r.raise_for_status()
    items = []
    for L in r.json().get("results", []):
        name = L.get("name") or "Launch"
        net = L.get("net")  # launch time
        pad = L.get("pad") or {}
        loc = pad.get("location") or {}
        provider = (L.get("launch_service_provider") or {}).get("name", "")
        mission = (L.get("mission") or {}).get("description", "")
        status = (L.get("status") or {}).get("name", "")
        items.append({
            "id": _mkid("launch", L.get("id") or name + str(net)),
            "source": feed["id"], "source_label": feed["label"],
            "title": _clean(f"{name} — {provider}"),
            "url": L.get("url") or "https://thespacedevs.com",
            "summary": _strip_html(mission, 400) or status,
            "published_at": net,
            "vectors_hint": feed.get("vectors", []),
            "extra": {
                "kind": "launch", "status": status, "net": net,
                "pad": pad.get("name"), "location": loc.get("name"),
                "lat": _f(pad.get("latitude")), "lon": _f(pad.get("longitude")),
                "provider": provider,
            },
        })
    return items


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


GDELT_RETRY_S = 6  # patient single retry on 429


async def fetch_gdelt(client: httpx.AsyncClient, feed: dict) -> list[dict]:
    r = await client.get(feed["url"])
    if r.status_code == 429:  # GDELT rate-limits aggressively; one patient retry
        await asyncio.sleep(GDELT_RETRY_S)
        r = await client.get(feed["url"])
    r.raise_for_status()
    items = []
    for a in r.json().get("articles", []):
        title = _clean(a.get("title"))
        url = a.get("url") or ""
        if not title or not url:
            continue
        items.append({
            "id": _mkid("gdelt", url),
            "source": feed["id"], "source_label": feed["label"],
            "title": title, "url": url,
            "summary": f"{a.get('sourcecountry', '')} · {a.get('domain', '')}",
            "published_at": _gdelt_date(a.get("seendate")),
            "vectors_hint": feed.get("vectors", []),
            "extra": {"kind": "gdelt", "domain": a.get("domain"),
                      "country": a.get("sourcecountry"), "lang": a.get("language")},
        })
    return items


def _gdelt_date(s: str | None) -> str | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


FETCHERS = {
    "rss": fetch_rss, "arxiv": fetch_arxiv, "hn": fetch_hn,
    "launches": fetch_launches, "gdelt": fetch_gdelt,
}


async def fetch_all(feeds: list[dict] | None = None) -> tuple[list[dict], list[str]]:
    """Fetch every configured feed concurrently; never raises."""
    feeds = feeds if feeds is not None else config.FEEDS
    errors: list[str] = []

    async def one(client, feed):
        try:
            fn = FETCHERS[feed["kind"]]
            items = await fn(client, feed)
            _record_health(feed["id"], True, len(items))
            return items
        except Exception as e:  # noqa: BLE001 - feed isolation by design
            msg = f"{feed['id']}: {type(e).__name__}: {e}"
            errors.append(msg)
            _record_health(feed["id"], False, 0, msg[:300])
            return []

    async with httpx.AsyncClient(
        timeout=config.HTTP_TIMEOUT_S,
        headers={"User-Agent": config.USER_AGENT},
        follow_redirects=True,
    ) as client:
        results = await asyncio.gather(*(one(client, f) for f in feeds))

    items: list[dict] = []
    for r in results:
        items.extend(r)
    return items, errors


if __name__ == "__main__":
    # CLI smoke test: python -m singularity_atlas.feeds
    items, errors = asyncio.run(fetch_all())
    by_source: dict[str, int] = {}
    for it in items:
        by_source[it["source"]] = by_source.get(it["source"], 0) + 1
    for src, n in sorted(by_source.items()):
        print(f"{src:20s} {n:3d} items")
    print(f"\nTOTAL {len(items)} items, {len(errors)} errors")
    for e in errors:
        print("  ERR", e)
