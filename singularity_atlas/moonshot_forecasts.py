"""Forecast ledger: dated, speaker-attributed claims from stripped Moonshot turns.

Not a crystal ball. The atlas tracks what this room said, and how the
distribution of stated years has moved. Ads, citations of Ray/Elon as if
they were the speaker's own year, and hypotheticals are filtered.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from . import moonshot_ads

_YEAR_RE = re.compile(r"\b(202[4-9]|203[0-9]|204[0-5])\b")
_HERE_RE = re.compile(
    r"\bagi is here\b|\balready (?:had|have|achieved) agi\b|"
    r"we(?:['’]re| are) at agi\b|passed agi\b|agi already\b",
    re.I,
)
_CITE_RE = re.compile(
    r"\bkurzweil\b|\bray(?:'s|’s)?\b|\belon (?:said|says|thinks)\b|"
    r"\bdemis\b|\bpredicted\b.{0,24}\b(2029|2045)\b",
    re.I,
)
_HYPO_RE = re.compile(r"\bimagine if\b|\bwhat if\b|\bhypothetic", re.I)
_OWN_RE = re.compile(
    r"\bi (?:think|believe|predict|expect|see|said)|that's my|"
    r"\bmy (?:point|view|prediction|estimate)\b",
    re.I,
)

_FAMILIES: list[tuple[str, re.Pattern, str]] = [
    ("benchmark", re.compile(
        r"frontiermath|gdpval|hle\b|humanity'?s last exam|swe-bench", re.I), "capability"),
    ("humanoid", re.compile(r"humanoid|optimus|\brobotaxi\b", re.I), "embodiment"),
    ("energy", re.compile(
        r"gigawatt|\b\d+\s*gw\b|terafab|fusion|orbital data", re.I), "compute"),
    ("jobs", re.compile(
        r"white.?collar|job[s]? (?:gone|loss|replaced|displaced)|"
        r"\bubi\b|unemployment", re.I), "culture"),
    ("asi", re.compile(r"\basi\b|superintelligence", re.I), "capability"),
    ("agi_year", re.compile(r"\bagi\b|artificial general|singularity", re.I), "capability"),
    ("longevity", re.compile(
        r"escape velocity|\blev\b|live to (?:1[25]0)|age reversal", re.I), "culture"),
]

_HOSTS = {
    "Peter Diamandis", "Dave Blundin", "Salim Ismail", "Alex Wissner-Gross",
}

_CACHE: list[dict] | None = None
_SUMMARY: dict | None = None


def invalidate() -> None:
    global _CACHE, _SUMMARY
    _CACHE = None
    _SUMMARY = None


def _family(text: str) -> tuple[str, str] | None:
    for name, rx, vector in _FAMILIES:
        if rx.search(text):
            return name, vector
    return None


def extract(episodes: list[dict]) -> list[dict]:
    """Build forecast rows from ad-stripped segments. Caps per episode."""
    rows: list[dict] = []
    for ep in episodes:
        n_ep = 0
        segs = ep.get("segments") or []
        tagged = segs if segs and "is_ad" in (segs[0] if segs else {}) else moonshot_ads.tag_segments(segs)
        for seg in tagged:
            if n_ep >= 8:
                break
            if seg.get("is_ad"):
                continue
            text = (seg.get("text") or "").strip()
            if len(text) < 24 or _HYPO_RE.search(text):
                continue
            fam = _family(text)
            years = [int(y) for y in _YEAR_RE.findall(text)]
            here = bool(_HERE_RE.search(text))
            if not fam and not years and not here:
                continue
            if not fam:
                continue
            family, vector = fam
            if not years and not here and family not in {"benchmark", "jobs", "energy", "humanoid"}:
                continue
            speaker = seg.get("speaker") or ""
            if not speaker:
                continue
            cite = bool(_CITE_RE.search(text))
            own = bool(_OWN_RE.search(text))
            if cite and not own:
                attribution = "citation"
            elif own:
                attribution = "own"
            else:
                attribution = "unmarked"
            role = "host" if speaker in _HOSTS else "guest"
            year = years[0] if years else None
            if here and year is None:
                # "AGI is here" on the episode's calendar
                try:
                    year = int((ep.get("date") or "")[:4]) or None
                except ValueError:
                    year = None
            rows.append({
                "speaker": speaker,
                "role": role,
                "episode": ep.get("episode"),
                "date": ep.get("date") or "",
                "title": ep.get("title") or "",
                "url": ep.get("url") or "",
                "video_id": ep.get("video_id") or "",
                "start": seg.get("start"),
                "family": family,
                "vector": vector,
                "year": year,
                "here": here,
                "attribution": attribution,
                "quote": text[:400],
            })
            n_ep += 1
    return rows


def load_forecasts(episodes: list[dict] | None = None) -> list[dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if episodes is None:
        from . import moonshot_archive
        episodes = moonshot_archive.load_episodes()
    _CACHE = extract(episodes)
    return _CACHE


def _median(xs: list[float]) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    mid = len(xs) // 2
    if len(xs) % 2:
        return float(xs[mid])
    return (xs[mid - 1] + xs[mid]) / 2.0


def summary(episodes: list[dict] | None = None) -> dict:
    """Dashboard strip: n, guest median year, trailing-12m velocity, samples."""
    global _SUMMARY
    if _SUMMARY is not None:
        return _SUMMARY
    rows = load_forecasts(episodes)
    agi = [r for r in rows if r["family"] in {"agi_year", "asi"}
           and r["year"] and r["attribution"] != "citation"]
    guests = [r for r in agi if r["role"] == "guest"]
    hosts = [r for r in agi if r["role"] == "host"]
    guest_median = _median([r["year"] for r in guests])
    host_median = _median([r["year"] for r in hosts])

    today = datetime.now(timezone.utc).date()
    def in_months(r, lo, hi):
        if not r["date"]:
            return False
        try:
            d = datetime.strptime(r["date"][:10], "%Y-%m-%d").date()
        except ValueError:
            return False
        months = (today.year - d.year) * 12 + (today.month - d.month)
        return lo <= months < hi

    recent = [r["year"] for r in guests if in_months(r, 0, 12)]
    prev = [r["year"] for r in guests if in_months(r, 12, 24)]
    rmed, pmed = _median(recent), _median(prev)
    velocity = None
    if rmed is not None and pmed is not None:
        velocity = round(rmed - pmed, 1)  # negative = pulled earlier

    sample = []
    prefer = [r for r in rows if r["role"] == "guest" and r["attribution"] == "own" and r.get("year")]
    dated_guests = [r for r in guests if r.get("year")]
    pool = prefer or dated_guests or guests or agi or rows
    for r in pool[:3]:
        sample.append({
            "speaker": r["speaker"], "role": r["role"], "year": r["year"],
            "quote": r["quote"], "date": r["date"], "title": r["title"],
            "url": r["url"], "family": r["family"],
        })
    _SUMMARY = {
        "n": len(rows),
        "n_agi": len(agi),
        "guest_median": guest_median,
        "host_median": host_median,
        "velocity_yr": velocity,
        "sample": sample,
    }
    return _SUMMARY


def for_entity(name: str, limit: int = 4) -> list[dict]:
    """Forecast quotes by this person, or mentioning them."""
    q = (name or "").lower().strip()
    if len(q) < 3:
        return []
    hits = []
    for r in load_forecasts():
        if r["speaker"].lower() == q or q in (r["quote"] or "").lower():
            hits.append(r)
    return hits[:limit]
