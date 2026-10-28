# 0008. Keep third-party works out of the repository; Apache-2.0 for original code only

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`22cc0c3`, `261a0d0`, `b246a6d`)

## Context

The Atlas draws on *The Innermost Loop* newsletter (Dr. Alex Wissner-Gross, "no licence granting redistribution has been identified") and *Accelerando* (Charles Stross, CC BY-NC-ND 2.5). Three same-day commits changed how they are handled: "Licence the project Apache 2.0, with attribution and scope carved out", "Stop publishing the Innermost Loop corpus; keep it local only", "Stop publishing Accelerando; keep the local copy gitignored".

## Decision

- `ref/` (local corpus and *Accelerando* copy) and `data/` are gitignored; README says neither work "is in the history". A check of all fetched branches (`git log --all -- ref/`) found no `ref/` paths, which is consistent with that.
- The Apache-2.0 grant covers only the listed original paths; NOTICE records attributions, the worldmonitor (AGPL) inspiration with "No worldmonitor source code is present", and the uncertain licence of the vendored `innermost_loop.py`.
- At runtime, `loop_sync` may fetch the latest 20 editions from the author's public Substack RSS into gitignored `data/loop_issues/`; the full text is used for local search only.
- `.gitignore` also excludes `*.zip` and `.env` (`b39f85a`).
- The UI quotes short lines and links to the author's free edition of *Accelerando*; the lobster glyph is "original to this dashboard".

## Consequences

**Positive**
- The public repo and the public site don't redistribute copyrighted text.
- Licence scope is explicit.

**Negative**
- A fresh clone has an empty archive (tests for the corpus skip); the "218 editions" label in `web/index.html` is hard-coded and doesn't reflect what's actually loaded.
- Keeping full newsletter text locally, even from a public feed, is a legal judgement that isn't verified here (A-005).
- The licence of `innermost_loop.py` is unresolved (A-004).

## Alternatives considered

Shipping the corpus and *Accelerando* in the repo was the earlier state before `261a0d0`/`b246a6d` (as the commit titles say "Stop publishing"). History rewriting isn't evidenced; the current history has no `ref/` paths (unverified for branches never pushed).

## Evidence

- `.gitignore`, `LICENSE`, `NOTICE`, `README.md` § Licence, § Notes; `QUICKSTART.md` § What a clone does not include
- `singularity_atlas/loop_archive.py`, `singularity_atlas/loop_sync.py`, `web/app.js` (lobster drawer)
- Commits `22cc0c3`, `261a0d0`, `b246a6d`, `b39f85a`
