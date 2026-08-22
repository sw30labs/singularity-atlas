# Graph baseline

Offline snapshot of the Neo4j graph plus the runtime files ingest needs
(`seen.json`, SI history, feed health, Loop fetches). Taken 2026-08-22:
370 feed stories, 220 Loop archive editions.

A fresh clone loads this automatically when the graph is empty
(`./setup_and_run.sh`). To replace a graph that already has stories:

```bash
./scripts/load_baseline.sh --force
```

The payload is `neo4j.dump` (not a `.tar.gz`). GitHub accepts gzip archives,
but a 100 MB file cap and some org rules make an unpacked dump the safer
thing to track. 445 KB. `manifest.txt` has the sha256.
