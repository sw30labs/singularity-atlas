"""Neo4j store: schema, writes, and every query the API needs.

Graph model
    (:Story {id, title, url, source, source_label, summary, published_at,
             salience, ingested_at, origin})        origin: feed|archive
    (:Vector {name, label})
    (:Entity {name, type})                         type: org|person|model|place|tech
    (:Brief  {id, date, text, model, created_at, n_items})
    rels: (Story)-[:ABOUT {score}]->(Vector)
          (Story)-[:MENTIONS]->(Entity)
          (Story)-[:LOCATED {lat, lon}]->(Entity)  -- place entities only
          (Entity)-[:CO_OCCURS {stories}]-(Entity)
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from neo4j import GraphDatabase

from . import config

_driver = None


def driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
    return _driver


def close() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def init_schema() -> None:
    stmts = [
        "CREATE CONSTRAINT story_id IF NOT EXISTS FOR (s:Story) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT vector_name IF NOT EXISTS FOR (v:Vector) REQUIRE v.name IS UNIQUE",
        "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
        "CREATE CONSTRAINT brief_id IF NOT EXISTS FOR (b:Brief) REQUIRE b.id IS UNIQUE",
        "CREATE INDEX story_published IF NOT EXISTS FOR (s:Story) ON (s.published_at)",
    ]
    with driver().session() as s:
        for q in stmts:
            s.run(q)
        for name, meta in config.VECTORS.items():
            s.run("MERGE (v:Vector {name: $name}) SET v.label = $label, v.color = $color",
                  name=name, label=meta["label"], color=meta["color"])


def ping() -> bool:
    try:
        driver().verify_connectivity()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

def upsert_story(tx, item: dict) -> None:
    tx.run(
        """
        MERGE (s:Story {id: $id})
        SET s.title = $title, s.url = $url, s.source = $source,
            s.source_label = $source_label, s.summary = $summary,
            s.published_at = $published_at, s.salience = $salience,
            s.ingested_at = $ingested_at, s.origin = $origin,
            s.extra = $extra
        """,
        id=item["id"], title=item["title"], url=item.get("url", ""),
        source=item["source"], source_label=item.get("source_label", item["source"]),
        summary=item.get("summary", ""), published_at=item.get("published_at"),
        salience=item.get("salience", 0.0),
        ingested_at=datetime.now(timezone.utc).isoformat(),
        origin=item.get("origin", "feed"),
        extra=json.dumps(item.get("extra") or {}),
    )
    for vector, score in (item.get("vectors") or {}).items():
        tx.run(
            """
            MATCH (s:Story {id: $id}), (v:Vector {name: $vector})
            MERGE (s)-[r:ABOUT]->(v) SET r.score = $score
            """,
            id=item["id"], vector=vector, score=score,
        )
    for ent in item.get("entities", []):
        tx.run(
            """
            MATCH (s:Story {id: $id})
            MERGE (e:Entity {name: $name}) SET e.type = $type
            MERGE (s)-[:MENTIONS]->(e)
            """,
            id=item["id"], name=ent["name"], type=ent.get("type", "thing"),
        )
    for pl in item.get("places", []):
        tx.run(
            """
            MATCH (s:Story {id: $id})
            MERGE (e:Entity {name: $name}) SET e.type = 'place'
            MERGE (s)-[r:LOCATED]->(e) SET r.lat = $lat, r.lon = $lon
            """,
            id=item["id"], name=pl["name"], lat=pl.get("lat"), lon=pl.get("lon"),
        )


def persist_items(items: list[dict]) -> int:
    if not items:
        return 0
    with driver().session() as s:
        n = s.execute_write(lambda tx: _persist_tx(tx, items))
    _refresh_cooccurrence()
    return n


def _persist_tx(tx, items: list[dict]) -> int:
    for item in items:
        upsert_story(tx, item)
    return len(items)


def _refresh_cooccurrence() -> None:
    """Rebuild CO_OCCURS edges from recent shared stories (bounded, cheap)."""
    with driver().session() as s:
        s.run(
            """
            MATCH (e1:Entity)<-[:MENTIONS]-(s:Story)-[:MENTIONS]->(e2:Entity)
            WHERE e1.name < e2.name
              AND s.ingested_at > datetime() - duration('P7D')
            WITH e1, e2, count(DISTINCT s) AS n
            MERGE (e1)-[r:CO_OCCURS]-(e2) SET r.stories = n
            """
        )


def save_brief(text: str, model: str, n_items: int, brief_date: str | None = None) -> str:
    d = brief_date or datetime.now(timezone.utc).date().isoformat()
    with driver().session() as s:
        s.run(
            """
            MERGE (b:Brief {id: $id})
            SET b.date = $date, b.text = $text, b.model = $model,
                b.n_items = $n_items, b.created_at = $created
            """,
            id=f"brief-{d}", date=d, text=text, model=model, n_items=n_items,
            created=datetime.now(timezone.utc).isoformat(),
        )
    return d


def _decode_story(st: dict) -> dict:
    """Story dict from the graph with `extra` JSON decoded."""
    raw = st.get("extra")
    if isinstance(raw, str):
        try:
            st["extra"] = json.loads(raw)
        except json.JSONDecodeError:
            st["extra"] = {}
    return st


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------

def recent_stories(hours: int = 48, limit: int = 400) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with driver().session() as s:
        res = s.run(
            """
            MATCH (s:Story)
            WHERE coalesce(s.published_at, s.ingested_at) > $since
            OPTIONAL MATCH (s)-[a:ABOUT]->(v:Vector)
            WITH s, collect({vector: v.name, score: a.score}) AS vecs
            OPTIONAL MATCH (s)-[:MENTIONS]->(e:Entity)
            RETURN s, vecs, collect(e.name) AS entities
            ORDER BY s.salience DESC LIMIT $limit
            """,
            since=since, limit=limit,
        )
        out = []
        for r in res:
            st = _decode_story(dict(r["s"]))
            st["vectors"] = {v["vector"]: v["score"] for v in r["vecs"] if v["vector"]}
            st["entities"] = [e for e in r["entities"] if e]
            out.append(st)
        return out


def vector_signals(hours: int = 72, per_vector: int = 12) -> dict[str, list[dict]]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    out: dict[str, list[dict]] = {v: [] for v in config.VECTOR_NAMES}
    with driver().session() as s:
        for v in config.VECTOR_NAMES:
            res = s.run(
                """
                MATCH (s:Story)-[a:ABOUT]->(v:Vector {name: $v})
                WHERE coalesce(s.published_at, s.ingested_at) > $since
                OPTIONAL MATCH (s)-[:MENTIONS]->(e:Entity)
                WITH s, a, collect(DISTINCT e.name) AS ents
                RETURN s, a.score AS score, ents
                ORDER BY (a.score + s.salience) DESC LIMIT $k
                """,
                v=v, since=since, k=per_vector,
            )
            out[v] = [{**_decode_story(dict(r["s"])), "score": r["score"],
                       "entities": r["ents"]} for r in res]
    return out


def convergence(hours: int = 72, limit: int = 20) -> list[dict]:
    """Entities mentioned by stories about >=2 distinct vectors in the window."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with driver().session() as s:
        res = s.run(
            """
            MATCH (e:Entity)<-[:MENTIONS]-(s:Story)-[:ABOUT]->(v:Vector)
            WHERE coalesce(s.published_at, s.ingested_at) > $since
              AND e.type <> 'thing'
            WITH e, collect(DISTINCT v.name) AS vecs, count(DISTINCT s) AS stories,
                 sum(s.salience) AS heat
            WHERE size(vecs) >= 2
            RETURN e.name AS name, e.type AS type, vecs, stories, heat
            ORDER BY size(vecs) DESC, heat DESC LIMIT $limit
            """,
            since=since, limit=limit,
        )
        return [dict(r) for r in res]


