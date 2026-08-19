"""FastAPI surface: one dashboard payload + focused endpoints + static app.

    uv run uvicorn singularity_atlas.api:app --host 127.0.0.1 --port 8055
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import (config, feeds, llm, loop_archive, loop_sync, scheduler,
               scoring, store)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.stop()
    store.close()


app = FastAPI(title="The Singularity Atlas", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/state")
def api_state() -> dict:
    """The one-shot payload the frontend polls."""
    hist = store.si_history(limit=200)
    current = hist[-1] if hist else scoring.compute_si()
    return {
        "si": current,
        "si_history": [{"ts": h["ts"], "si": h["si"]} for h in hist],
        "vectors": config.VECTORS,
        "signals": store.vector_signals(hours=config.SIGNAL_WINDOW_H, per_vector=10),
        "convergence": store.convergence(hours=config.SIGNAL_WINDOW_H, limit=14),
        "brief": store.latest_brief(),
        "feeds": feeds.feed_health(),
        "graph": store.graph_stats(),
        "llm": {"available": llm.available(), "preferred": config.OLLAMA_MODEL,
                "active": llm.current_model()},
        "quotes": config.ACCELERANDO_QUOTES,
        "si_baseline_days": config.SI_BASELINE_DAYS,
        "on_this_date": loop_archive.on_this_date(),
        "loop_sync": loop_sync.last_sync(),
        "last_ingest": scheduler.last_run(),
        "ingest_running": scheduler.ingest_running(),
    }


@app.get("/api/si")
def api_si() -> dict:
    hist = store.si_history()
    return {"history": hist,
            "current": hist[-1] if hist else scoring.compute_si(),
            "epochs": config.EPOCHS, "singularity_year": config.SINGULARITY_YEAR}


@app.get("/api/signals")
def api_signals(vector: str = Query("capability"), hours: int = 72, limit: int = 25) -> dict:
    sig = store.vector_signals(hours=hours, per_vector=limit)
    return {"vector": vector, "stories": sig.get(vector, [])}


@app.get("/api/convergence")
def api_convergence(hours: int = 72) -> dict:
    return {"convergence": store.convergence(hours=hours, limit=30)}


@app.get("/api/graph")
def api_graph(entity: str = Query(...)) -> dict:
    ego = store.entity_ego(entity)
    ego["loop_editions"] = loop_archive.entity_editions(entity)
    return ego


# ---------------------------------------------------------------------------
# Brief
# ---------------------------------------------------------------------------

@app.get("/api/brief")
def api_brief() -> dict:
    return {"brief": store.latest_brief(), "history": store.brief_history()}


@app.get("/api/ingest")
def api_ingest_status() -> dict:
    return {"running": scheduler.ingest_running(), "last": scheduler.last_run()}


@app.post("/api/ingest")
def api_ingest() -> dict:
    return scheduler.run_ingest_safe()


@app.post("/api/brief/regenerate")
def api_brief_regen() -> dict:
    from . import pipeline
    return pipeline.run_brief_only()


# ---------------------------------------------------------------------------
# Globe
# ---------------------------------------------------------------------------

@app.get("/api/globe")
def api_globe() -> dict:
    return {
        "sites": config.GLOBE_SITES,
        "events": store.globe_events(hours=config.SIGNAL_WINDOW_H),
        "arcs": store.globe_arcs(hours=config.SIGNAL_WINDOW_H),
        "launches": store.upcoming_launches(),
    }


# ---------------------------------------------------------------------------
# Loop archive
# ---------------------------------------------------------------------------

@app.get("/api/archive/search")
def api_archive_search(q: str = Query(..., min_length=2)) -> dict:
    return {"q": q, "hits": loop_archive.search(q)}


@app.get("/api/archive/entity")
def api_archive_entity(name: str = Query(...)) -> dict:
    return {"entity": name, "editions": loop_archive.entity_editions(name, limit=10)}


@app.post("/api/archive/sync")
def api_archive_sync() -> dict:
    """Pull any new editions now, instead of waiting for the daily job."""
    return scheduler.run_loop_sync_safe()


@app.get("/api/feeds")
def api_feeds() -> dict:
    return {"feeds": feeds.feed_health(), "configured": [
        {"id": f["id"], "label": f["label"], "kind": f["kind"]} for f in config.FEEDS
    ]}


# ---------------------------------------------------------------------------
# Static app
# ---------------------------------------------------------------------------

@app.get("/")
def index() -> FileResponse:
    return FileResponse(config.WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=config.WEB_DIR), name="static")
