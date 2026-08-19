"""Fetch recent issues of The Innermost Loop from its official mirror.

This is a single-file, standard-library-only module. Copy it into any Python
project and import ``fetch_latest_newsletters``.

Example::

    from innermost_loop import fetch_latest_newsletters

    for issue in fetch_latest_newsletters(limit=5):
        print(issue["published_at"], issue["title"], issue["url"])

The official RSS feed includes each issue's full HTML. ``body_html`` preserves
that source HTML; ``body_text`` is a convenient plain-text rendering with
Substack subscription widgets and other interface controls omitted.
"""

from __future__ import annotations

import math
import re
import time
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from http.client import HTTPException
from typing import ClassVar, FrozenSet, List, Optional, TypedDict
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

DEFAULT_FEED_URL = "https://theinnermostloop.substack.com/feed"
DEFAULT_USER_AGENT = (
    "InnermostLoopFetcher/1.0 "
    "(+https://theinnermostloop.substack.com/archive; public RSS reader)"
)
_CONTENT_NAMESPACE = "http://purl.org/rss/1.0/modules/content/"
_DC_NAMESPACE = "http://purl.org/dc/elements/1.1/"
_MAX_FEED_BYTES = 16 * 1024 * 1024
_RETRYABLE_HTTP_STATUS = {408, 425, 429, 500, 502, 503, 504}


class NewsletterFetchError(RuntimeError):
    """Raised when the official feed cannot be downloaded or parsed."""


class Newsletter(TypedDict):
    """JSON-serializable shape returned by ``fetch_latest_newsletters``."""

    title: str
    slug: str
    guid: str
    url: str
    author: str
    published_at: str
    description: str
    cover_image_url: Optional[str]
    audio_url: Optional[str]
    body_html: str
    body_text: str


class _ArticleTextExtractor(HTMLParser):
    """Extract readable article text while dropping Substack interface UI."""

    _BLOCK_TAGS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "address",
            "article",
            "aside",
            "blockquote",
            "div",
            "figcaption",
            "figure",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "hr",
            "main",
            "ol",
            "p",
            "pre",
            "section",
            "table",
            "tbody",
            "td",
            "tfoot",
            "th",
            "thead",
            "tr",
            "ul",
        }
    )
    _VOID_TAGS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
    )
    _SKIP_TAGS: ClassVar[FrozenSet[str]] = frozenset(
        {
            "button",
            "form",
            "noscript",
            "script",
            "select",
            "style",
            "svg",
            "textarea",
        }
    )
    _SKIP_CLASS_PREFIXES = (
        "subscription-widget",
        "paywall",
        "post-ufi",
    )

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._pieces: List[str] = []
        self._skip_depth = 0

    def _append_break(self) -> None:
        if self._pieces and not self._pieces[-1].endswith("\n"):
            self._pieces.append("\n")

    @classmethod
    def _should_skip(cls, tag: str, attrs: List[tuple]) -> bool:
        attributes = {str(key).lower(): value or "" for key, value in attrs}
        classes = attributes.get("class", "").split()
        if tag in cls._SKIP_TAGS:
            return True
        if any(
            token.startswith(prefix)
            for token in classes
            for prefix in cls._SKIP_CLASS_PREFIXES
        ):
            return True
        return attributes.get("data-component-name") == "SubscribeWidgetToDOM"

    def handle_starttag(self, tag: str, attrs: List[tuple]) -> None:
        tag = tag.lower()
        if self._skip_depth:
            if tag not in self._VOID_TAGS:
                self._skip_depth += 1
            return
        if self._should_skip(tag, attrs):
            if tag not in self._VOID_TAGS:
                self._skip_depth = 1
            return
        if tag == "br":
            self._append_break()
        elif tag == "li":
            self._append_break()
            self._pieces.append("- ")
        elif tag in self._BLOCK_TAGS:
            self._append_break()

    def handle_startendtag(self, tag: str, attrs: List[tuple]) -> None:
        if self._skip_depth or self._should_skip(tag.lower(), attrs):
            return
        if tag.lower() in self._BLOCK_TAGS or tag.lower() == "br":
            self._append_break()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._skip_depth:
            self._skip_depth -= 1
            return
        if tag in self._BLOCK_TAGS or tag == "li":
            self._append_break()

    def handle_data(self, data: str) -> None:
        if not self._skip_depth and data:
            self._pieces.append(data)

    def text(self) -> str:
        value = "".join(self._pieces).replace("\xa0", " ")
        value = re.sub(r"[ \t\f\v]+", " ", value)
        value = re.sub(r" *\r?\n *", "\n", value)
        value = re.sub(r"\n{3,}", "\n\n", value)
        return value.strip()


def _html_to_text(source: str) -> str:
    parser = _ArticleTextExtractor()
    try:
        parser.feed(source)
        parser.close()
    except Exception as exc:  # HTMLParser normally recovers malformed HTML.
        raise NewsletterFetchError("Could not parse an issue's HTML body") from exc
    return parser.text()


def _retry_delay(error: HTTPError, attempt: int) -> float:
    retry_after = error.headers.get("Retry-After") if error.headers else None
    if retry_after:
        try:
            return min(max(float(retry_after), 0.0), 30.0)
        except ValueError:
            pass
    return min(0.5 * (2**attempt), 4.0)


