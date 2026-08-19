"""Loop sync: dating rule, corpus-shaped output, dedupe, and failure handling.

Offline throughout — the feed fetcher is stubbed, so these exercise loop_sync's
own logic rather than re-testing innermost_loop (see test_innermost_loop.py).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from singularity_atlas import config, innermost_loop, loop_archive, loop_sync

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def _issue(title, slug, published_at, body="Compute scaled again today."):
    """A feed item in the shape innermost_loop.fetch_latest_newsletters returns."""
    return {
        "title": title,
        "slug": slug,
        "guid": f"https://theinnermostloop.substack.com/p/{slug}",
        "url": f"https://theinnermostloop.substack.com/p/{slug}",
        "author": "Dr. Alex Wissner-Gross",
        "published_at": published_at,
        "description": "A short standfirst.",
        "cover_image_url": None,
        "audio_url": None,
        "body_html": f"<p>{body}</p>",
        "body_text": body,
    }


@pytest.fixture()
def archive_dir(tmp_path, monkeypatch):
    """An empty stand-in for the shipped ref/ corpus."""
    d = tmp_path / "shipped"
    d.mkdir()
    monkeypatch.setattr(config, "LOOP_ARCHIVE_DIR", d)
    loop_archive.invalidate()
    return d


def _stub_feed(monkeypatch, issues):
    monkeypatch.setattr(loop_sync.innermost_loop, "fetch_latest_newsletters",
                        lambda *a, **k: issues)


class TestIssueDate:
    def test_title_is_authoritative_over_pubdate(self):
        """Edition 218 shipped as 2026-08-17 but the feed published it 08-18."""
        date, basis = loop_sync.issue_date(
            "Welcome to August 17, 2026", "2026-08-18T01:36:03+00:00")
        assert (date, basis) == ("2026-08-17", "title")

    def test_non_date_title_falls_back_to_pubdate(self):
        date, basis = loop_sync.issue_date(
            "A Conversation with Ray Kurzweil", "2026-01-23T09:00:00+00:00")
        assert (date, basis) == ("2026-01-23", "published_at")

    def test_unparseable_month_falls_back(self):
        date, basis = loop_sync.issue_date(
            "Welcome to Smarch 40, 2026", "2026-03-02T09:00:00+00:00")
        assert (date, basis) == ("2026-03-02", "published_at")

    def test_reproduces_the_shipped_corpus(self):
        """The rule must match how the 218 shipped editions were dated."""
        issues = loop_archive._read_dir(config.LOOP_ARCHIVE_DIR)
        if not issues:
            pytest.skip("shipped corpus not present")
        for it in issues:
            raw = f"{it['title']}"
            # front matter keeps the published_at we would have fetched
            assert loop_sync.issue_date(raw, it["date"] + "T00:00:00+00:00")[0] \
                == it["date"], it["title"]


class TestSync:
    def test_writes_new_editions_in_corpus_format(self, archive_dir, monkeypatch):
        _stub_feed(monkeypatch, [_issue("Welcome to August 19, 2026",
                                        "welcome-to-august-19-2026",
                                        "2026-08-20T01:00:00+00:00")])
        result = loop_sync.sync(now=NOW)
        assert result["new"] == 1 and result["error"] is None

        written = list(config.LOOP_FETCH_DIR.glob("*.md"))
        assert len(written) == 1
        # named by issue date, not publication date
        assert written[0].name == "001--2026-08-19--welcome-to-august-19-2026.md"

    def test_output_round_trips_through_the_archive_parser(self, archive_dir,
                                                           monkeypatch):
        """What we write must be readable by loop_archive, or search breaks."""
        _stub_feed(monkeypatch, [_issue("Welcome to August 19, 2026",
                                        "welcome-to-august-19-2026",
                                        "2026-08-20T01:00:00+00:00",
                                        body="Fusion ignition milestone today.")])
        loop_sync.sync(now=NOW)
        loop_archive.invalidate()

        issues = loop_archive.load_issues()
        assert len(issues) == 1
        it = issues[0]
        assert it["edition"] == 1
        assert it["date"] == "2026-08-19"
        assert it["title"] == "Welcome to August 19, 2026"
        assert it["slug"] == "welcome-to-august-19-2026"
        assert it["url"].endswith("/welcome-to-august-19-2026")
        assert it["word_count"] == 4
        assert "Fusion ignition" in it["text"]

    def test_skips_editions_already_in_the_archive(self, archive_dir, monkeypatch):
        issue = _issue("Welcome to August 19, 2026", "welcome-to-august-19-2026",
                       "2026-08-20T01:00:00+00:00")
        _stub_feed(monkeypatch, [issue])
        assert loop_sync.sync(now=NOW)["new"] == 1
        loop_archive.invalidate()
        # same feed again -> nothing new, no duplicate file
        assert loop_sync.sync(now=NOW)["new"] == 0
        assert len(list(config.LOOP_FETCH_DIR.glob("*.md"))) == 1

    def test_numbers_editions_in_publication_order(self, archive_dir, monkeypatch):
        # feed order is newest-first; editions must still ascend with time
        _stub_feed(monkeypatch, [
            _issue("Welcome to August 20, 2026", "welcome-to-august-20-2026",
                   "2026-08-21T01:00:00+00:00"),
            _issue("Welcome to August 19, 2026", "welcome-to-august-19-2026",
                   "2026-08-20T01:00:00+00:00"),
        ])
        result = loop_sync.sync(now=NOW)
        assert [i["edition"] for i in result["issues"]] == [1, 2]
        assert [i["date"] for i in result["issues"]] == ["2026-08-19", "2026-08-20"]

    def test_continues_numbering_from_the_shipped_corpus(self, archive_dir,
                                                         monkeypatch):
        (archive_dir / "218--2026-08-17--welcome-to-august-17-2026.md").write_text(
            '---\nedition_number: 218\nissue_date: "2026-08-17"\n'
            'title: "Welcome to August 17, 2026"\n'
            'source_url: "https://theinnermostloop.substack.com/p/'
            'welcome-to-august-17-2026"\ndescription: "x"\nword_count: 3\n---\n\nbody\n',
            encoding="utf-8")
        loop_archive.invalidate()
        _stub_feed(monkeypatch, [_issue("Welcome to August 19, 2026",
                                        "welcome-to-august-19-2026",
                                        "2026-08-20T01:00:00+00:00")])
        assert loop_sync.sync(now=NOW)["issues"][0]["edition"] == 219

    def test_feed_failure_is_recorded_not_raised(self, archive_dir, monkeypatch):
        def boom(*a, **k):
            raise innermost_loop.NewsletterFetchError("HTTP 503 while fetching")
        monkeypatch.setattr(loop_sync.innermost_loop,
                            "fetch_latest_newsletters", boom)
        result = loop_sync.sync(now=NOW)
        assert result["new"] == 0
        assert "503" in result["error"]
        # the failure is still a check, so state records when we looked
        assert loop_sync.last_sync()["checked_at"] == NOW.isoformat()


class TestDue:
    def test_due_when_never_synced(self):
        assert loop_sync.due(NOW) is True

    def test_not_due_within_the_interval(self, archive_dir, monkeypatch):
        _stub_feed(monkeypatch, [])
        loop_sync.sync(now=NOW)
        assert loop_sync.due(NOW + timedelta(hours=1)) is False

    def test_due_again_after_the_interval(self, archive_dir, monkeypatch):
        _stub_feed(monkeypatch, [])
        loop_sync.sync(now=NOW)
        later = NOW + timedelta(hours=config.LOOP_SYNC_INTERVAL_H, minutes=1)
        assert loop_sync.due(later) is True


class TestSyncAndPersist:
    def test_persists_only_the_new_editions(self, archive_dir, monkeypatch):
        _stub_feed(monkeypatch, [_issue("Welcome to August 19, 2026",
                                        "welcome-to-august-19-2026",
                                        "2026-08-20T01:00:00+00:00")])
        seen = {}

        class FakeStore:
            def persist_items(self, stories):
                seen["stories"] = stories
                return len(stories)

        result = loop_sync.sync_and_persist(FakeStore(), now=NOW)
        assert result["persisted"] == 1
        story = seen["stories"][0]
        assert story["id"] == "loop-001"
        assert story["origin"] == "archive"
        assert story["source"] == "innermost-loop"

    def test_nothing_persisted_when_nothing_new(self, archive_dir, monkeypatch):
        _stub_feed(monkeypatch, [])

        class FakeStore:
            def persist_items(self, stories):  # pragma: no cover - must not run
                raise AssertionError("persist_items called with no new editions")

        assert loop_sync.sync_and_persist(FakeStore(), now=NOW)["persisted"] == 0
