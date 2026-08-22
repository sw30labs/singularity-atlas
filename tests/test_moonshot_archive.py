"""Moonshot archive: JSON+TXT pairs, diarized search, story conversion."""

from __future__ import annotations

from pathlib import Path

import pytest

from singularity_atlas import config, moonshot_archive as ma

FIXTURES = Path(__file__).parent / "fixtures" / "moonshots"


@pytest.fixture()
def moonshots(monkeypatch):
    monkeypatch.setattr(config, "MOONSHOT_DIR", FIXTURES)
    ma.invalidate()
    yield
    ma.invalidate()


class TestPairs:
    def test_loads_json_txt_pairs(self, moonshots):
        eps = ma.load_episodes()
        assert len(eps) == 3
        assert all(ep["has_txt"] for ep in eps)
        ids = {ep["video_id"] for ep in eps}
        assert ids == {"fixtureAAA01", "fixtureBBB02", "fixtureCCC03"}

    def test_order_oldest_first(self, moonshots):
        dates = [ep["date"] for ep in ma.load_episodes()]
        assert dates == sorted(dates)

    def test_empty_without_directory(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config, "MOONSHOT_DIR", tmp_path / "missing")
        ma.invalidate()
        assert ma.load_episodes() == []


class TestSpeakers:
    def test_host_alias_and_unknown_dropped(self, moonshots):
        by_id = {ep["video_id"]: ep for ep in ma.load_episodes()}
        a = by_id["fixtureAAA01"]
        assert a["speakers"] == ["Peter Diamandis", "Alex Wissner-Gross"]
        assert a["guests"] == []
        b = by_id["fixtureBBB02"]
        assert "Peter Diamandis" in b["speakers"]
        assert "Emad Mostaque" in b["speakers"]
        assert "Unknown speaker 1" not in b["speakers"]
        assert b["guests"] == ["Emad Mostaque"]
        c = by_id["fixtureCCC03"]
        assert "Mo Gawdat" in c["guests"]
        assert "Unknown speaker 1" not in c["speakers"]

    def test_title_bleed_guest_cleaned(self):
        assert ma._clean_speaker("Humanoid Robots w／ Emad Mostaque") == "Emad Mostaque"
        assert ma._clean_speaker("Unknown speaker 3") is None
        assert ma._clean_speaker("SPEAKER_00") is None
        assert ma._clean_speaker("Peter H. Diamandis") == "Peter Diamandis"


class TestEpisodeNumber:
    def test_patterns(self):
        assert ma.episode_number("Thing | EP #62") == 62
        assert ma.episode_number("Thing ｜ EP#51") == 51
        assert ma.episode_number("#16 Moonshots and Mindsets") == 16
        assert ma.episode_number("Title | 264") == 264
        assert ma.episode_number("A Meditation About the Future") is None


class TestSearch:
    def test_ranked_hits_keep_speaker(self, moonshots):
        hits = ma.search("OpenAI")
        assert hits
        assert hits[0]["video_id"] == "fixtureAAA01"
        assert hits[0]["speaker"] == "Peter Diamandis"
        assert "OpenAI" in hits[0]["snippet"]
        assert hits[0]["episode"] == 99

    def test_stopword_only_query_empty(self, moonshots):
        assert ma.search("the and for") == []

    def test_entity_episodes_attribute_speaker(self, moonshots):
        hits = ma.entity_episodes("OpenAI")
        assert hits
        assert hits[0]["mentions"] >= 1
        assert "Peter Diamandis" in hits[0]["speakers"]

    def test_latest_and_on_this_date(self, moonshots):
        latest = ma.latest()
        assert latest and latest["video_id"] == "fixtureCCC03"
        hit = ma.on_this_date("08-01")
        assert hit and hit["episode"] == 99
        assert ma.on_this_date("13-40") is None


