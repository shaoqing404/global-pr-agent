from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


DEFAULT_MARKET = {
    "language_hint": "English",
    "media_style": "clear, localized, credible, benefit-led",
    "cultural_notes": ["Explain local customer value early.", "Avoid unsupported claims."],
    "channels": ["LinkedIn", "industry media", "local PR wire"],
    "risk_notes": ["Require local legal and brand review before publishing."],
}


def load_market_playbook(path: str = "data/market_playbook.json") -> Dict[str, Dict[str, Any]]:
    file_path = Path(path)
    if not file_path.exists():
        file_path = Path(__file__).resolve().parents[2] / "data" / "market_playbook.json"
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_market_profile(target_market: str) -> Dict[str, Any]:
    playbook = load_market_playbook()
    if target_market in playbook:
        return playbook[target_market]
    for market_name, profile in playbook.items():
        if target_market.lower() in market_name.lower() or market_name.lower() in target_market.lower():
            return profile
    return DEFAULT_MARKET


def list_markets() -> list[str]:
    return sorted(load_market_playbook().keys())
