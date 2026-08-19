"""The Singularity Index (SI): a composite 0-100 proximity score.

Port of worldmonitor's Country Instability Index idea, re-aimed: instead of
country stress, we score how loud each Singularity vector is right now.

Per vector v:
    raw_v   = Σ (1 + salience) over stories about v in the last 24h
    score_v = 100 * raw_v / (raw_v + K)          (bounded, explainable; K=8)
    + convergence bonus: entities crossing ≥2 vectors add heat to the composite.

SI = weighted mean of vector scores (weights in config.VECTORS).

The epoch dial maps SI onto Stross's three parts, and the calendar onto
Kurzweil's 2045. Everything here is a heuristic — transparent by design.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import config, store

K_HALF = 40.0         # half-saturation constant for vector scoring
CONVERGENCE_BONUS = 1.0  # per convergent entity, added to composite pre-clamp


def _epoch(si: float) -> dict:
    if si < 34:
        idx = 0
    elif si < 67:
        idx = 1
    else:
        idx = 2
    e = config.EPOCHS[idx]
    return {"index": idx, "name": e["name"]}


def countdown() -> dict:
    now = datetime.now(timezone.utc)
    target = datetime(config.SINGULARITY_YEAR, 1, 1, tzinfo=timezone.utc)
    days = (target - now).days
    return {"days": days, "years": round(days / 365.25, 2),
            "target": target.date().isoformat()}


def compute_si() -> dict:
    stories = store.recent_stories(hours=24, limit=2000)
    per_vector: dict[str, float] = {v: 0.0 for v in config.VECTOR_NAMES}
    for st in stories:
        for v in (st.get("vectors") or {}):
            if v in per_vector:
                per_vector[v] += 1.0 + float(st.get("salience") or 0.0)

    conv = store.convergence(hours=72, limit=50)
    conv_names = {c["name"] for c in conv}

    vector_scores: dict[str, dict] = {}
    weighted_sum = 0.0
    weight_total = 0.0
    for v, meta in config.VECTORS.items():
        raw = per_vector[v]
        score = 100.0 * raw / (raw + K_HALF)
        vector_scores[v] = {
            "score": round(score, 1),
            "raw": round(raw, 2),
            "label": meta["label"], "color": meta["color"],
            "blurb": meta["blurb"],
        }
        weighted_sum += score * meta["weight"]
        weight_total += meta["weight"]

    composite = weighted_sum / max(weight_total, 1e-9)
    composite += CONVERGENCE_BONUS * min(len(conv_names), 6)
    composite = min(100.0, composite)

    now = datetime.now(timezone.utc)
    snapshot = {
        "ts": now.isoformat(),
        "si": round(composite, 1),
        "epoch": _epoch(composite),
        "countdown": countdown(),
        "vectors": vector_scores,
        "convergent_entities": sorted(conv_names),
        "n_stories_24h": len(stories),
    }

    # delta vs the mean of prior snapshots inside the baseline window.
    # Selected by timestamp, not row count, so the window stays honest if the
    # ingest cadence changes or the scheduler was down for a stretch.
    snapshot["delta"] = _delta_vs_baseline(snapshot["si"], now)

    return snapshot


def _delta_vs_baseline(si: float, now: datetime) -> float:
    """SI minus the mean of prior snapshots within config.SI_BASELINE_DAYS."""
    cutoff = (now - timedelta(days=config.SI_BASELINE_DAYS)).isoformat()
    # Ask for enough rows to span the window at the current cadence, plus slack.
    rows = int(config.SI_BASELINE_DAYS * 24 * 60 / config.INGEST_INTERVAL_MIN) + 8
    recent = [h for h in store.si_history(limit=rows)
              if cutoff <= h.get("ts", "") < now.isoformat()]
    if not recent:
        return 0.0
    mean = sum(h["si"] for h in recent) / len(recent)
    return round(si - mean, 1)