class TestAds:
    def test_blitzy_and_fountain_stripped(self, moonshots):
        ep = {e["video_id"]: e for e in ma.load_episodes()}["fixtureCCC03"]
        body = ep["content_text"].lower()
        assert "blitzy" not in body
        assert "fountainlife.com" not in body
        assert "infinite code context" not in body
        assert "agi will be here by 2027" in body
        assert "openai is not the only lab" in body
        brands = {s["brand"] for s in ep["ad_spans"]}
        assert "blitzy" in brands or "fountain_life" in brands
        assert ep["ad_fraction"] > 0.2

    def test_search_skips_ad_copy(self, moonshots):
        assert ma.search("Blitzy") == []
        hits = ma.search("OpenAI")
        assert hits
        assert all("blitzy" not in (h.get("snippet") or "").lower() for h in hits)


class TestForecasts:
    def test_guest_own_year(self, moonshots):
        from singularity_atlas import moonshot_forecasts as mf
        mf.invalidate()
        rows = mf.load_forecasts()
        agi = [r for r in rows if r["speaker"] == "Mo Gawdat" and r["year"] == 2027]
        assert agi
        assert agi[0]["role"] == "guest"
        assert agi[0]["attribution"] == "own"
        led = mf.summary()
        assert led["n"] >= 1
        assert led["guest_median"] == 2027


class TestMix:
    def test_monthly_shares(self, moonshots):
        mix = ma.vector_mix()
        months = {m["month"] for m in mix}
        assert "2026-08" in months
        for row in mix:
            total = sum(row["shares"].values())
            assert total == pytest.approx(1.0, abs=0.02)
        shares = ma.prior_shares(days=400)
        assert set(shares) == set(config.VECTOR_NAMES)
        assert "Mo Gawdat" in ma.known_guests()
        assert "Mo Gawdat" in ma.recent_guests(days=30)
        # seating-chart hit even when the surname is never spoken
        seated = ma.entity_episodes("Mo Gawdat")
        assert seated and seated[0]["video_id"] == "fixtureCCC03"


class TestArchiveMerge:
    def test_interleave_does_not_drown_the_loop(self, moonshots, monkeypatch):
        from singularity_atlas import api, loop_archive
        monkeypatch.setattr(loop_archive, "search", lambda q, limit=8: [
            {"title": "loop-hit", "score": 9, "edition": 1, "date": "2026-01-01",
             "url": "https://example.com/loop", "snippet": "s"}
        ])
        hits = api._archive_search("OpenAI", limit=8)
        sources = [h["source"] for h in hits]
        assert "loop" in sources and "moonshot" in sources
        assert set(sources[:2]) == {"loop", "moonshot"}


class TestAsStories:
    def test_shape(self, moonshots):
        stories = ma.as_stories()
        assert len(stories) == 3
        by_id = {s["id"]: s for s in stories}
        s = by_id["moonshot-fixtureAAA01"]
        assert s["origin"] == "moonshot"
        assert s["source"] == "moonshots"
        assert s["published_at"].startswith("2026-08-01")
        assert s["url"].endswith("fixtureAAA01")
        names = {e["name"] for e in s["entities"]}
        assert "OpenAI" in names
        assert "Peter Diamandis" not in names
        assert "Alex Wissner-Gross" in names
        assert s["extra"]["speakers"][0] == "Peter Diamandis"
        assert s["salience"] > 0

    def test_vectors_are_known(self, moonshots):
        for s in ma.as_stories():
            assert set(s["vectors"]).issubset(set(config.VECTOR_NAMES))


@pytest.mark.skipif(
    not (config.ROOT / "transcriptions_moonshot").is_dir()
    or not any((config.ROOT / "transcriptions_moonshot").glob("*.json")),
    reason="moonshot transcripts not present",
)
class TestRealCorpus:
    def test_pair_count(self, monkeypatch):
        monkeypatch.setattr(config, "MOONSHOT_DIR", config.ROOT / "transcriptions_moonshot")
        monkeypatch.setattr(
            config, "MOONSHOT_DATES_FILE",
            Path(ma.__file__).resolve().parent / "moonshot_dates.json",
        )
        ma.invalidate()
        eps = ma.load_episodes()
        assert len(eps) >= 200
        assert sum(1 for e in eps if e["has_txt"]) == len(eps)
        assert sum(1 for e in eps if e["date"]) >= 200
