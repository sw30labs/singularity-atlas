"""Moonshot archive: the Peter Diamandis podcast as a searchable,
graph-seedable corpus of local transcripts.

Each episode is a JSON + TXT pair under ``transcriptions_moonshot/``
(not in version control — third-party). The JSON holds Whisper text plus
speaker-diarized segments; the TXT is the same transcript as timestamped
lines. Ads are stripped before classify / search / forecasts. Reading
stays offline. Without the directory the archive is empty.
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import config, moonshot_ads, moonshot_forecasts, taxonomy

_EPISODES: list[dict] | None = None
_DATES: dict[str, str] | None = None
_MIX: list[dict] | None = None

_UNKNOWN_RE = re.compile(r"^unknown speaker\s+\d+$", re.I)
_SPEAKER_LABEL_RE = re.compile(r"^SPEAKER_\d+$", re.I)
_EP_RE = re.compile(r"EPs?\.?\s*#?\s*(\d+)", re.I)
_HASH_EP_RE = re.compile(r"#(\d+)\s*Moonshots", re.I)
_TRAIL_HASH_RE = re.compile(r"[|#]\s*(\d+)\s*$")
_TRAIL_NUM_RE = re.compile(r"\s(\d{2,3})\s*$")
_TITLE_WITH_RE = re.compile(
    r"\b(?:w/|w／|with)\s+(.+?)(?:\s*[|｜]|$)", re.I,
)

_SPEAKER_ALIASES = {
    "peter h. diamandis": "Peter Diamandis",
    "peter diamandis": "Peter Diamandis",
    "alexander wissner-gross": "Alex Wissner-Gross",
    "alex wissner-gross": "Alex Wissner-Gross",
    "awg": "Alex Wissner-Gross",
    "db2": "Dave Blundin",
    "david blunden": "Dave Blundin",
    "dave blundin": "Dave Blundin",
    "imad mostaque": "Emad Mostaque",
    "emad": "Emad Mostaque",
    "mo gawdat": "Mo Gawdat",
    "mo": "Mo Gawdat",
}

_HOSTS = {
    "Peter Diamandis",
    "Dave Blundin",
    "Salim Ismail",
    "Alex Wissner-Gross",
}

_SYNTHETIC = {
    "a doomsday ai", "doomsday ai", "nigel",
    "my ai clone", "ai clone", "peterbot",
    "ai, intelligence", "ai intelligence",
    "ai health breakthroughs",
}

_JUNK = {
    "us government", "spacex ai", "x spaces", "adhd w",
    "the coming change", "ai technology",
}

_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "are", "was", "were",
    "has", "have", "had", "not", "but", "you", "your", "its", "our", "their",
    "his", "her", "she", "him", "they", "them", "all", "can", "will", "would",
    "there", "here", "what", "when", "where", "which", "who", "how", "why",
    "into", "over", "under", "about", "after", "before", "between", "more",
    "than", "then", "now", "out", "off", "new", "one", "two", "say", "says",
    "said", "via",
}

_FORMAT_WEIGHT = {
    "interview": 1.75,
    "mates_panel": 1.25,
    "news_roundup": 0.60,
    "other": 0.40,
}


def invalidate() -> None:
    """Drop the in-process cache (tests, or after files appear on disk)."""
    global _EPISODES, _DATES, _MIX
    _EPISODES = None
    _DATES = None
    _MIX = None
    moonshot_forecasts.invalidate()


def _load_dates() -> dict[str, str]:
    global _DATES
    if _DATES is not None:
        return _DATES
    path = config.MOONSHOT_DATES_FILE
    if not path.exists():
        _DATES = {}
        return _DATES
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = {}
    _DATES = {str(k): str(v) for k, v in raw.items()} if isinstance(raw, dict) else {}
    return _DATES


def is_synthetic(name: str) -> bool:
    return (name or "").strip().lower() in _SYNTHETIC


def _split_people(name: str) -> list[str]:
    """Break YouTube compound labels ('Emad, AWG, Dave & Salim')."""
    raw = (name or "").strip()
    if not raw:
        return []
    parts = re.split(r"\s*(?:,|&| and )\s*", raw)
    out = []
    for p in parts:
        p = p.strip(" .")
        if p:
            out.append(p)
    return out or [raw]


def _clean_one(name: str) -> str | None:
    name = (name or "").strip()
    if not name or _UNKNOWN_RE.match(name) or _SPEAKER_LABEL_RE.match(name):
        return None
    for sep in (" w/ ", " w／ "):
        if sep in name:
            tail = name.split(sep)[-1].strip()
            if 1 < len(tail) < 48:
                name = tail
    low = name.lower()
    if low in _SYNTHETIC or low in _JUNK:
        return None
    if low in _SPEAKER_ALIASES:
        return _SPEAKER_ALIASES[low]
    # honorifics / leftover title heads
    name = re.sub(r"^dr\.?\s+", "", name, flags=re.I)
    name = re.sub(r",?\s*m\.?d\.?$", "", name, flags=re.I)
    if len(name) < 2 or len(name) > 60:
        return None
    if name.lower() in _JUNK:
        return None
    return name


def _clean_speaker(name: str) -> str | None:
    """Drop unmatched labels; fold host aliases; peel title-bleed; split compounds."""
    people = []
    for part in _split_people(name):
        cleaned = _clean_one(part)
        if cleaned and cleaned not in people:
            people.append(cleaned)
    if not people:
        return None
    # a compound that is *only* hosts is not a guest name; return first host
    # so diarization of "Dave & Salim" does not invent a person.
    return people[0] if len(people) == 1 else None


def _clean_many(name: str) -> list[str]:
    out = []
    for part in _split_people(name):
        cleaned = _clean_one(part)
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


def episode_number(title: str) -> int | None:
    """Parse an episode number out of a YouTube title, if one is there."""
    for rx in (_EP_RE, _HASH_EP_RE, _TRAIL_HASH_RE):
        m = rx.search(title)
        if m:
            return int(m.group(1))
    m = _TRAIL_NUM_RE.search(title)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 400:
            return n
    return None


def _iso_date(value: object) -> str:
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    if re.match(r"^\d{8}$", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    return ""


def _compact_segments(raw_segments: list) -> list[dict]:
    out = []
    for seg in raw_segments or []:
        if not isinstance(seg, dict):
            continue
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        out.append({
            "speaker": _clean_speaker(seg.get("speaker") or "") or "",
            "text": text,
            "start": seg.get("start"),
            "end": seg.get("end"),
        })
    return moonshot_ads.tag_segments(out)


def _speakers_in_order(segments: list[dict], recorded: list[str]) -> list[str]:
    """Identified speakers, hosts first, then guests, de-duplicated."""
    seen: list[str] = []
    for name in recorded:
        if name and name not in seen and not is_synthetic(name):
            seen.append(name)
    for seg in segments:
        name = seg.get("speaker") or ""
        if name and name not in seen and not is_synthetic(name):
            seen.append(name)
    hosts = [s for s in seen if s in _HOSTS]
    guests = [s for s in seen if s not in _HOSTS]
    return hosts + guests


def _recorded_speakers(rec: dict) -> list[str]:
    names: list[str] = []
    dia = rec.get("diarization") or {}
    speakers = dia.get("speakers") or {}
    if isinstance(speakers, dict):
        values = speakers.values()
    elif isinstance(speakers, list):
        values = speakers
    else:
        values = []
    for sp in values:
        raw = ""
        if isinstance(sp, dict):
            raw = sp.get("name") or sp.get("speaker") or ""
        else:
            raw = str(sp)
        for cleaned in _clean_many(raw):
            if cleaned not in names:
                names.append(cleaned)
    return names


def _title_guests(title: str) -> list[str]:
    m = _TITLE_WITH_RE.search(title or "")
    if not m:
        return []
    return [n for n in _clean_many(m.group(1)) if n not in _HOSTS]


def _candidate_guests(rec: dict, title: str) -> list[str]:
    names: list[str] = []
    dia = rec.get("diarization") or {}
    for raw in dia.get("guest_candidates") or []:
        if isinstance(raw, dict):
            raw = raw.get("name") or ""
        for n in _clean_many(str(raw)):
            if n not in _HOSTS and n not in names:
                names.append(n)
    for n in _title_guests(title):
        if n not in names:
            names.append(n)
    return names


def _episode_format(title: str, guests: list[str], n_regulars: int) -> str:
    t = title or ""
    commas = t.count(",")
    recapish = commas >= 2 or bool(re.search(
        r"\b(AI Update|This Week|Latest AI News|AI Now)\b", t, re.I))
    if recapish and n_regulars >= 2:
        return "news_roundup"
    if guests and n_regulars <= 1:
        return "interview"
    if n_regulars >= 2:
        return "mates_panel"
    return "other"


def _read_pair(json_path: Path, dates: dict[str, str]) -> dict | None:
    try:
        rec = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(rec, dict):
        return None
    video_id = rec.get("id") or rec.get("video_key") or ""
    if not video_id:
        return None
    txt_path = json_path.with_suffix(".txt")
    text = rec.get("text") or ""
    if not text and txt_path.exists():
        try:
            text = txt_path.read_text(encoding="utf-8")
        except OSError:
            text = ""
    plain = rec.get("plain_text") or ""
    if not plain:
        plain = re.sub(r"^\[\d{2}:\d{2}:\d{2}\]\s*[^:]+:\s*", "", text, flags=re.M)
        plain = re.sub(r"\s+", " ", plain).strip()
    title = rec.get("title") or json_path.stem
    segments = _compact_segments(rec.get("segments") or [])
    speakers = _speakers_in_order(segments, _recorded_speakers(rec))
    guests = [s for s in speakers if s not in _HOSTS]
    # Title / guest_candidates recover people the diarizer left unmatched.
    for n in _candidate_guests(rec, title):
        if n not in speakers:
            speakers.append(n)
        if n not in guests:
            guests.append(n)
    n_regulars = sum(1 for s in speakers if s in _HOSTS and s != "Peter Diamandis")
    content = moonshot_ads.content_text(segments) or plain
    ad_spans = moonshot_ads.spans(segments)
    date = (
        _iso_date(rec.get("publication_date"))
        or _iso_date(rec.get("upload_date"))
        or dates.get(video_id, "")
        or dates.get(rec.get("video_key") or "", "")
    )
    return {
        "video_id": video_id,
        "title": title,
        "url": rec.get("url") or f"https://www.youtube.com/watch?v={video_id}",
        "episode": episode_number(title),
        "date": date,
        "speakers": speakers,
        "guests": guests,
        "plain_text": plain,
        "content_text": content,
        "text": text,
        "segments": segments,
        "ad_spans": ad_spans,
        "ad_fraction": _ad_fraction(segments),
        "fmt": _episode_format(title, guests, n_regulars),
        "word_count": len(content.split()),
        "has_txt": txt_path.exists(),
    }


def _ad_fraction(segments: list[dict]) -> float:
    if not segments:
        return 0.0
    ad = sum(len((s.get("text") or "").split()) for s in segments if s.get("is_ad"))
    tot = sum(len((s.get("text") or "").split()) for s in segments) or 1
    return round(ad / tot, 4)


def load_episodes() -> list[dict]:
    """Paired JSON+TXT episodes, oldest first. Empty if the directory is absent."""
    global _EPISODES
    if _EPISODES is not None:
        return _EPISODES
    directory = config.MOONSHOT_DIR
    if not directory.is_dir():
        _EPISODES = []
        return _EPISODES
    dates = _load_dates()
    episodes = []
    for path in sorted(directory.glob("*.json")):
        ep = _read_pair(path, dates)
        if ep:
            episodes.append(ep)
    episodes.sort(key=lambda it: (it["date"] or "9999", it["episode"] or 0, it["title"]))
    _EPISODES = episodes
    return _EPISODES


def as_stories(episodes: list[dict] | None = None) -> list[dict]:
    """Convert episodes to story dicts for graph seeding (origin=moonshot).

    Classifies the ad-stripped body (not the 4k trailer). Peter is not
    injected as an entity on every row — guests and gazetteer hits are.
    """
    stories = []
    for it in episodes if episodes is not None else load_episodes():
        body = it.get("content_text") or it["plain_text"]
        text = f"{it['title']}\n{' '.join(it['guests'])}\n{body[:12000]}"
        scores = taxonomy.classify_text(text)
        entity_text = f"{it['title']}\n{body[:12000]}"
        entities = taxonomy.extract_entities(entity_text)[:8]
        seen = {e["name"] for e in entities}
        for name in it["guests"]:
            if name not in seen and not is_synthetic(name):
                entities.append({"name": name, "type": "person"})
                seen.add(name)
        for name in it["speakers"]:
            if name in _HOSTS and name != "Peter Diamandis" and name not in seen:
                entities.append({"name": name, "type": "person"})
                seen.add(name)
        places = taxonomy.extract_places(entity_text)[:3]
        summary = body[:300].strip()
        if it["guests"]:
            guest_line = "with " + ", ".join(it["guests"][:4])
            summary = f"{guest_line}. {summary}" if summary else guest_line
        stories.append({
            "id": f"moonshot-{it['video_id']}",
            "source": "moonshots", "source_label": "Moonshots",
            "title": it["title"], "url": it["url"],
            "summary": summary,
            "published_at": f"{it['date']}T12:00:00+00:00" if it["date"] else None,
            "vectors": {v: round(s, 2) for v, s in scores.items()},
            "entities": entities, "places": places,
            "salience": taxonomy.salience(text, scores) + 0.5,
            "origin": "moonshot",
            "extra": {
                "episode": it["episode"],
                "speakers": it["speakers"],
                "guests": it["guests"],
                "youtube_id": it["video_id"],
                "fmt": it.get("fmt"),
                "ad_fraction": it.get("ad_fraction", 0),
            },
        })
    return stories


def search(query: str, limit: int = 8) -> list[dict]:
    """Term search over titles and ad-stripped spoken text. Snippets keep the speaker."""
    terms = [t.lower() for t in re.findall(r"\w+", query)
             if len(t) > 2 and t.lower() not in _STOPWORDS]
    if not terms:
        return []
    hits = []
    for it in load_episodes():
        title_l = it["title"].lower()
        text_l = (it.get("content_text") or it["plain_text"]).lower()
        body = sum(text_l.count(t) for t in terms)
        score = sum(title_l.count(t) * 3 for t in terms) + math.log1p(body)
        if score <= 0:
            continue
        speaker, snippet = _snippet(it, terms)
        hits.append({
            "episode": it["episode"], "date": it["date"],
            "title": it["title"], "url": it["url"],
            "video_id": it["video_id"],
            "score": score, "snippet": snippet, "speaker": speaker,
            "speakers": it["speakers"], "guests": it["guests"],
        })
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:limit]


def _snippet(it: dict, terms: list[str]) -> tuple[str, str]:
    for seg in it["segments"]:
        if seg.get("is_ad"):
            continue
        low = seg["text"].lower()
        if any(t in low for t in terms):
            return seg.get("speaker") or "", seg["text"].strip()[:280]
    body = it.get("content_text") or it["plain_text"]
    idx = min((body.lower().find(t) for t in terms
               if body.lower().find(t) >= 0), default=0)
    return "", body[max(0, idx - 80): idx + 220].strip()


def entity_episodes(entity: str, limit: int = 5) -> list[dict]:
    """Episodes that mention an entity, with who said it (ads skipped)."""
    q = entity.lower().strip()
    if len(q) < 2:
        return []
    rx = re.compile(re.escape(q), re.I)
    hits = []
    for it in load_episodes():
        body = it.get("content_text") or it["plain_text"]
        n = len(rx.findall(body))
        # They often say "Emad", never "Emad Mostaque". Credit the seating chart.
        in_cast = q not in {h.lower() for h in _HOSTS} and any(
            s.lower() == q for s in (it["speakers"] + it["guests"])
        )
        if not n and not in_cast:
            continue
        if in_cast and not n:
            n = 1
        who: dict[str, int] = {}
        quotes: list[dict] = []
        for seg in it["segments"]:
            if seg.get("is_ad") or not rx.search(seg["text"]):
                continue
            speaker = seg.get("speaker") or ""
            if speaker:
                who[speaker] = who.get(speaker, 0) + 1
                if len(quotes) < 2:
                    role = "host" if speaker in _HOSTS else "guest"
                    quotes.append({"speaker": speaker, "role": role,
                                   "text": seg["text"].strip()[:280]})
        speakers = sorted(who, key=who.get, reverse=True)[:3]
        hits.append({
            "episode": it["episode"], "date": it["date"],
            "title": it["title"], "url": it["url"],
            "video_id": it["video_id"],
            "mentions": n, "speakers": speakers, "quotes": quotes,
            "guests": it["guests"],
        })
    hits.sort(key=lambda h: h["mentions"], reverse=True)
    return hits[:limit]


def latest() -> dict | None:
    """Most recently published episode in the local corpus, if dated."""
    dated = [it for it in load_episodes() if it["date"]]
    if not dated:
        return None
    it = max(dated, key=lambda e: e["date"])
    return {k: it[k] for k in
            ("episode", "date", "title", "url", "video_id", "speakers", "guests")}


def on_this_date(month_day: str | None = None) -> dict | None:
    """An episode whose upload month-day matches today, if any."""
    md = month_day or datetime.now(timezone.utc).strftime("%m-%d")
    for it in load_episodes():
        if it["date"] and it["date"][5:] == md:
            return {k: it[k] for k in
                    ("episode", "date", "title", "url", "video_id")}
    return None


def known_guests() -> set[str]:
    names: set[str] = set()
    for it in load_episodes():
        for g in it["guests"]:
            if g not in _HOSTS and not is_synthetic(g):
                names.add(g)
    return names


def recent_guests(days: int = 14) -> list[str]:
    """Named guests (not hosts, not synthetics) from episodes in the last `days`."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    names: list[str] = []
    for it in load_episodes():
        if not it["date"] or it["date"] < cutoff:
            continue
        for g in it["guests"]:
            if g not in names and g not in _HOSTS and not is_synthetic(g):
                names.append(g)
    return names


