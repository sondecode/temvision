"""Champion metadata loader (ID -> name/icon alias).

Uses a small bundled cache at temvision/lol/data/champions.json.
For extensibility, can be extended later to fetch from Data Dragon.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

_BUNDLED_PATH = os.path.join(
    os.path.dirname(__file__), "data", "champions.json"
)


class ChampionMapper:
    """Resolve champion_id to champion name and alias."""

    def __init__(self, json_path: str = _BUNDLED_PATH) -> None:
        self.json_path = json_path
        self._data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.json_path):
            logger.warning("Champion map missing: %s", self.json_path)
            return {"by_id": {}}
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load champion map: %s", exc)
            return {"by_id": {}}

    @lru_cache(maxsize=1024)
    def by_id(self, champion_id: int) -> Optional[dict]:
        return self._data.get("by_id", {}).get(str(champion_id))

    def name(self, champion_id: int) -> str:
        entry = self.by_id(champion_id)
        return entry.get("name") if entry else "Unknown"

    def alias(self, champion_id: int) -> str:
        entry = self.by_id(champion_id)
        return entry.get("alias") if entry else ""
