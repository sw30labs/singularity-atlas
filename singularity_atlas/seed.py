"""One-time seed: push the 218 Innermost Loop editions into the graph.

    uv run python -m singularity_atlas.seed
"""

from __future__ import annotations

from . import loop_archive, store


def run() -> dict:
    store.init_schema()
    stories = loop_archive.as_stories()
    n = store.persist_items(stories)
    stats = store.graph_stats()
    return {"seeded": n, "graph": stats}


if __name__ == "__main__":
    print(run())