def _share(scores: dict[str, float]) -> dict[str, float]:
    total = sum(scores.values()) or 1.0
    return {v: scores.get(v, 0.0) / total for v in config.VECTOR_NAMES}


def vector_mix() -> list[dict]:
    """Monthly mean vector shares from ad-stripped full bodies."""
    global _MIX
    if _MIX is not None:
        return _MIX
    buckets: dict[str, list[dict[str, float]]] = {}
    for it in load_episodes():
        month = (it["date"] or "")[:7]
        if len(month) != 7:
            continue
        body = it.get("content_text") or it["plain_text"]
        text = f"{it['title']}\n{body}"
        buckets.setdefault(month, []).append(_share(taxonomy.classify_text(text)))
    mix = []
    for month in sorted(buckets):
        rows = buckets[month]
        n = len(rows)
        avg = {v: round(sum(r[v] for r in rows) / n, 4) for v in config.VECTOR_NAMES}
        mix.append({"month": month, "n": n, "shares": avg})
    _MIX = mix
    return _MIX


def prior_shares(days: int | None = None) -> dict[str, float]:
    """Log-compressed, format-weighted vector mix over the prior window."""
    days = days if days is not None else config.MOONSHOT_PRIOR_DAYS
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    acc = {v: 0.0 for v in config.VECTOR_NAMES}
    weight = 0.0
    for it in load_episodes():
        if not it["date"] or it["date"] < cutoff:
            continue
        w = _FORMAT_WEIGHT.get(it.get("fmt") or "other", 0.4)
        body = it.get("content_text") or it["plain_text"]
        scores = taxonomy.classify_text(f"{it['title']}\n{body}")
        for v, s in scores.items():
            if v in acc:
                acc[v] += math.log1p(s) * w
        weight += w
    if weight <= 0:
        return {v: 1.0 / len(config.VECTOR_NAMES) for v in config.VECTOR_NAMES}
    total = sum(acc.values()) or 1.0
    return {v: round(acc[v] / total, 4) for v in config.VECTOR_NAMES}
