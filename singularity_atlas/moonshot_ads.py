"""Detect Peter Diamandis mid-rolls and own-media CTAs in Moonshot segments.

Framed ads (opener / brand script / closer) are dropped from SI, search,
forecasts, and vector mix. Guest-company interviews are not ads.
"""

from __future__ import annotations

import re

_OPENER = re.compile(
    r"this episode is (brought to you|sponsored)"
    r"|welcome to the health section"
    r"|(quick|short) break from (this|the|our) episode"
    r"|every day i get the strangest compliment"
    r"|every week,? my team and i study"
    r"|i'?ve been asked over and over again,? what do i do for my own health",
    re.I,
)

_SCRIPT = re.compile(
    r"infinite code context|5x your engineering velocity|blitzy\.com|\bblitzi\b"
    r"|fountainlife\.com|company is called fountain life"
    r"|levels\.link|oneskin\.co|seed\.com/moonshots|athleticgreens|\bag1\b"
    r"|viome\.com|google for startups|8sleep|eightsleep"
    r"|diamandis\.com|dmandus\.com|demandus\.com|slash metatrends"
    r"|mylifeforce\.com|use code peter|write peter at checkout"
    r"|abundance360\.com",
    re.I,
)

_CLOSER = re.compile(
    r"now back to (the|our|this) episode"
    r"|let'?s go back to (the|our|this) episode"
    r"|i'?m going to take us back"
    r"|all right,? back to the episode"
    r"|alright,? now back to the episode",
    re.I,
)

_BRANDS = (
    ("blitzy", re.compile(r"blitzy|blitzi|infinite code context", re.I)),
    ("fountain_life", re.compile(r"fountain ?life|fountainlife", re.I)),
    ("oneskin", re.compile(r"oneskin", re.I)),
    ("viome", re.compile(r"viome", re.I)),
    ("levels", re.compile(r"levels\.link|the levels app|brought to you by levels", re.I)),
    ("eight_sleep", re.compile(r"8sleep|eight sleep|pod cover", re.I)),
    ("seed", re.compile(r"seed\.com|ds-01", re.I)),
    ("ag1", re.compile(r"athletic greens|\bag1\b", re.I)),
    ("google_startups", re.compile(r"google for startups", re.I)),
    ("metatrends", re.compile(r"metatrends|diamandis\.com|dmandus|demandus", re.I)),
    ("abundance360", re.compile(r"abundance ?360|abundance360", re.I)),
    ("lifeforce", re.compile(r"mylifeforce|life force", re.I)),
)

_MAX_SPAN_S = 180.0
_LEAD_IN_S = 20.0


def _t(seg: dict) -> float:
    try:
        return float(seg.get("start") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _end(segments: list[dict], i: int) -> float:
    nxt = _t(segments[i + 1]) if i + 1 < len(segments) else _t(segments[i]) + 8.0
    return max(nxt, _t(segments[i]) + 1.0)


def _is_seed(text: str) -> bool:
    return bool(_OPENER.search(text) or _SCRIPT.search(text) or _CLOSER.search(text))


def _brand_of(text: str) -> tuple[str, str]:
    for brand, rx in _BRANDS:
        if rx.search(text):
            kind = "health_section" if "health section" in text.lower() else "paid_midroll"
            if brand in {"fountain_life", "abundance360", "metatrends", "lifeforce"}:
                kind = "own_company" if brand != "metatrends" else "own_media"
            if "health section" in text.lower():
                kind = "health_section"
            return brand, kind
    return "unknown", "paid_midroll"


def tag_segments(segments: list[dict]) -> list[dict]:
    """Copy segments and set is_ad / ad_brand on framed promo spans."""
    if not segments:
        return []
    out = [dict(s) for s in segments]
    for s in out:
        s["is_ad"] = False
        s["ad_brand"] = ""
        s["ad_kind"] = ""
    n = len(out)
    used = [False] * n

    seeds = [i for i, s in enumerate(out) if _is_seed(s.get("text") or "")]
    for seed in seeds:
        if used[seed]:
            continue
        lo = seed
        t0 = _t(out[seed])
        while lo > 0:
            prev = out[lo - 1]
            speaker = prev.get("speaker") or ""
            if t0 - _t(prev) > _LEAD_IN_S:
                break
            if speaker and speaker != "Peter Diamandis":
                break
            lo -= 1
        hi = seed
        closer_hit = bool(_CLOSER.search(out[seed].get("text") or ""))
        while hi + 1 < n and not closer_hit:
            nxt = out[hi + 1]
            if _end(out, hi) - _t(out[lo]) > _MAX_SPAN_S:
                break
            speaker = nxt.get("speaker") or ""
            text = nxt.get("text") or ""
            if _CLOSER.search(text):
                hi += 1
                closer_hit = True
                break
            if speaker and speaker != "Peter Diamandis" and not _is_seed(text):
                break
            hi += 1
        blob = " ".join(out[i].get("text") or "" for i in range(lo, hi + 1))
        brand, kind = _brand_of(blob)
        for i in range(lo, hi + 1):
            used[i] = True
            out[i]["is_ad"] = True
            out[i]["ad_brand"] = brand
            out[i]["ad_kind"] = kind
    return out


def spans(segments: list[dict]) -> list[dict]:
    """Collapsed {start, end, brand, kind} from tagged segments."""
    tagged = segments if segments and "is_ad" in segments[0] else tag_segments(segments)
    out: list[dict] = []
    run: list[dict] = []
    for i, seg in enumerate(tagged):
        if seg.get("is_ad"):
            run.append((i, seg))
            continue
        if run:
            out.append(_collapse(tagged, run))
            run = []
    if run:
        out.append(_collapse(tagged, run))
    return out


def _collapse(tagged: list[dict], run: list[tuple[int, dict]]) -> dict:
    first_i, first = run[0]
    last_i, last = run[-1]
    return {
        "start": round(_t(first), 2),
        "end": round(_end(tagged, last_i), 2),
        "brand": first.get("ad_brand") or "unknown",
        "kind": first.get("ad_kind") or "paid_midroll",
    }


def content_text(segments: list[dict]) -> str:
    tagged = segments if segments and "is_ad" in (segments[0] if segments else {}) else tag_segments(segments)
    return " ".join((s.get("text") or "").strip() for s in tagged if not s.get("is_ad")).strip()
