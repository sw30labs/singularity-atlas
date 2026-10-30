# 0006. The Singularity Index is a transparent, bounded heuristic composite

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`, baseline fix `51f13b5`)

## Context

The headline number (0–100) and the "Slow Takeoff → Point of Inflexion → Singularity" dial reimplement "the idea behind worldmonitor's Country Instability Index (no code in common)". The module says: "Everything here is a heuristic — transparent by design."

## Decision

- Per vector: `raw_v = Σ (1 + salience)` over stories about v in the last 24 h; `score_v = 100 · raw_v / (raw_v + K_HALF)` with `K_HALF = 40.0`.
- Composite = weighted mean using weights in `config.VECTORS` (capability 0.18, compute 0.16, agency 0.14, capital/embodiment/security 0.12, space/culture 0.08; a test asserts they sum to 1), plus `CONVERGENCE_BONUS = 1.0` per convergent entity (max 6), clamped to 100.
- Epochs: SI < 34, < 67, ≥ 67; calendar mapping 2015–2029 / 2030–2039 / 2040–2045; countdown to 2045-01-01 (Kurzweil).
- Delta = SI minus the mean of snapshots within `SI_BASELINE_DAYS = 7`, **selected by timestamp, not row count**. `51f13b5` fixed a bug where the label said 7 d but the code averaged ~14 h.
- Every snapshot is appended to `data/si_history.jsonl`.

## Consequences

**Positive**
- Explainable, deterministic, unit-tested (`tests/test_scoring.py`).
- Bounded per-vector score avoids one noisy feed dominating.

**Negative**
- The index measures news *volume and salience*, not progress; feed mix and cadence move it directly.
- Weights, `K_HALF`, bonus and thresholds are uncalibrated judgement calls (A-008).
- The docstring in `scoring.py` still says `K=8` while the code uses `K_HALF = 40.0` (A-001).
- The convergence bonus uses a 72 h window while vector scores use 24 h.

## Alternatives considered

None recorded beyond the worldmonitor inspiration.

## Evidence

- `singularity_atlas/scoring.py`, `singularity_atlas/config.py` (`VECTORS`, `EPOCHS`, `SINGULARITY_YEAR`, `SI_BASELINE_DAYS`)
- `tests/test_scoring.py`
- `NOTICE` § Acknowledgements
- Commits `ed3300c`, `51f13b5`
