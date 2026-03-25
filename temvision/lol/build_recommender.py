"""Rune and item build recommender + LCU auto-import.

Provides per-champion recommended runes and starting items, and
can import rune pages directly into the League Client via LCU API.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.lcu_client import LCUClient

logger = logging.getLogger(__name__)

_BUNDLED_BUILDS_PATH = os.path.join(
    os.path.dirname(__file__), "data", "builds.json"
)


@dataclass
class RunePage:
    """A rune page recommendation."""

    name: str = ""
    primary_style: int = 0        # e.g. 8100 = Domination
    sub_style: int = 0            # e.g. 8300 = Inspiration
    selected_perks: list[int] = field(default_factory=list)  # 6 perk IDs
    stat_shards: list[int] = field(default_factory=list)     # 3 stat IDs


@dataclass
class BuildRecommendation:
    """Champion + lane build recommendation."""

    champion: str = ""
    lane: str = ""
    rune_page: Optional[RunePage] = None
    starting_items: list[str] = field(default_factory=list)
    core_items: list[str] = field(default_factory=list)
    summoner_spells: list[str] = field(default_factory=list)
    skill_order: str = ""
    win_rate: float = 0.0
    source: str = "bundled"       # "bundled" | "opgg" | "custom"


class BuildRecommender:
    """Look up recommended builds for a champion+lane.

    Uses a bundled JSON file. Extensible later to fetch from OP.GG/
    community APIs.
    """

    def __init__(self, builds_path: str = _BUNDLED_BUILDS_PATH) -> None:
        self._builds_path = builds_path
        self._data: dict = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self._builds_path):
            logger.debug("Builds file not found: %s", self._builds_path)
            return {}
        try:
            with open(self._builds_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load builds: %s", exc)
            return {}

    def recommend(
        self, champion: str, lane: str = ""
    ) -> Optional[BuildRecommendation]:
        """Return a build recommendation for *champion* in *lane*.

        Falls back to default lane if the requested lane isn't found.
        """
        champ_key = champion.lower()
        champ_data = self._data.get(champ_key)
        if champ_data is None:
            return None

        lane_key = lane.lower() if lane else "default"
        build_raw = champ_data.get(lane_key) or champ_data.get("default")
        if build_raw is None:
            return None

        rec = BuildRecommendation(
            champion=champion,
            lane=lane or "default",
            starting_items=build_raw.get("starting_items", []),
            core_items=build_raw.get("core_items", []),
            summoner_spells=build_raw.get("summoner_spells", ["Flash", "Teleport"]),
            skill_order=build_raw.get("skill_order", ""),
            win_rate=build_raw.get("win_rate", 0.0),
            source="bundled",
        )

        rune_raw = build_raw.get("runes")
        if rune_raw:
            rec.rune_page = RunePage(
                name=rune_raw.get("name", f"Temvision - {champion}"),
                primary_style=rune_raw.get("primary_style", 0),
                sub_style=rune_raw.get("sub_style", 0),
                selected_perks=rune_raw.get("selected_perks", []),
                stat_shards=rune_raw.get("stat_shards", []),
            )

        return rec

    def overlay_lines(self, rec: BuildRecommendation) -> list[str]:
        """Format a recommendation into overlay display lines."""
        lines: list[str] = []
        lines.append(
            f"🏗️  Build: {rec.champion} ({rec.lane}) "
            f"[{rec.win_rate:.0f}% WR]"
        )
        if rec.starting_items:
            lines.append(f"  Start: {', '.join(rec.starting_items)}")
        if rec.core_items:
            lines.append(f"  Core:  {', '.join(rec.core_items)}")
        if rec.skill_order:
            lines.append(f"  Skills: {rec.skill_order}")
        return lines


class RuneImporter:
    """Import rune pages into the League Client via LCU API."""

    def __init__(self, lcu: Optional[LCUClient] = None) -> None:
        self._lcu = lcu or LCUClient()

    def import_runes(self, page: RunePage) -> bool:
        """Push a RunePage into the League Client.

        Returns True if import succeeded. Requires LCU to be running.
        """
        if not self._lcu.is_running():
            logger.debug("LCU not running – cannot import runes")
            return False

        # Delete existing "Temvision" pages first
        existing = self._lcu.get("/lol-perks/v1/pages")
        if isinstance(existing, list):
            for p in existing:
                if p.get("name", "").startswith("Temvision") and p.get("isDeletable"):
                    pid = p.get("id")
                    if pid:
                        self._lcu.get(f"/lol-perks/v1/pages/{pid}")  # read
                        self._delete_page(pid)

        payload = {
            "name": page.name or "Temvision",
            "primaryStyleId": page.primary_style,
            "subStyleId": page.sub_style,
            "selectedPerkIds": page.selected_perks + page.stat_shards,
            "current": True,
        }

        result = self._lcu_post("/lol-perks/v1/pages", payload)
        if result is not None:
            logger.info("Rune page imported: %s", page.name)
            return True
        return False

    def _delete_page(self, page_id: int) -> None:
        """Delete an existing rune page by ID."""
        lock = self._lcu._read_lockfile()
        if lock is None:
            return
        import requests
        import base64
        url = f"{self._lcu._build_base_url(lock)}/lol-perks/v1/pages/{page_id}"
        headers = self._lcu._headers(lock)
        try:
            requests.delete(url, headers=headers, timeout=2.0, verify=False)
        except Exception as exc:
            logger.debug("Failed to delete rune page %d: %s", page_id, exc)

    def _lcu_post(self, path: str, payload: dict) -> Optional[dict]:
        """POST request to LCU API."""
        lock = self._lcu._read_lockfile()
        if lock is None:
            return None
        import requests
        import base64
        url = f"{self._lcu._build_base_url(lock)}{path}"
        headers = self._lcu._headers(lock)
        headers["Content-Type"] = "application/json"
        try:
            resp = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=2.0,
                verify=False,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.debug("LCU POST %s failed: %s", path, exc)
            return None
