"""Scoring: epoch mapping, countdown, and the composite SI with a mocked store."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from singularity_atlas import config, scoring


class TestEpoch:
    @pytest.mark.parametrize("si,idx", [(0, 0), (33.9, 0), (34, 1), (66.9, 1),
                                        (67, 2), (100, 2)])
    def test_boundaries(self, si, idx):
        assert scoring._epoch(si)["index"] == idx
        assert scoring._epoch(si)["name"] == config.EPOCHS[idx]["name"]


class TestCountdown:
    def test_target(self):
        cd = scoring.countdown()
        assert cd["target"] == f"{config.SINGULARITY_YEAR}-01-01"
        assert cd["days"] > 0
        assert cd["years"] == pytest.approx(cd["days"] / 365.25, abs=0.01)

    def test_countdown_decreases(self):
        # sanity: today is closer to 2045 than the project's epoch start was
        now = datetime.now(timezone.utc)
        assert now < datetime(config.SINGULARITY_YEAR, 1, 1, tzinfo=timezone.utc)


def _story(vectors: dict, salience: float = 1.0) -> dict:
    return {"id": "x", "vectors": vectors, "salience": salience}


class TestComputeSI:
    def _patch_store(self, monkeypatch, stories, conv=None, history=None):
        monkeypatch.setattr(scoring.store, "recent_stories", lambda **k: stories)
        monkeypatch.setattr(scoring.store, "convergence", lambda **k: conv or [])
        monkeypatch.setattr(scoring.store, "si_history", lambda *a, **k: history or [])

    def test_empty_world(self, monkeypatch):
        self._patch_store(monkeypatch, stories=[])
        si = scoring.compute_si()
        assert si["si"] == 0.0
        assert si["epoch"]["index"] == 0
        assert si["delta"] == 0.0
        assert set(si["vectors"].keys()) == set(config.VECTOR_NAMES)

    def test_saturated_world(self, monkeypatch):
        stories = [_story({v: 1.0}, salience=50.0)
                   for v in config.VECTOR_NAMES for _ in range(100)]
        self._patch_store(monkeypatch, stories=stories,
                          conv=[{"name": f"E{i}"} for i in range(20)])
        si = scoring.compute_si()
        assert si["si"] == pytest.approx(100.0)
        assert si["epoch"]["index"] == 2
        assert len(si["convergent_entities"]) == 20

    def test_weighted_composite(self, monkeypatch):
        # one story per vector with equal salience → score follows raw formula
        stories = [_story({v: 1.0}, salience=1.0) for v in config.VECTOR_NAMES]
        self._patch_store(monkeypatch, stories=stories)
        si = scoring.compute_si()
        expected_per = 100.0 * 2.0 / (2.0 + scoring.K_HALF)
        weighted = sum(expected_per * m["weight"] for m in config.VECTORS.values())
        assert si["si"] == pytest.approx(min(100.0, weighted), abs=0.1)
        for v in config.VECTOR_NAMES:
            assert si["vectors"][v]["score"] == pytest.approx(expected_per, abs=0.05)

    def test_convergence_bonus_capped(self, monkeypatch):
        self._patch_store(monkeypatch, stories=[],
                          conv=[{"name": f"E{i}"} for i in range(50)])
        si = scoring.compute_si()
        # zero volume + capped bonus (6 * 1.0)
        assert si["si"] == pytest.approx(6 * scoring.CONVERGENCE_BONUS, abs=0.05)

    def test_delta_vs_history(self, monkeypatch):
        now = datetime.now(timezone.utc)
        self._patch_store(monkeypatch, stories=[], history=[
            {"ts": (now - timedelta(days=2)).isoformat(), "si": 10.0},
            {"ts": (now - timedelta(days=1)).isoformat(), "si": 20.0},
        ])
        si = scoring.compute_si()
        assert si["delta"] == pytest.approx(0.0 - 15.0, abs=0.05)

    def test_delta_ignores_snapshots_older_than_baseline_window(self, monkeypatch):
        """Snapshots outside config.SI_BASELINE_DAYS must not skew the mean."""
        now = datetime.now(timezone.utc)
        stale = now - timedelta(days=config.SI_BASELINE_DAYS + 3)
        self._patch_store(monkeypatch, stories=[], history=[
            {"ts": stale.isoformat(), "si": 99.0},                      # too old
            {"ts": (now - timedelta(hours=6)).isoformat(), "si": 20.0},  # in window
        ])
        si = scoring.compute_si()
        # only the 20.0 snapshot counts; the 99.0 outlier is out of window
        assert si["delta"] == pytest.approx(0.0 - 20.0, abs=0.05)

    def test_delta_zero_when_all_history_is_stale(self, monkeypatch):
        now = datetime.now(timezone.utc)
        stale = now - timedelta(days=config.SI_BASELINE_DAYS + 1)
        self._patch_store(monkeypatch, stories=[],
                          history=[{"ts": stale.isoformat(), "si": 50.0}])
        si = scoring.compute_si()
        assert si["delta"] == 0.0

    def test_prior_skipped_without_corpus(self, monkeypatch):
        self._patch_store(monkeypatch, stories=[])
        si = scoring.compute_si()
        assert si["si"] == 0.0
        assert si["prior"]["alpha"] == 0.0 or si["prior"]["prior"] is None

    def test_prior_clamped(self, monkeypatch):
        from singularity_atlas import moonshot_archive as ma
        monkeypatch.setattr(config, "MOONSHOT_PRIOR_ALPHA", 0.5)
        monkeypatch.setattr(config, "MOONSHOT_PRIOR_CLAMP", 3.0)
        monkeypatch.setattr(ma, "load_episodes", lambda: [{"date": "2026-08-01"}])
        monkeypatch.setattr(ma, "prior_shares", lambda days=None: {
            v: 1.0 / len(config.VECTOR_NAMES) for v in config.VECTOR_NAMES
        })
        monkeypatch.setattr(ma, "recent_guests", lambda days=14: [])
        self._patch_store(monkeypatch, stories=[])
        si = scoring.compute_si()
        # feed SI is 0; 50% mix toward ~12.5 would be 6.25, clamped to 3
        assert si["si"] == pytest.approx(3.0, abs=0.05)
        assert si["prior"]["clamped"] is True

    def test_weights_sum_to_one(self):
        total = sum(m["weight"] for m in config.VECTORS.values())
        assert total == pytest.approx(1.0)
