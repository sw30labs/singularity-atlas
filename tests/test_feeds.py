"""Feed fetchers: parsers against canned payloads (httpx MockTransport, offline)."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from singularity_atlas import feeds

RSS_XML = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Test Feed</title>
<item><title>OpenAI unveils GPT-6 &amp; partners</title>
<link>https://example.com/gpt6</link>
<description>&lt;p&gt;A frontier model&lt;/p&gt;</description>
<pubDate>Tue, 19 Aug 2026 00:00:00 GMT</pubDate></item>
<item><title>Second story</title><link>https://example.com/2</link></item>
</channel></rss>"""

ARXIV_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Attention Is Still All You Need</title>
<id>http://arxiv.org/abs/2608.00001v1</id>
<summary>We show transformers scale forever.</summary>
<published>2026-08-18T00:00:00Z</published></entry>
</feed>"""

HN_JSON = {"hits": [
    {"objectID": "1", "title": "AGI achieved?", "url": "https://x.com/a",
     "points": 500, "num_comments": 300, "created_at": "2026-08-19T00:00:00.000Z"},
    {"objectID": "2", "title": "Low points story", "url": "https://x.com/b",
     "points": 3, "num_comments": 1, "created_at": "2026-08-19T00:00:00.000Z"},
]}

LAUNCH_JSON = {"results": [{
    "id": "abc", "name": "Falcon 9 | Starlink 10-39", "net": "2026-08-20T15:19:00Z",
    "url": "https://thespacedevs.com/x",
    "status": {"name": "Go for Launch"},
    "launch_service_provider": {"name": "SpaceX"},
    "mission": {"description": "Batch of satellites."},
    "pad": {"name": "CCSFS SLC 40", "latitude": "28.56194122", "longitude": "-80.57735736",
            "location": {"name": "Cape Canaveral"}},
}]}

GDELT_JSON = {"articles": [{
    "url": "https://news.example/ai", "title": "AI summit convenes",
    "seendate": "20260819T010000Z", "domain": "news.example",
    "sourcecountry": "United States", "language": "English",
}]}


def client_with(routes: dict[str, tuple[int, object]]) -> httpx.AsyncClient:
    """AsyncClient whose GETs are answered from {url-substring: (status, body)}."""
    def handler(request: httpx.Request) -> httpx.Response:
        for key, (status, body) in routes.items():
            if key in str(request.url):
                if isinstance(body, (dict, list)):
                    return httpx.Response(status, json=body)
                return httpx.Response(status, text=body)
        return httpx.Response(404, text="no route")
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


class TestHelpers:
    def test_clean_unescapes_entities(self):
        assert feeds._clean("Claude&#8217;s &amp; friends") == "Claude’s & friends"

    def test_strip_html(self):
        out = feeds._strip_html("<p>Hello <b>world</b> &amp; all</p>")
        assert out == "Hello world & all"

    def test_strip_html_limit(self):
        assert len(feeds._strip_html("x" * 5000, limit=100)) == 100

    def test_mkid_deterministic(self):
        assert feeds._mkid("a", "b") == feeds._mkid("a", "b")
        assert feeds._mkid("a", "b") != feeds._mkid("a", "c")

    def test_gdelt_date(self):
        assert feeds._gdelt_date("20260819T010000Z") == "2026-08-19T01:00:00+00:00"
        assert feeds._gdelt_date("garbage") is None
        assert feeds._gdelt_date(None) is None

    def test_float_coercion(self):
        assert feeds._f("28.5") == 28.5
        assert feeds._f(None) is None
        assert feeds._f("nope") is None


class TestFetchers:
    def test_rss(self):
        client = client_with({"rss": (200, RSS_XML)})
        feed = {"id": "t", "kind": "rss", "label": "T", "url": "https://x/rss",
                "vectors": ["capability"]}
        items = asyncio.run(feeds.fetch_rss(client, feed))
        assert len(items) == 2
        first = items[0]
        assert first["title"] == "OpenAI unveils GPT-6 & partners"  # unescaped
        assert first["url"] == "https://example.com/gpt6"
        assert first["published_at"] is not None
        assert first["vectors_hint"] == ["capability"]
        assert "frontier model" in first["summary"]
        assert "<p>" not in first["summary"]

    def test_arxiv(self):
        client = client_with({"arxiv": (200, ARXIV_ATOM)})
        feed = {"id": "a", "kind": "arxiv", "label": "A", "categories": ["cs.AI"],
                "vectors": ["capability"]}
        items = asyncio.run(feeds.fetch_arxiv(client, feed))
        assert len(items) == 1
        assert items[0]["extra"]["kind"] == "paper"
        assert "arxiv.org" in items[0]["url"]

    def test_hn_min_points_and_dedupe(self):
        client = client_with({"algolia": (200, HN_JSON)})
        feed = {"id": "hn", "kind": "hn", "label": "HN",
                "queries": ["AI", "AGI"], "min_points": 60, "vectors": []}
        items = asyncio.run(feeds.fetch_hn(client, feed))
        # both queries return the same payload → dedupe by objectID; low-points filtered
        assert len(items) == 1
        assert items[0]["title"] == "AGI achieved?"
        assert items[0]["extra"]["points"] == 500

    def test_launches_geo(self):
        client = client_with({"thespacedevs": (200, LAUNCH_JSON)})
        feed = {"id": "l", "kind": "launches", "label": "L",
                "url": "https://ll.thespacedevs.com/x", "vectors": ["space"]}
        items = asyncio.run(feeds.fetch_launches(client, feed))
        assert len(items) == 1
        e = items[0]["extra"]
        assert e["lat"] == pytest.approx(28.56, abs=0.01)
        assert e["lon"] == pytest.approx(-80.58, abs=0.01)
        assert e["provider"] == "SpaceX"

    def test_gdelt(self):
        client = client_with({"gdeltproject": (200, GDELT_JSON)})
        feed = {"id": "g", "kind": "gdelt", "label": "G",
                "url": "https://api.gdeltproject.org/x", "vectors": ["culture"]}
        items = asyncio.run(feeds.fetch_gdelt(client, feed))
        assert len(items) == 1
        assert items[0]["published_at"] == "2026-08-19T01:00:00+00:00"

    def test_gdelt_429_retry(self, monkeypatch):
        monkeypatch.setattr(feeds, "GDELT_RETRY_S", 0)
        calls = {"n": 0}

        def handler(request):
            calls["n"] += 1
            if calls["n"] == 1:
                return httpx.Response(429)
            return httpx.Response(200, json=GDELT_JSON)

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        feed = {"id": "g", "kind": "gdelt", "label": "G",
                "url": "https://api.gdeltproject.org/x", "vectors": []}
        items = asyncio.run(feeds.fetch_gdelt(client, feed))
        assert calls["n"] == 2
        assert len(items) == 1


class TestFetchAll:
    def test_feed_isolation(self, monkeypatch):
        async def ok(client, feed):
            return [{"id": "1", "source": feed["id"]}]

        async def boom(client, feed):
            raise RuntimeError("exploded")

        monkeypatch.setitem(feeds.FETCHERS, "rss", ok)
        monkeypatch.setitem(feeds.FETCHERS, "gdelt", boom)
        items, errors = asyncio.run(feeds.fetch_all(feeds=[
            {"id": "good", "kind": "rss", "label": "G", "url": "http://x"},
            {"id": "bad", "kind": "gdelt", "label": "B", "url": "http://y"},
        ]))
        assert len(items) == 1
        assert len(errors) == 1
        assert "bad" in errors[0]

    def test_health_recorded(self, monkeypatch):
        async def ok(client, feed):
            return [{"id": "1"}]

        monkeypatch.setitem(feeds.FETCHERS, "rss", ok)
        feeds._HEALTH.clear()
        asyncio.run(feeds.fetch_all(feeds=[{"id": "h", "kind": "rss", "label": "H",
                                            "url": "http://x"}]))
        assert feeds.feed_health()["h"]["ok"] is True
        assert feeds.feed_health()["h"]["items"] == 1
