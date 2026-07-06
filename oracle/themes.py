"""oracle/themes.py — the forming-themes map for the thematic net (2026-07-06).

Top-down sourcing: an under-covered name sitting in front of a forming SECTOR wave
whose own numbers may not have bent yet (spec §3 top_down). The map is
OPERATOR-EDITABLE — themes rotate as waves form and decay (the moat is the
rotation). Each theme has:
  tight_industries  — industries specific enough that membership alone signals the
                      theme (fires at 0.6);
  keywords          — substrings in the business name/description that fire the
                      theme even from a broad industry like Biotechnology (fires at
                      1.0, since it's a targeted match, not a whole-sector sweep).

Deliberately selective: a broad industry (Biotechnology, Software) does NOT fire a
theme on industry alone — only a keyword match does — so the thematic net stays a
signal, not a whole-sector rubber stamp. The net is weighted modestly in the
composite; it earns its keep by CORROBORATING the fundamental nets on a name the
market hasn't connected to the wave, not by carrying a name alone.
"""
from __future__ import annotations

from typing import Optional

FORMING_THEMES: dict[str, dict] = {
    "ai_compute": {
        "tight_industries": {"Semiconductors", "Semiconductor Equipment & Materials"},
        "keywords": ("semiconductor", "photonic", "optical interconnect", "data center",
                     "gpu", "accelerator", "inference", "advanced packaging", "hbm"),
    },
    "power_electrification": {
        "tight_industries": {"Electrical Equipment & Parts"},
        "keywords": ("grid", "transformer", "switchgear", "transmission", "power management",
                     "electrification", "busbar", "power distribution"),
    },
    "defense": {
        "tight_industries": {"Aerospace & Defense"},
        "keywords": ("defense", "missile", "radar", "munition", "drone", "hypersonic",
                     "electronic warfare", "autonomy"),
    },
    "reshoring_infra": {
        "tight_industries": {"Engineering & Construction"},
        "keywords": ("infrastructure", "reshoring", "industrial automation", "onshoring",
                     "capacity expansion"),
    },
    "obesity_metabolic": {
        "tight_industries": set(),
        "keywords": ("glp-1", "glp1", "obesity", "incretin", "metabolic", "weight loss",
                     "amylin", "gipr"),
    },
    "nuclear_uranium": {
        "tight_industries": {"Uranium"},
        "keywords": ("nuclear", "uranium", "reactor", "smr", "enrichment"),
    },
}

# themes considered FORMING right now (operator-editable; drives which fire)
ACTIVE_THEMES: set[str] = set(FORMING_THEMES.keys())


def tag_theme(industry: Optional[str], name: str = "", description: str = "",
              active: Optional[set[str]] = None) -> Optional[dict]:
    """Return {"theme", "theme_strength"} for the first forming theme this name
    matches, else None. Keyword match (1.0) beats a tight-industry match (0.6).
    Only ACTIVE themes fire."""
    active = active if active is not None else ACTIVE_THEMES
    hay = f"{name} {description}".lower()
    ind = (industry or "").strip()
    industry_hit = None
    for theme in active:
        spec = FORMING_THEMES.get(theme)
        if not spec:
            continue
        if any(k in hay for k in spec["keywords"]):
            return {"theme": theme, "theme_strength": 1.0}       # targeted keyword match
        if industry_hit is None and ind in spec["tight_industries"]:
            industry_hit = theme
    if industry_hit:
        return {"theme": industry_hit, "theme_strength": 0.6}    # whole-sector membership
    return None
