"""Loop archive: the 218-edition corpus — parsing, search, story conversion.

Skipped if the archive isn't present (fresh clone without ref/).
"""

from __future__ import annotations

import pytest

from singularity_atlas import config, loop_archive as la

pytestmark = pytest.mark.skipif(
    not config.LOOP_ARCHIVE_DIR.exists(),
    reason="loop archive not present",
)


class TestCorpus:
    def test_issue_count_and_order(self):
        issues = la.load_issues()
        assert len(issues) == 218
        assert issues[0]["date"] == "2025-12-11"
        assert issues[-1]["date"] == "2026-08-17"
        editions = [i["edition"] for i in issues]
        assert editions == sorted(editions)

    def test_front_matter_fields(self):
        last = la.load_issues()[-1]
        assert last["edition"] == 218
        assert last["title"] == "Welcome to August 17, 2026"
        assert last["url"].startswith("https://theinnermostloop.substack.com/")
        assert last["word_count"] > 100

    def test_plain_text_strips_markup(self):
        for issue in la.load_issues()[:10]:
            assert "](" not in issue["text"]
            assert "![" not in issue["text"]


class TestSearch:
    def test_ranked_hits(self):
        hits = la.search("orbital data center")
        assert hits
        scores = [h["score"] for h in hits]
        assert scores == sorted(scores, reverse=True)
        assert all("edition" in h and "snippet" in h and "url" in h for h in hits)

    def test_stopword_only_query_empty(self):
        assert la.search("the and for") == []

    def test_entity_editions(self):
        hits = la.entity_editions("OpenAI")
        assert hits
        assert hits[0]["mentions"] >= hits[-1]["mentions"]

    def test_on_this_date(self):
        hit = la.on_this_date("08-17")
        assert hit and hit["edition"] == 218
        assert la.on_this_date("01-01") is not None  # Welcome to 2026
        assert la.on_this_date("13-40") is None


class TestAsStories:
    def test_shape(self):
        stories = la.as_stories()
        assert len(stories) == 218
        s = stories[-1]
        assert s["id"] == "loop-218"
        assert s["origin"] == "archive"
        assert s["source"] == "innermost-loop"
        assert s["published_at"].startswith("2026-08-17")
        assert isinstance(s["vectors"], dict) and s["vectors"]
        assert isinstance(s["entities"], list)
        assert s["salience"] > 0

    def test_vectors_are_known(self):
        from singularity_atlas import config as cfg
        for s in la.as_stories()[:20]:
            assert set(s["vectors"]).issubset(set(cfg.VECTOR_NAMES))