def _download_feed(
    feed_url: str,
    *,
    timeout: float,
    retries: int,
    user_agent: str,
) -> bytes:
    request = Request(
        feed_url,
        headers={
            "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": user_agent,
        },
    )
    last_error: Optional[BaseException] = None

    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read(_MAX_FEED_BYTES + 1)
            if len(payload) > _MAX_FEED_BYTES:
                raise NewsletterFetchError(
                    "The RSS response exceeded the 16 MiB safety limit"
                )
            return payload
        except HTTPError as exc:
            last_error = exc
            if exc.code not in _RETRYABLE_HTTP_STATUS or attempt == retries:
                raise NewsletterFetchError(
                    f"HTTP {exc.code} while fetching {feed_url}"
                ) from exc
            time.sleep(_retry_delay(exc, attempt))
        except (URLError, TimeoutError, OSError, HTTPException) as exc:
            last_error = exc
            if attempt == retries:
                break
            time.sleep(min(0.5 * (2**attempt), 4.0))

    raise NewsletterFetchError(
        f"Could not fetch {feed_url}: {last_error}"
    ) from last_error


def _published_at(value: str, url: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError) as exc:
        raise NewsletterFetchError(
            f"Invalid publication date {value!r} for {url}"
        ) from exc
    if parsed.tzinfo is None:
        raise NewsletterFetchError(f"Publication date has no timezone for {url}")
    return parsed.astimezone(timezone.utc).isoformat()


def _slug_from_url(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def _parse_item(item: ET.Element) -> Newsletter:
    title = (item.findtext("title") or "").strip()
    url = (item.findtext("link") or "").strip()
    guid = (item.findtext("guid") or url).strip()
    author = (item.findtext(f"{{{_DC_NAMESPACE}}}creator") or "").strip()
    date_text = (item.findtext("pubDate") or "").strip()
    description_html = item.findtext("description") or ""
    body_html = item.findtext(f"{{{_CONTENT_NAMESPACE}}}encoded") or ""

    if not title or not url or not guid or not date_text or not body_html:
        raise NewsletterFetchError(
            "An RSS item is missing title, URL, date, or full body HTML"
        )
    parsed_url = urlsplit(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise NewsletterFetchError(f"An RSS item has an invalid URL: {url!r}")

    cover_image_url: Optional[str] = None
    audio_url: Optional[str] = None
    for enclosure in item.findall("enclosure"):
        enclosure_url = (enclosure.get("url") or "").strip()
        media_type = (enclosure.get("type") or "").lower()
        if not enclosure_url:
            continue
        if media_type.startswith("image/") and cover_image_url is None:
            cover_image_url = enclosure_url
        elif media_type.startswith("audio/") and audio_url is None:
            audio_url = enclosure_url

    return Newsletter(
        title=title,
        slug=_slug_from_url(url),
        guid=guid,
        url=url,
        author=author,
        published_at=_published_at(date_text, url),
        description=_html_to_text(description_html),
        cover_image_url=cover_image_url,
        audio_url=audio_url,
        body_html=body_html,
        body_text=_html_to_text(body_html),
    )


def fetch_latest_newsletters(
    limit: int = 10,
    *,
    feed_url: str = DEFAULT_FEED_URL,
    timeout: float = 20.0,
    retries: int = 2,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[Newsletter]:
    """Return the newest issues from the author's official public mirror.

    The result is newest-first. Each dictionary is JSON serializable and
    includes metadata, the complete source HTML, and cleaned plain text.

    Args:
        limit: Maximum number of issues to return. ``0`` returns immediately.
            Substack's official RSS feed currently exposes its latest 20
            issues, so asking for more returns however many the feed provides.
        feed_url: RSS URL to read. The default is The Innermost Loop's official
            mirror; this argument also makes local/integration testing easy.
        timeout: Per-request network timeout in seconds.
        retries: Number of retries after the initial request for transient
            network errors and retryable HTTP statuses.
        user_agent: HTTP User-Agent header.

    Raises:
        ValueError: If an argument is invalid.
        NewsletterFetchError: If the feed cannot be fetched or parsed.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError("limit must be a non-negative integer")
    if limit == 0:
        return []
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or not math.isfinite(float(timeout))
        or timeout <= 0
    ):
        raise ValueError("timeout must be a positive number")
    if isinstance(retries, bool) or not isinstance(retries, int) or retries < 0:
        raise ValueError("retries must be a non-negative integer")
    if not isinstance(feed_url, str) or not feed_url.strip():
        raise ValueError("feed_url must be a non-empty URL")
    feed_url = feed_url.strip()
    parsed_url = urlsplit(feed_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("feed_url must be an absolute HTTP(S) URL")
    if not isinstance(user_agent, str) or not user_agent.strip():
        raise ValueError("user_agent must be a non-empty string")
    if "\r" in user_agent or "\n" in user_agent:
        raise ValueError("user_agent cannot contain CR or LF characters")
    user_agent = user_agent.strip()

    payload = _download_feed(
        feed_url,
        timeout=float(timeout),
        retries=retries,
        user_agent=user_agent,
    )
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise NewsletterFetchError("The RSS response is not valid XML") from exc

    channel = root.find("channel")
    if root.tag != "rss" or channel is None:
        raise NewsletterFetchError("The response is not an RSS 2.0 feed")

    issues: List[Newsletter] = []
    seen_guids = set()
    for item in channel.findall("item"):
        issue = _parse_item(item)
        if issue["guid"] in seen_guids:
            continue
        seen_guids.add(issue["guid"])
        issues.append(issue)
    issues.sort(key=lambda issue: issue["published_at"], reverse=True)
    return issues[:limit]


__all__ = [
    "DEFAULT_FEED_URL",
    "Newsletter",
    "NewsletterFetchError",
    "fetch_latest_newsletters",
]
