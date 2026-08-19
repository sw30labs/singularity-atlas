"""The Loop Archive: the Innermost Loop editions as a searchable,
graph-seedable corpus of local markdown.

Two sources, same format: the fixed corpus shipped under ``ref/`` and any
newer editions ``loop_sync`` has fetched into ``data/loop_issues/``. Reading
stays offline; only ``loop_sync`` touches the network.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from . import config, taxonomy

_ISSUES: list[dict] | None = None

_FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_IMG_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")


def _parse_front_matter(raw: str) -> dict:
    m = _FM_RE.match(raw)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        v = v.strip().strip('"').strip("'")
        out[k.strip()] = v
    return out


def _body(raw: str) -> str:
    m = _FM_RE.match(raw)
    return raw[m.end():] if m else raw


def plain_text(body: str) -> str:
    t = _IMG_RE.sub(" ", body)
    t = _LINK_RE.sub(lambda m: m.group(1), t)
    t = re.sub(r"[#>*`-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def invalidate() -> None:
    """Drop the in-process cache after loop_sync writes new editions."""
    global _ISSUES
    _ISSUES = None


def _slug(url: str, path) -> str:
    """Stable identity for an edition: the Substack post slug."""
    tail = url.rstrip("/").rsplit("/", 1)[-1] if url else ""
    if tail:
        return tail
    # filename shape is NNN--YYYY-MM-DD--slug.md
    parts = path.stem.split("--", 2)
    return parts[2] if len(parts) == 3 else path.stem


def _read_dir(directory) -> list[dict]:
    issues = []
    for path in sorted(directory.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        fm = _parse_front_matter(raw)
        body = _body(raw)
        text = plain_text(body)
        url = fm.get("source_url", "")
        issues.append({
            "edition": int(fm.get("edition_number", "0") or 0),
            "date": fm.get("issue_date", ""),
            "title": fm.get("title", path.stem),
            "url": url,
            "slug": _slug(url, path),
            "description": fm.get("description", ""),
            "word_count": int(fm.get("word_count", "0") or 0),
            "body": body,
            "text": text,
        })
    return issues


def load_issues() -> list[dict]:
    """Shipped corpus plus fetched editions, deduped by slug, oldest first."""
    global _ISSUES
    if _ISSUES is not None:
        return _ISSUES
    issues = _read_dir(config.LOOP_ARCHIVE_DIR)
    seen = {it["slug"] for it in issues}
    if config.LOOP_FETCH_DIR.exists():
        for it in _read_dir(config.LOOP_FETCH_DIR):
            # the shipped corpus wins if an edition somehow exists in both
            if it["slug"] not in seen:
                seen.add(it["slug"])
                issues.append(it)
    issues.sort(key=lambda it: (it["edition"], it["date"]))
    _ISSUES = issues
    return issues


def as_stories(issues: list[dict] | None = None) -> list[dict]:
    """Convert editions to story dicts for graph seeding (origin=archive).

    Defaults to the whole archive; pass a subset to persist just new editions.
    """
    stories = []
    for it in issues if issues is not None else load_issues():
        text = f"{it['title']}\n{it['description']}\n{it['text'][:1200]}"
        scores = taxonomy.classify_text(text)
        entities = taxonomy.extract_entities(text)
        places = taxonomy.extract_places(text)
        stories.append({
            "id": f"loop-{it['edition']:03d}",
            "source": "innermost-loop", "source_label": "The Innermost Loop",
            "title": it["title"], "url": it["url"],
            "summary": it["description"] or it["text"][:300],
            "published_at": f"{it['date']}T09:00:00+00:00" if it["date"] else None,
            "vectors": {v: round(s, 2) for v, s in scores.items()},
            "entities": entities[:10], "places": places[:3],
            "salience": taxonomy.salience(text, scores) + 1.0,  # editions are dense
            "origin": "archive",
        })
    return stories


_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "were",
    "has", "have", "had", "not", "but", "you", "your", "its", "our", "their",
    "his", "her", "she", "him", "they", "them", "all", "can", "will", "would",
    "there", "here", "what", "when", "where", "which", "who", "how", "why",
    "into", "over", "under", "about", "after", "before", "between", "more",
    "than", "then", "now", "out", "off", "new", "one", "two", "say", "says",
    "said", "via",
}


def search(query: str, limit: int = 8) -> list[dict]:
    """Naive but effective term search over editions. Title hits weigh 3x."""
    terms = [t.lower() for t in re.findall(r"\w+", query)
             if len(t) > 2 and t.lower() not in _STOPWORDS]
    if not terms:
        return []
    hits = []
    for it in load_issues():
        title_l = it["title"].lower()
        text_l = it["text"].lower()
        score = sum(title_l.count(t) * 3 + text_l.count(t) for t in terms)
        if score:
            # snippet around first term occurrence
            idx = min((text_l.find(t) for t in terms if text_l.find(t) >= 0),
                      default=0)
            snippet = it["text"][max(0, idx - 80): idx + 220].strip()
            hits.append({"edition": it["edition"], "date": it["date"],
                         "title": it["title"], "url": it["url"],
                         "score": score, "snippet": snippet})
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def on_this_date(month_day: str | None = None) -> dict | None:
    """Edition closest to today's month-day in the archive (there is ~1/day)."""
    md = month_day or datetime.now(timezone.utc).strftime("%m-%d")
    for it in load_issues():
        if it["date"][5:] == md:
            return {k: it[k] for k in ("edition", "date", "title", "url", "description")}
    return None


def entity_editions(entity: str, limit: int = 5) -> list[dict]:
    """Editions mentioning an entity — 'Alex wrote about this'."""
    q = re.escape(entity.lower())
    hits = []
    for it in load_issues():
        n = len(re.findall(q, it["text"].lower()))
        if n:
            hits.append({"edition": it["edition"], "date": it["date"],
                         "title": it["title"], "url": it["url"], "mentions": n})
    hits.sort(key=lambda h: h["mentions"], reverse=True)
    return hits[:limit]