def entity_ego(name: str, hours: int = 168) -> dict:
    """Small ego-network around an entity for the constellation view."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with driver().session() as s:
        nodes: dict[str, dict] = {}
        edges: list[dict] = []
        res = s.run(
            """
            MATCH (e:Entity {name: $name})<-[:MENTIONS]-(s:Story)
            WHERE coalesce(s.published_at, s.ingested_at) > $since
            OPTIONAL MATCH (s)-[:MENTIONS]->(o:Entity)
            RETURN s, collect(o.name) AS others
            ORDER BY s.salience DESC LIMIT 30
            """,
            name=name, since=since,
        )
        for r in res:
            st = r["s"]
            nodes[st["id"]] = {"id": st["id"], "label": st["title"][:60],
                               "kind": "story", "url": st.get("url", "")}
            for o in r["others"]:
                if o and o != name:
                    oid = f"ent-{o}"
                    nodes[oid] = {"id": oid, "label": o, "kind": "entity"}
                    edges.append({"from": st["id"], "to": oid})
                    edges.append({"from": f"ent-{name}", "to": oid})
        return {"nodes": list(nodes.values()), "edges": edges}


def globe_events(hours: int = 72, limit: int = 60) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with driver().session() as s:
        res = s.run(
            """
            MATCH (s:Story)-[l:LOCATED]->(p:Entity)
            WHERE coalesce(s.published_at, s.ingested_at) > $since
            RETURN s.title AS title, s.url AS url, s.salience AS salience,
                   p.name AS place, l.lat AS lat, l.lon AS lon,
                   s.published_at AS published_at
            ORDER BY s.salience DESC LIMIT $limit
            """,
            since=since, limit=limit,
        )
        return [dict(r) for r in res]


def globe_arcs(hours: int = 72, limit: int = 40) -> list[dict]:
    """Arcs between places co-mentioned by the same story (signal flow)."""
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    with driver().session() as s:
        res = s.run(
            """
            MATCH (s:Story)-[l1:LOCATED]->(p1:Entity),
                  (s)-[l2:LOCATED]->(p2:Entity)
            WHERE coalesce(s.published_at, s.ingested_at) > $since
              AND p1.name < p2.name
            WITH p1.name AS from_name, l1.lat AS from_lat, l1.lon AS from_lon,
                 p2.name AS to_name, l2.lat AS to_lat, l2.lon AS to_lon,
                 count(DISTINCT s) AS n
            RETURN from_name, from_lat, from_lon, to_name, to_lat, to_lon, n
            ORDER BY n DESC LIMIT $limit
            """,
            since=since, limit=limit,
        )
        return [dict(r) for r in res]


def upcoming_launches(limit: int = 12) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    with driver().session() as s:
        res = s.run(
            """
            MATCH (s:Story {source: 'launches'})
            WHERE s.published_at > $now
            RETURN s ORDER BY s.published_at ASC LIMIT $limit
            """,
            now=now, limit=limit,
        )
        return [_decode_story(dict(r["s"])) for r in res]


def latest_brief() -> dict | None:
    with driver().session() as s:
        res = s.run(
            "MATCH (b:Brief) RETURN b ORDER BY b.created_at DESC LIMIT 1"
        ).single()
        return dict(res["b"]) if res else None


def brief_history(limit: int = 14) -> list[dict]:
    with driver().session() as s:
        res = s.run(
            "MATCH (b:Brief) RETURN b.date AS date, b.model AS model, "
            "b.n_items AS n_items ORDER BY b.date DESC LIMIT $limit",
            limit=limit,
        )
        return [dict(r) for r in res]


def graph_stats() -> dict:
    with driver().session() as s:
        def c(q):
            return s.run(q).single()[0]
        return {
            "stories": c("MATCH (s:Story) RETURN count(s)"),
            "entities": c("MATCH (e:Entity) RETURN count(e)"),
            "briefs": c("MATCH (b:Brief) RETURN count(b)"),
            "edges": c("MATCH ()-[r]->() RETURN count(r)"),
        }


# ---------------------------------------------------------------------------
# SI history (JSONL on disk — tiny, append-only, survives graph resets)
# ---------------------------------------------------------------------------

def append_si(snapshot: dict) -> None:
    with config.SI_HISTORY_FILE.open("a") as f:
        f.write(json.dumps(snapshot) + "\n")


def si_history(limit: int = 500) -> list[dict]:
    if not config.SI_HISTORY_FILE.exists():
        return []
    lines = config.SI_HISTORY_FILE.read_text().strip().splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
