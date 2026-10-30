# 0007. Use only public, no-auth, no-registration data sources

- **Status:** Accepted, retrospective, inferred 2026-10-28
- **Date of decision (from history):** 2026-08-19 (`ed3300c`)

## Context

README and QUICKSTART repeat "No API keys, no registration. Feeds are public." `config.py`: "Feeds — all verified reachable, none require auth or registration."

## Decision

`config.FEEDS` holds 15 sources of five kinds (`rss`, `arxiv`, `hn`, `launches`, `gdelt`): arXiv cs.AI/LG/CL/RO, OpenAI, Google DeepMind, Import AI, Interconnects, MIT Tech Review, Ars Technica, The Verge, VentureBeat, Hacker News (Algolia, min 60 points), Launch Library 2.2.0, GDELT DOC API. Each feed carries `vectors` hints. The globe's infrastructure sites (`GLOBE_SITES`) are a hand-curated list in code. A fixed `User-Agent` identifies the app.

## Consequences

**Positive**
- Anyone can clone and run without accounts or secrets; nothing to leak.

**Negative**
- Coverage is limited to what these feeds expose (RSS excerpts, top-12 arXiv per category, etc.).
- Public endpoints can change or rate-limit without notice (GDELT 429 handling exists).
- `GLOBE_SITES` (datacenters, fabs, labs, pads) is static and will go stale.
- The `USER_AGENT` contact URL is `https://localhost/singularity-atlas`, which isn't reachable for feed operators (A-015).

## Alternatives considered

Authenticated APIs were implicitly rejected; no record of specific ones.

## Evidence

- `singularity_atlas/config.py` (`FEEDS`, `GLOBE_SITES`, `USER_AGENT`), `singularity_atlas/feeds.py`
- `README.md`, `QUICKSTART.md`, `NOTICE` (public data sources)
- Commit `ed3300c`
