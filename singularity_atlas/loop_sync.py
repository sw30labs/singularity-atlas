"""Keep the Loop Archive current with Alex's official Substack mirror.

Any local corpus under ``ref/`` is a fixed reference set that stops at whatever
edition it was captured on (and is not in version control). This module fetches
issues published since then and writes them, in the same markdown +
front-matter shape, into ``data/loop_issues/`` so ``loop_archive.load_issues()``
picks them up alongside it. ``ref/`` is never modified.

Dating follows the corpus convention exactly (verified to reproduce all 218
shipped issue dates): a "Welcome to <Month D, YYYY>" title is authoritative,
and anything else falls back to the feed's publication date. The feed's
``pubDate`` is often a day *after* the issue it carries -- edition 218 is
titled "Welcome to August 17, 2026" but was published 2026-08-18 -- so keying
off ``published_at`` alone would date every edition a day late and skew
``on_this_date()``.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

from . import config, innermost_loop, loop_archive

_TITLE_DATE_RE = re.compile(r"welcome to ([a-z]+ \d{1,2}, \d{4})\s*$", re.I)

# Constants shared by every edition in the corpus, carried over so fetched
# editions stay homogeneous with the shipped ones.
_NEWSLETTER_TITLE = "The Innermost Loop"
_NEWSLETTER_ID = "7404871891775025153"
_LINKEDIN_URL = (
    "https://www.linkedin.com/newsletters/"
    "the-innermost-loop-7404871891775025153/"
)
_SOURCE_MIRROR = "Author's official Substack publication"


def issue_date(title: str, published_at: str) -> tuple[str, str]:
    """Return (YYYY-MM-DD, basis) for an issue, mirroring the corpus rule."""
    m = _TITLE_DATE_RE.search((title or "").strip())
    if m:
        try:
            parsed = datetime.strptime(m.group(1), "%B %d, %Y")
            return parsed.strftime("%Y-%m-%d"), "title"
        except ValueError:
            pass
    return (published_at or "")[:10], "published_at"


def _fm(value) -> str:
    """Flatten a value so it survives the archive's line-based front matter."""
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace('"', "'")


def _render(issue: dict, edition: int, captured_at: str) -> str:
    """Serialize one fetched issue in the shipped corpus's exact shape."""
    date, basis = issue_date(issue["title"], issue["published_at"])
    body = issue["body_text"]
    html = issue["body_html"]
    fields = [
        ("schema_version", 1),
        ("edition_number", edition),
        ("title", _fm(issue["title"])),
        ("newsletter_title", _NEWSLETTER_TITLE),
        ("newsletter_id", _NEWSLETTER_ID),
        ("linkedin_newsletter_url", _LINKEDIN_URL),
        ("author_name", _fm(issue["author"]) or "Dr. Alex Wissner-Gross"),
        ("issue_date", date),
        ("issue_date_basis", basis),
        ("published_at", issue["published_at"]),
        ("modified_at", issue["published_at"]),
        ("source_url", issue["url"]),
        ("source_mirror", _SOURCE_MIRROR),
        ("language", "en"),
        ("description", _fm(issue["description"])[:400]),
        ("cover_image_url", issue.get("cover_image_url") or ""),
        ("content_kind", "article"),
        ("word_count", len(body.split())),
        ("link_count", html.count("<a ")),
        ("image_count", html.count("<img")),
        ("content_sha256", hashlib.sha256(body.encode("utf-8")).hexdigest()),
        ("captured_at", captured_at),
    ]
    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}: {value}" if isinstance(value, int)
                     else f'{key}: "{value}"')
    lines.append("---")
    lines.append("")
    lines.append(body)
    lines.append("")
    return "\n".join(lines)


def _read_state() -> dict:
    try:
        return json.loads(config.LOOP_SYNC_STATE_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _write_state(state: dict) -> None:
    config.LOOP_SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.LOOP_SYNC_STATE_FILE.write_text(json.dumps(state, indent=2))


def last_sync() -> dict:
    """What the scheduler and API report: when we last looked, and what for."""
    return _read_state()


def due(now: datetime | None = None) -> bool:
    """True when the feed has not been checked for LOOP_SYNC_INTERVAL_H."""
    stamp = _read_state().get("checked_at")
    if not stamp:
        return True
    try:
        last = datetime.fromisoformat(stamp)
    except ValueError:
        return True
    now = now or datetime.now(timezone.utc)
    return now - last >= timedelta(hours=config.LOOP_SYNC_INTERVAL_H)


def sync(limit: int | None = None, *, now: datetime | None = None) -> dict:
    """Fetch the feed and write any editions the archive does not have yet.

    Never raises: a feed outage is recorded in the sync state and reported,
    so a scheduled run can fail without taking the ingest cycle down.
    """
    now = now or datetime.now(timezone.utc)
    captured_at = now.isoformat()
    state = {"checked_at": captured_at, "new": 0, "error": None}

    try:
        fetched = innermost_loop.fetch_latest_newsletters(
            limit=config.LOOP_FETCH_LIMIT if limit is None else limit,
            feed_url=config.LOOP_FEED_URL,
        )
    except (innermost_loop.NewsletterFetchError, ValueError) as exc:
        state["error"] = f"{type(exc).__name__}: {exc}"
        _write_state(state)
        return {**state, "issues": []}

    existing = loop_archive.load_issues()
    known = {it["slug"] for it in existing if it["slug"]}
    edition = max((it["edition"] for it in existing), default=0)

    # oldest first, so edition numbers continue in publication order
    pending = [i for i in reversed(fetched) if i["slug"] and i["slug"] not in known]
    config.LOOP_FETCH_DIR.mkdir(parents=True, exist_ok=True)

    written = []
    for issue in pending:
        edition += 1
        date, _ = issue_date(issue["title"], issue["published_at"])
        path = config.LOOP_FETCH_DIR / f"{edition:03d}--{date}--{issue['slug']}.md"
        path.write_text(_render(issue, edition, captured_at), encoding="utf-8")
        written.append({"edition": edition, "date": date,
                        "title": issue["title"], "url": issue["url"],
                        "slug": issue["slug"]})

    if written:
        loop_archive.invalidate()

    state["new"] = len(written)
    state["latest"] = written[-1]["date"] if written else (
        max((it["date"] for it in existing), default="")
    )
    _write_state(state)
    return {**state, "issues": written}


def sync_and_persist(store, limit: int | None = None,
                     *, now: datetime | None = None) -> dict:
    """Sync, then push only the new editions into the graph.

    ``store`` is passed in rather than imported so a sync can be exercised
    without a Neo4j connection.
    """
    result = sync(limit, now=now)
    if not result["issues"]:
        return {**result, "persisted": 0}
    new_slugs = {i["slug"] for i in result["issues"]}
    fresh = [it for it in loop_archive.load_issues() if it["slug"] in new_slugs]
    persisted = store.persist_items(loop_archive.as_stories(fresh))
    return {**result, "persisted": persisted}
