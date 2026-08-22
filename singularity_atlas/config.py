"""The Singularity Atlas — configuration.

Everything tunable lives here: feeds, ports, model names, vector weights,
and the curated geography used by the globe layers.
"""

from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
SEEN_FILE = DATA_DIR / "seen.json"          # dedupe fingerprints
SI_HISTORY_FILE = DATA_DIR / "si_history.jsonl"
FEED_HEALTH_FILE = DATA_DIR / "feed_health.json"
LOOP_ARCHIVE_DIR = ROOT / "ref" / "innermost-loop" / "the-innermost-loop-markdown" / "issues"
LOOP_FETCH_DIR = DATA_DIR / "loop_issues"   # editions fetched from the live feed
LOOP_SYNC_STATE_FILE = DATA_DIR / "loop_sync.json"
# Local Moonshots transcripts (JSON + TXT pairs). Gitignored; third-party.
MOONSHOT_DIR = ROOT / "transcriptions_moonshot"
MOONSHOT_DATES_FILE = Path(__file__).resolve().parent / "moonshot_dates.json"
WEB_DIR = ROOT / "web"

# ---------------------------------------------------------------------------
# Neo4j
# ---------------------------------------------------------------------------
NEO4J_URI = os.environ.get("ATLAS_NEO4J_URI", "bolt://localhost:7689")
NEO4J_USER = os.environ.get("ATLAS_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("ATLAS_NEO4J_PASSWORD", "singularity-atlas")

# ---------------------------------------------------------------------------
# Ollama
# ---------------------------------------------------------------------------
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("ATLAS_MODEL", "qwen3.8:27b-mtp-bf16")
LLM_TIMEOUT_S = 180

# ---------------------------------------------------------------------------
# HTTP / API
# ---------------------------------------------------------------------------
API_HOST = os.environ.get("ATLAS_HOST", "127.0.0.1")
API_PORT = int(os.environ.get("ATLAS_PORT", "8055"))
HTTP_TIMEOUT_S = 20
USER_AGENT = "singularity-atlas/0.1 (+https://localhost/singularity-atlas)"

# ---------------------------------------------------------------------------
# Ingest scheduling
# ---------------------------------------------------------------------------
INGEST_INTERVAL_MIN = 15
LOOP_SYNC_INTERVAL_H = 24        # Alex posts ~daily; the feed holds 20 issues
BRIEF_MIN_NEW_ITEMS = 6          # skip brief if fewer new stories
BRIEF_TOP_N = 14                 # stories fed to the LLM for the daily loop
SIGNAL_WINDOW_H = 72             # convergence window
SI_BASELINE_DAYS = 7             # window for the SI delta baseline mean

# Moonshot influence on the live gauge. 0 = illustration only (histograms,
# ledger, drawer). Default is a hair of mix-in, hard-clamped so 276
# historical episodes cannot peg the index.
MOONSHOT_PRIOR_ALPHA = float(os.environ.get("ATLAS_MOONSHOT_PRIOR", "0.04"))
MOONSHOT_PRIOR_CLAMP = 3.0
MOONSHOT_PRIOR_DAYS = 90
MOONSHOT_GUEST_WINDOW_D = 14
MOONSHOT_GUEST_BONUS = 0.4       # per recent guest also in today's feed
MOONSHOT_GUEST_BONUS_CAP = 2.0

# ---------------------------------------------------------------------------
# Singularity vectors — the eight streams the dashboard watches.
# weight: contribution to the composite Singularity Index.
# ---------------------------------------------------------------------------
VECTORS: dict[str, dict] = {
    "capability": {"label": "Capability",  "weight": 0.18, "color": "#00e5ff",
                   "blurb": "Frontier models, benchmarks, reasoning"},
    "compute":    {"label": "Compute",     "weight": 0.16, "color": "#ff6d00",
                   "blurb": "Chips, fabs, datacenters, energy"},
    "capital":    {"label": "Capital",     "weight": 0.12, "color": "#ffd600",
                   "blurb": "Funding, valuations, revenue, M&A"},
    "embodiment": {"label": "Embodiment",  "weight": 0.12, "color": "#00e676",
                   "blurb": "Robots, humanoids, drones, autonomy"},
    "agency":     {"label": "Agency",      "weight": 0.14, "color": "#d500f9",
                   "blurb": "Agents, tool use, open weights, self-improvement"},
    "security":   {"label": "Security",    "weight": 0.12, "color": "#ff1744",
                   "blurb": "Safety, alignment, cyber, regulation"},
    "space":      {"label": "Space",       "weight": 0.08, "color": "#2979ff",
                   "blurb": "Launches, orbital compute, the frontier up"},
    "culture":    {"label": "Culture",     "weight": 0.08, "color": "#ffab91",
                   "blurb": "Society metabolizing the change"},
}
VECTOR_NAMES = list(VECTORS.keys())

# ---------------------------------------------------------------------------
# Accelerando epoch dial — Stross's three parts mapped to calendar years.
# ---------------------------------------------------------------------------
EPOCHS = [
    {"name": "Slow Takeoff",       "start": 2015, "end": 2029},
    {"name": "Point of Inflexion", "start": 2030, "end": 2039},
    {"name": "Singularity",        "start": 2040, "end": 2045},
]
SINGULARITY_YEAR = 2045  # Kurzweil's date; the dial counts down to Jan 1, 2045.

ACCELERANDO_QUOTES = [
    ("The Singularity is a rapture for nerds.", "Accelerando"),
    ("It's not the future until it's evenly distributed.", "after Accelerando"),
    ("We are the music makers, and we are the dreamers of dreams.", "Accelerando epigraph"),
    ("The Vile Offspring are coming.", "Accelerando"),
    ("Economics 2.0 is not for humans.", "Accelerando"),
    ("Your species is under new management.", "Accelerando"),
    ("The innermost loop is always the fastest.", "after Wissner-Gross"),
    ("Welcome to the point of inflexion.", "Accelerando"),
]

# ---------------------------------------------------------------------------
# Feeds — all verified reachable, none require auth or registration.
# kind: rss | arxiv | hn | launches | gdelt
# ---------------------------------------------------------------------------
# The Innermost Loop — the author's official Substack mirror. Fetched into the
# Loop Archive (not FEEDS) so editions keep full text for archive search.
LOOP_FEED_URL = "https://theinnermostloop.substack.com/feed"
LOOP_FETCH_LIMIT = 20

FEEDS: list[dict] = [
    # -- research pulse -----------------------------------------------------
    {"id": "arxiv-cs-ai", "kind": "arxiv", "label": "arXiv cs.AI",
     "categories": ["cs.AI"], "vectors": ["capability", "agency"]},
    {"id": "arxiv-cs-lg", "kind": "arxiv", "label": "arXiv cs.LG",
     "categories": ["cs.LG"], "vectors": ["capability"]},
    {"id": "arxiv-cs-cl", "kind": "arxiv", "label": "arXiv cs.CL",
     "categories": ["cs.CL"], "vectors": ["capability", "agency"]},
    {"id": "arxiv-cs-ro", "kind": "arxiv", "label": "arXiv cs.RO",
     "categories": ["cs.RO"], "vectors": ["embodiment"]},
    # -- lab & industry blogs ------------------------------------------------
    {"id": "openai", "kind": "rss", "label": "OpenAI",
     "url": "https://openai.com/news/rss.xml", "vectors": ["capability", "agency"]},
    {"id": "deepmind", "kind": "rss", "label": "Google DeepMind",
     "url": "https://deepmind.google/blog/rss.xml", "vectors": ["capability"]},
    {"id": "import-ai", "kind": "rss", "label": "Import AI",
     "url": "https://importai.substack.com/feed", "vectors": ["capability", "security"]},
    {"id": "interconnects", "kind": "rss", "label": "Interconnects",
     "url": "https://www.interconnects.ai/feed", "vectors": ["capability", "agency"]},
    # -- tech press ----------------------------------------------------------
    {"id": "mit-tr-ai", "kind": "rss", "label": "MIT Tech Review AI",
     "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
     "vectors": ["culture", "capability"]},
    {"id": "ars", "kind": "rss", "label": "Ars Technica",
     "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
     "vectors": ["culture", "compute"]},
    {"id": "verge-ai", "kind": "rss", "label": "The Verge AI",
     "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
     "vectors": ["culture", "capital"]},
    {"id": "venturebeat-ai", "kind": "rss", "label": "VentureBeat AI",
     "url": "https://venturebeat.com/category/ai/feed/", "vectors": ["capital", "agency"]},
    # -- crowd signal --------------------------------------------------------
    {"id": "hn-ai", "kind": "hn", "label": "Hacker News",
     "queries": ["AI", "LLM", "OpenAI", "Anthropic", "AGI", "robot"],
     "min_points": 60, "vectors": ["culture", "agency"]},
    # -- the frontier up -----------------------------------------------------
    {"id": "launches", "kind": "launches", "label": "Launch Library",
     "url": "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=20&mode=detailed",
     "vectors": ["space"]},
    # -- geolocated world press ----------------------------------------------
    {"id": "gdelt-ai", "kind": "gdelt", "label": "GDELT AI press",
     "url": ("https://api.gdeltproject.org/api/v2/doc/doc"
             "?query=%22artificial%20intelligence%22&mode=artlist"
             "&maxrecords=40&format=json&sort=hybridrel"),
     "vectors": ["culture"]},
]

# ---------------------------------------------------------------------------
# Curated geography for the globe's infrastructure layers.
# (name, lat, lon, kind, note)
# ---------------------------------------------------------------------------
GLOBE_SITES: list[dict] = [
    # --- AI gigacampuses / datacenters -------------------------------------
    {"name": "Stargate Abilene",      "lat": 32.45,  "lon": -99.73,  "kind": "datacenter", "note": "OpenAI/Oracle Stargate campus"},
    {"name": "OpenAI Ohio campus",    "lat": 39.96,  "lon": -83.00,  "kind": "datacenter", "note": "10-GW lease, NVIDIA-backed"},
    {"name": "xAI Colossus Memphis",  "lat": 35.15,  "lon": -90.05,  "kind": "datacenter", "note": "Colossus supercluster"},
    {"name": "Microsoft Fairwater WI","lat": 42.89,  "lon": -87.91,  "kind": "datacenter", "note": "Multi-GW AI datacenter"},
    {"name": "CoreWeave Lancaster PA","lat": 40.04,  "lon": -76.31,  "kind": "datacenter", "note": "GPU cloud campus"},
    {"name": "Meta Hyperion LA",      "lat": 32.30,  "lon": -92.00,  "kind": "datacenter", "note": "Hyperion multi-GW site"},
    {"name": "AWS New Carlisle IN",   "lat": 41.70,  "lon": -86.51,  "kind": "datacenter", "note": "Anthropic training campus"},
    # --- fabs ---------------------------------------------------------------
    {"name": "TSMC Phoenix",          "lat": 33.75,  "lon": -112.20, "kind": "fab", "note": "N4/N3 fab cluster"},
    {"name": "TSMC Hsinchu",          "lat": 24.78,  "lon": 121.00,  "kind": "fab", "note": "2-nm heartland"},
    {"name": "Samsung Taylor TX",     "lat": 30.57,  "lon": -97.41,  "kind": "fab", "note": "Advanced logic fab"},
    {"name": "Intel Ohio One",        "lat": 40.09,  "lon": -82.75,  "kind": "fab", "note": "Silicon heartland"},
    {"name": "Terafab Austin",        "lat": 30.27,  "lon": -97.74,  "kind": "fab", "note": "Tesla 2-nm-class AI chips + memory"},
    # --- labs -----------------------------------------------------------------
    {"name": "OpenAI San Francisco",  "lat": 37.77,  "lon": -122.41, "kind": "lab", "note": "Frontier lab HQ"},
    {"name": "Anthropic San Francisco","lat": 37.79, "lon": -122.40, "kind": "lab", "note": "Frontier lab HQ"},
    {"name": "Google DeepMind London","lat": 51.52,  "lon": -0.09,   "kind": "lab", "note": "Frontier lab HQ"},
    {"name": "Meta AI Menlo Park",    "lat": 37.45,  "lon": -122.18, "kind": "lab", "note": "Superintelligence lab"},
    {"name": "DeepSeek Hangzhou",     "lat": 30.27,  "lon": 120.16,  "kind": "lab", "note": "Open-weight frontier"},
    {"name": "Alibaba Qwen Hangzhou", "lat": 30.25,  "lon": 120.17,  "kind": "lab", "note": "Qwen frontier models"},
    {"name": "Mistral Paris",         "lat": 48.86,  "lon": 2.35,    "kind": "lab", "note": "EU frontier lab"},
    {"name": "xAI Palo Alto",         "lat": 37.44,  "lon": -122.14, "kind": "lab", "note": "Grok frontier lab"},
    {"name": "Unitree Hangzhou",      "lat": 30.28,  "lon": 120.15,  "kind": "lab", "note": "Humanoid robots"},
    {"name": "Figure AI Sunnyvale",   "lat": 37.37,  "lon": -122.04, "kind": "lab", "note": "Humanoid robots"},
    {"name": "Boston Dynamics Waltham","lat": 42.38, "lon": -71.25,  "kind": "lab", "note": "Atlas humanoids"},
    # --- launch sites ----------------------------------------------------------
    {"name": "Starbase Boca Chica",   "lat": 25.99,  "lon": -97.15,  "kind": "launch", "note": "Starship"},
    {"name": "Cape Canaveral",        "lat": 28.39,  "lon": -80.60,  "kind": "launch", "note": "KSC / CCSFS"},
    {"name": "Vandenberg SFB",        "lat": 34.74,  "lon": -120.57, "kind": "launch", "note": "Polar launches"},
    {"name": "Jiuquan",               "lat": 40.96,  "lon": 100.29,  "kind": "launch", "note": "China crewed/lunar"},
    {"name": "Wenchang",              "lat": 19.61,  "lon": 110.95,  "kind": "launch", "note": "Long March 5/10"},
]
