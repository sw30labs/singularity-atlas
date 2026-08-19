import unittest
from http.client import IncompleteRead
from unittest.mock import patch
from urllib.error import URLError

from singularity_atlas import innermost_loop

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:content="http://purl.org/rss/1.0/modules/content/" version="2.0">
  <channel>
    <title>The Innermost Loop</title>
    <item>
      <title>Older issue</title>
      <description>Older description</description>
      <link>https://theinnermostloop.substack.com/p/older</link>
      <guid>older-guid</guid>
      <dc:creator>Dr. Alex Wissner-Gross</dc:creator>
      <pubDate>Mon, 17 Aug 2026 01:00:00 GMT</pubDate>
      <content:encoded><![CDATA[<p>Older body.</p>]]></content:encoded>
    </item>
    <item>
      <title>Newest — issue</title>
      <description><![CDATA[The <em>latest</em> description.]]></description>
      <link>https://theinnermostloop.substack.com/p/newest</link>
      <guid>newest-guid</guid>
      <dc:creator>Dr. Alex Wissner-Gross</dc:creator>
      <pubDate>Tue, 18 Aug 2026 01:36:03 GMT</pubDate>
      <enclosure url="https://example.test/cover.jpg" type="image/jpeg" />
      <content:encoded><![CDATA[
        <p>Hello <strong>world</strong>.</p>
        <div class="subscription-widget-wrap-editor"><p>Subscribe noise.</p></div>
        <p>After the widget.</p>
        <button><svg><path>Interface noise</path></svg></button>
      ]]></content:encoded>
    </item>
    <item>
      <title>Duplicate newest issue</title>
      <description>Duplicate</description>
      <link>https://theinnermostloop.substack.com/p/newest-copy</link>
      <guid>newest-guid</guid>
      <dc:creator>Dr. Alex Wissner-Gross</dc:creator>
      <pubDate>Tue, 18 Aug 2026 01:36:03 GMT</pubDate>
      <content:encoded><![CDATA[<p>Duplicate body.</p>]]></content:encoded>
    </item>
  </channel>
</rss>
""".encode()


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self, _limit=-1):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FetchLatestNewslettersTests(unittest.TestCase):
    @patch("singularity_atlas.innermost_loop.urlopen", return_value=FakeResponse(FEED))
    def test_returns_newest_full_issue_and_cleans_text(self, mocked_urlopen):
        issues = innermost_loop.fetch_latest_newsletters(limit=1)

        self.assertEqual(len(issues), 1)
        issue = issues[0]
        self.assertEqual(issue["title"], "Newest — issue")
        self.assertEqual(issue["slug"], "newest")
        self.assertEqual(issue["guid"], "newest-guid")
        self.assertEqual(issue["published_at"], "2026-08-18T01:36:03+00:00")
        self.assertEqual(issue["description"], "The latest description.")
        self.assertEqual(issue["cover_image_url"], "https://example.test/cover.jpg")
        self.assertIn("subscription-widget", issue["body_html"])
        self.assertIn("Hello world.", issue["body_text"])
        self.assertIn("After the widget.", issue["body_text"])
        self.assertNotIn("Subscribe noise", issue["body_text"])
        self.assertNotIn("Interface noise", issue["body_text"])
        request = mocked_urlopen.call_args.args[0]
        self.assertIn("InnermostLoopFetcher", request.get_header("User-agent"))

    @patch("singularity_atlas.innermost_loop.urlopen", return_value=FakeResponse(FEED))
    def test_sorts_and_deduplicates(self, _mocked_urlopen):
        issues = innermost_loop.fetch_latest_newsletters(limit=10)
        self.assertEqual(
            [issue["guid"] for issue in issues], ["newest-guid", "older-guid"]
        )

    @patch("singularity_atlas.innermost_loop.urlopen")
    def test_sorts_mixed_timezone_offsets_by_actual_instant(self, mocked_urlopen):
        mixed_offsets = FEED.replace(
            b"Mon, 17 Aug 2026 01:00:00 GMT",
            b"Tue, 18 Aug 2026 00:30:00 -0500",
        ).replace(
            b"Tue, 18 Aug 2026 01:36:03 GMT",
            b"Tue, 18 Aug 2026 04:00:00 +0000",
        )
        mocked_urlopen.return_value = FakeResponse(mixed_offsets)

        issues = innermost_loop.fetch_latest_newsletters(limit=10)

        self.assertEqual(issues[0]["title"], "Older issue")
        self.assertEqual(issues[0]["published_at"], "2026-08-18T05:30:00+00:00")

    @patch("singularity_atlas.innermost_loop.time.sleep")
    @patch(
        "singularity_atlas.innermost_loop.urlopen",
        side_effect=[URLError("temporary"), FakeResponse(FEED)],
    )
    def test_retries_transient_network_error(self, mocked_urlopen, mocked_sleep):
        issues = innermost_loop.fetch_latest_newsletters(limit=1, retries=1)
        self.assertEqual(issues[0]["guid"], "newest-guid")
        self.assertEqual(mocked_urlopen.call_count, 2)
        mocked_sleep.assert_called_once()

    @patch("singularity_atlas.innermost_loop.time.sleep")
    @patch(
        "singularity_atlas.innermost_loop.urlopen",
        side_effect=[IncompleteRead(b"partial", 100), FakeResponse(FEED)],
    )
    def test_retries_truncated_http_response(self, mocked_urlopen, mocked_sleep):
        issues = innermost_loop.fetch_latest_newsletters(limit=1, retries=1)
        self.assertEqual(issues[0]["guid"], "newest-guid")
        self.assertEqual(mocked_urlopen.call_count, 2)
        mocked_sleep.assert_called_once()

    @patch("singularity_atlas.innermost_loop.urlopen")
    def test_zero_limit_does_not_use_network(self, mocked_urlopen):
        self.assertEqual(innermost_loop.fetch_latest_newsletters(limit=0), [])
        mocked_urlopen.assert_not_called()

    def test_rejects_invalid_arguments(self):
        for bad_limit in (-1, 1.5, True, "1"):
            with self.subTest(limit=bad_limit), self.assertRaises(ValueError):
                innermost_loop.fetch_latest_newsletters(limit=bad_limit)
        for bad_timeout in (0, -1, float("inf"), float("nan"), True):
            with self.subTest(timeout=bad_timeout), self.assertRaises(ValueError):
                innermost_loop.fetch_latest_newsletters(timeout=bad_timeout)
        with self.assertRaises(ValueError):
            innermost_loop.fetch_latest_newsletters(user_agent="bad\r\nheader")
        with self.assertRaises(ValueError):
            innermost_loop.fetch_latest_newsletters(feed_url="not-a-url")

    @patch("singularity_atlas.innermost_loop.urlopen", return_value=FakeResponse(b"not xml"))
    def test_rejects_malformed_feed(self, _mocked_urlopen):
        with self.assertRaises(innermost_loop.NewsletterFetchError):
            innermost_loop.fetch_latest_newsletters()


if __name__ == "__main__":
    unittest.main()
