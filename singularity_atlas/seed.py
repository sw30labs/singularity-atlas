"""One-time seed: push the Loop editions and Moonshot episodes into the graph.

    uv run python -m singularity_atlas.seed
"""

from __future__ import annotations

from . import loop_archive, moonshot_archive, store

_BATCH = 50


def run() -> dict:
    store.init_schema()
    stories = loop_archive.as_stories() + moonshot_archive.as_stories()
    n = 0
    for i in range(0, len(stories), _BATCH):
        n += store.persist_items(stories[i:i + _BATCH])
    stats = store.graph_stats()
    return {"seeded": n, "loop": len(loop_archive.load_issues()),
            "moonshots": len(moonshot_archive.load_episodes()), "graph": stats}


if __name__ == "__main__":
    print(run())
