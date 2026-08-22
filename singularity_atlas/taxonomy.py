"""Heuristic taxonomy: the eight Singularity vectors, their keyword fields,
and a gazetteer of known entities (orgs, people, models, places, tech).

The classifier is deliberately simple and explainable: weighted keyword hits.
The LLM pass (pipeline.classify) refines only ambiguous or high-value items.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Keyword fields per vector. Multi-word phrases match on substrings;
# single tokens match on word boundaries. Weight per hit = len(set).
# ---------------------------------------------------------------------------
VECTOR_KEYWORDS: dict[str, list[str]] = {
    "capability": [
        "agi", "asi", "superintelligence", "frontier model", "foundation model",
        "benchmark", "sota", "state-of-the-art", "reasoning", "chain-of-thought",
        "multimodal", "frontier capability", "artificial analysis", "eval",
        "evaluation", "mmlu", "gpqa", "swe-bench", "arc-agi", "humanity's last exam",
        "o1", "o3", "gpt-5", "gpt-6", "claude", "gemini", "grok", "qwen", "deepseek",
        "llama", "mistral", "context window", "test-time compute", "inference scaling",
        "world model", "general intelligence", "turing test",
    ],
    "compute": [
        "gpu", "h100", "h200", "b200", "gb300", "blackwell", "rubin", "tpu", "npu",
        "asic", "chip", "semiconductor", "fab", "2nm", "2-nm", "3nm", "euv", "tsmc",
        "samsung foundry", "intel foundry", "datacenter", "data center", "gigawatt",
        "gw campus", "power grid", "nuclear", "smr", "energy", "dram", "hbm",
        "memory", "inference cluster", "supercluster", "colossus", "stargate",
        "terafab", "nvidia", "broadcom", "openai data center", "hyperscale",
    ],
    "capital": [
        "funding", "raises", "raised", "valuation", "billion", "trillion", "ipo",
        "revenue", "run rate", "arr", "acquisition", "acquires", "merger", "stake",
        "investment", "invests", "venture", "softbank", "series a", "series b",
        "series c", "term sheet", "capex", "off-balance-sheet", "circular financing",
        "deal", "buys", "sell-off", "market cap", "earnings", "profit",
    ],
    "embodiment": [
        "robot", "humanoid", "optimus", "atlas", "figure 01", "figure 02", "unitree",
        "boston dynamics", "drone", "quadcopter", "self-driving", "autonomous vehicle",
        "robotaxi", "waymo", "cybercab", "actuator", "dexterous", "manipulation",
        "locomotion", "embodied ai", "physical ai", "physical superintelligence",
        "factory robot", "warehouse robot", "exoskeleton", "bipedal",
    ],
    "agency": [
        "agent", "agentic", "ai agent", "coding agent", "autonomous agent",
        "tool use", "function calling", "mcp", "computer use", "browser agent",
        "open-weight", "open weight", "open source model", "apache-licensed",
        "self-improvement", "self-improving", "recursive self-improvement",
        "automated coder", "ai researcher agent", "swarm", "orchestration",
        "fine-tune", "distill", "distillation", "rlhf", "rlaif", "reinforcement",
    ],
    "security": [
        "ai safety", "alignment", "misalignment", "existential risk", "x-risk",
        "cyberattack", "cyber", "exploit", "vulnerability", "jailbreak", "red team",
        "watermark", "steganographic", "regulation", "executive order", "eu ai act",
        "export control", "chip ban", "sanctions", "surveillance", "deepfake",
        "misinformation", "bioweapon", "dual-use", "defender's window", "safeguard",
        "guardrail", "interpretability", "evals gap", "moratorium",
    ],
    "space": [
        "launch", "rocket", "starship", "falcon 9", "long march", "satellite",
        "orbit", "orbital", "lunar", "moon", "mars", "space station", "nasa",
        "spacex", "blue origin", "rocket lab", "payload", "starlink", "kuiper",
        "orbital data center", "space data", "south pole", "artemis", "chang'e",
        "space race", "uap", "ufo", "avi loeb", "interstellar",
    ],
    "culture": [
        "jobs", "unemployment", "ubi", "labor", "workforce", "election", "voters",
        "regulation backlash", "protest", "hollywood", "writers strike", "copyright",
        "lawsuit", "court", "education", "students", "art", "music", "film",
        "novel", "broadway", "society", "public opinion", "poll", "anxiety",
        "doomer", "accelerationist", "e/acc", "effective altruism", "cult",
        "religion", "god", "consciousness", "sentience", "personhood",
    ],
}

# ---------------------------------------------------------------------------
# Gazetteer of known entities -> (type, canonical name).
# Matching is case-insensitive on word boundaries; longest match wins.
# ---------------------------------------------------------------------------
GAZETTEER: dict[str, tuple[str, str]] = {
    # orgs
    "openai": ("org", "OpenAI"), "anthropic": ("org", "Anthropic"),
    "google deepmind": ("org", "Google DeepMind"), "deepmind": ("org", "Google DeepMind"),
    "xai": ("org", "xAI"), "meta": ("org", "Meta"), "meta ai": ("org", "Meta"),
    "nvidia": ("org", "NVIDIA"), "tsmc": ("org", "TSMC"), "intel": ("org", "Intel"),
    "samsung": ("org", "Samsung"), "broadcom": ("org", "Broadcom"),
    "microsoft": ("org", "Microsoft"), "amazon": ("org", "Amazon"),
    "aws": ("org", "Amazon"), "apple": ("org", "Apple"), "google": ("org", "Google"),
    "alphabet": ("org", "Google"), "alibaba": ("org", "Alibaba"),
    "deepseek": ("org", "DeepSeek"), "mistral": ("org", "Mistral"),
    "cohere": ("org", "Cohere"), "perplexity": ("org", "Perplexity"),
    "softbank": ("org", "SoftBank"), "oracle": ("org", "Oracle"),
    "coreweave": ("org", "CoreWeave"), "stripe": ("org", "Stripe"),
    "openrouter": ("org", "OpenRouter"), "spacex": ("org", "SpaceX"),
    "blue origin": ("org", "Blue Origin"), "rocket lab": ("org", "Rocket Lab"),
    "nasa": ("org", "NASA"), "tesla": ("org", "Tesla"), "waymo": ("org", "Waymo"),
    "unitree": ("org", "Unitree"), "boston dynamics": ("org", "Boston Dynamics"),
    "figure ai": ("org", "Figure AI"),
    "figure 01": ("org", "Figure AI"), "figure 02": ("org", "Figure AI"),
    "hugging face": ("org", "Hugging Face"), "groq": ("org", "Groq"),
    "cerebras": ("org", "Cerebras"), "sambanova": ("org", "SambaNova"),
    "scale ai": ("org", "Scale AI"), "palantir": ("org", "Palantir"),
    "anduril": ("org", "Anduril"), "uber": ("org", "Uber"), "zipline": ("org", "Zipline"),
    "flock": ("org", "Flock Safety"), "eu": ("org", "European Union"),
    "european commission": ("org", "European Commission"),
    "ai futures project": ("org", "AI Futures Project"),
    # people
    "sam altman": ("person", "Sam Altman"), "dario amodei": ("person", "Dario Amodei"),
    "demis hassabis": ("person", "Demis Hassabis"), "elon musk": ("person", "Elon Musk"),
    "jensen huang": ("person", "Jensen Huang"), "satya nadella": ("person", "Satya Nadella"),
    "mark zuckerberg": ("person", "Mark Zuckerberg"), "zuckerberg": ("person", "Mark Zuckerberg"),
    "sundar pichai": ("person", "Sundar Pichai"), "mustafa suleyman": ("person", "Mustafa Suleyman"),
    "ilya sutskever": ("person", "Ilya Sutskever"), "mira murati": ("person", "Mira Murati"),
    "greg brockman": ("person", "Greg Brockman"), "ray kurzweil": ("person", "Ray Kurzweil"),
    "yann lecun": ("person", "Yann LeCun"), "geoffrey hinton": ("person", "Geoffrey Hinton"),
    "yoshua bengio": ("person", "Yoshua Bengio"), "andrej karpathy": ("person", "Andrej Karpathy"),
    "naval ravikant": ("person", "Naval Ravikant"), "avi loeb": ("person", "Avi Loeb"),
    "alex wissner-gross": ("person", "Alex Wissner-Gross"),
    "alexander wissner-gross": ("person", "Alex Wissner-Gross"),
    "peter diamandis": ("person", "Peter Diamandis"),
    "peter h. diamandis": ("person", "Peter Diamandis"),
    "dave blundin": ("person", "Dave Blundin"),
    "salim ismail": ("person", "Salim Ismail"),
    "emad mostaque": ("person", "Emad Mostaque"),
    "mo gawdat": ("person", "Mo Gawdat"),
    "brett adcock": ("person", "Brett Adcock"),
    "nat friedman": ("person", "Nat Friedman"),
    "david sinclair": ("person", "David Sinclair"),
    "eric schmidt": ("person", "Eric Schmidt"),
    "vinod khosla": ("person", "Vinod Khosla"),
    "palmer luckey": ("person", "Palmer Luckey"),
    "dara khosrowshahi": ("person", "Dara Khosrowshahi"),
    "amjad masad": ("person", "Amjad Masad"),
    "tristan harris": ("person", "Tristan Harris"),
    "fei-fei li": ("person", "Fei-Fei Li"),
    "andrew ng": ("person", "Andrew Ng"),
    "alexandr wang": ("person", "Alexandr Wang"),
    "jack hidary": ("person", "Jack Hidary"),
    "ramez naam": ("person", "Ramez Naam"),
    "michael saylor": ("person", "Michael Saylor"),
    "marc benioff": ("person", "Marc Benioff"),
    "alvin graylin": ("person", "Alvin Graylin"),
    "simon willison": ("person", "Simon Willison"), "john gruber": ("person", "John Gruber"),
    "cathie wood": ("person", "Cathie Wood"), "ben horowitz": ("person", "Ben Horowitz"),
    "fidji simo": ("person", "Fidji Simo"), "jack clark": ("person", "Jack Clark"),
    "masayoshi son": ("person", "Masayoshi Son"),
    # models / products
    "gpt-4": ("model", "GPT-4"), "gpt-5": ("model", "GPT-5"), "gpt-6": ("model", "GPT-6"),
    "chatgpt": ("model", "ChatGPT"), "claude": ("model", "Claude"),
    "gemini": ("model", "Gemini"), "grok": ("model", "Grok"), "qwen": ("model", "Qwen"),
    "llama": ("model", "Llama"), "deepseek v3": ("model", "DeepSeek-V3"),
    "deepseek r1": ("model", "DeepSeek-R1"), "sora": ("model", "Sora"),
    "veo": ("model", "Veo"), "imagen": ("model", "Imagen"), "copilot": ("model", "Copilot"),
    "devin": ("model", "Devin"), "cursor": ("model", "Cursor"),
    "atlas": ("model", "Atlas"), "optimus": ("model", "Optimus"),
    # tech
    "h100": ("tech", "H100"), "h200": ("tech", "H200"), "b200": ("tech", "B200"),
    "blackwell": ("tech", "Blackwell"), "rubin": ("tech", "Rubin"),
    "tpu": ("tech", "TPU"), "hbm": ("tech", "HBM"), "euv": ("tech", "EUV"),
    "transformer": ("tech", "Transformer"), "mcp": ("tech", "MCP"),
    "world model": ("tech", "World Models"), "starship": ("tech", "Starship"),
    "starlink": ("tech", "Starlink"), "terafab": ("tech", "Terafab"),
    "stargate": ("tech", "Stargate"), "colossus": ("tech", "Colossus"),
    # places
    "san francisco": ("place", "San Francisco"), "new york": ("place", "New York"),
    "london": ("place", "London"), "paris": ("place", "Paris"),
    "beijing": ("place", "Beijing"), "shanghai": ("place", "Shanghai"),
    "hangzhou": ("place", "Hangzhou"), "shenzhen": ("place", "Shenzhen"),
    "taiwan": ("place", "Taiwan"), "hsinchu": ("place", "Hsinchu"),
    "ohio": ("place", "Ohio"), "texas": ("place", "Texas"), "austin": ("place", "Austin"),
    "memphis": ("place", "Memphis"), "abilene": ("place", "Abilene"),
    "arizona": ("place", "Arizona"), "phoenix": ("place", "Phoenix"),
    "washington": ("place", "Washington"), "brussels": ("place", "Brussels"),
    "davos": ("place", "Davos"), "las vegas": ("place", "Las Vegas"),
    "boca chica": ("place", "Boca Chica"), "cape canaveral": ("place", "Cape Canaveral"),
}

# Pre-compile: longest phrases first so multi-word entities win.
_GAZETTEER_SORTED = sorted(GAZETTEER.keys(), key=len, reverse=True)
_ENTITY_RE = {
    k: re.compile(r"\b" + re.escape(k) + r"\b", re.IGNORECASE) for k in _GAZETTEER_SORTED
}
_KEYWORD_RE = {
    # single tokens get an optional plural 's' (gpu→gpus, robot→robots, datacenter→datacenters)
    v: [re.compile(re.escape(kw) if " " in kw or "-" in kw else r"\b" + re.escape(kw) + r"s?\b",
                   re.IGNORECASE)
        for kw in kws]
    for v, kws in VECTOR_KEYWORDS.items()
}

# City -> (lat, lon) for LOCATED relations / globe event placement.
PLACE_GEO: dict[str, tuple[float, float]] = {
    "San Francisco": (37.77, -122.41), "New York": (40.71, -74.00),
    "London": (51.50, -0.12), "Paris": (48.86, 2.35),
    "Beijing": (39.90, 116.40), "Shanghai": (31.23, 121.47),
    "Hangzhou": (30.27, 120.16), "Shenzhen": (22.54, 114.06),
    "Taiwan": (23.70, 121.00), "Hsinchu": (24.78, 121.00),
    "Ohio": (40.42, -82.90), "Texas": (31.00, -100.00), "Austin": (30.27, -97.74),
    "Memphis": (35.15, -90.05), "Abilene": (32.45, -99.73),
    "Arizona": (34.05, -111.09), "Phoenix": (33.45, -112.07),
    "Washington": (38.90, -77.04), "Brussels": (50.85, 4.35),
    "Davos": (46.80, 9.83), "Las Vegas": (36.17, -115.14),
    "Boca Chica": (25.99, -97.15), "Cape Canaveral": (28.39, -80.60),
}


def classify_text(text: str) -> dict[str, float]:
    """Return {vector: score} for a text. Score = number of distinct keyword hits."""
    scores: dict[str, float] = {}
    for vector, regexes in _KEYWORD_RE.items():
        hits = sum(1 for rx in regexes if rx.search(text))
        if hits:
            scores[vector] = float(hits)
    return scores


def extract_entities(text: str) -> list[dict]:
    """Return [{'name': canonical, 'type': kind}] found in text (deduped)."""
    found: list[dict] = []
    seen: set[str] = set()
    for key in _GAZETTEER_SORTED:
        rx = _ENTITY_RE[key]
        if rx.search(text):
            etype, canonical = GAZETTEER[key]
            if canonical not in seen:
                seen.add(canonical)
                found.append({"name": canonical, "type": etype})
    return found


def extract_places(text: str) -> list[dict]:
    """Return [{'name', 'lat', 'lon'}] for known places mentioned in text."""
    out = []
    for e in extract_entities(text):
        if e["type"] == "place" and e["name"] in PLACE_GEO:
            lat, lon = PLACE_GEO[e["name"]]
            out.append({"name": e["name"], "lat": lat, "lon": lon})
    return out


def top_vectors(scores: dict[str, float], k: int = 3) -> list[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]


def salience(text: str, scores: dict[str, float]) -> float:
    """Crude salience: keyword density + entity count, log-scaled."""
    n_ent = len(extract_entities(text))
    total = sum(scores.values())
    import math
    return round(math.log1p(total * 2 + n_ent * 3), 3)
