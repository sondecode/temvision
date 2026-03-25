"""Item active cooldown tracker.

Tracks active item cooldowns (Zhonya's, Guardian Angel, etc.)
using Live Client API item data. Shows cooldown timers on the overlay.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Active item cooldowns (seconds) keyed by item displayName substring.
ITEM_COOLDOWNS: dict[str, float] = {
    "Zhonya's Hourglass": 120.0,
    "Guardian Angel": 300.0,
    "Stopwatch": 0.0,  # one-time use
    "Hextech Rocketbelt": 40.0,
    "Galeforce": 90.0,
    "Goredrinker": 15.0,
    "Stridebreaker": 20.0,
    "Gargoyle Stoneplate": 90.0,
    "Randuin's Omen": 60.0,
    "Locket of the Iron Solari": 90.0,
    "Redemption": 120.0,
    "Mikael's Blessing": 120.0,
    "Shurelya's Battlesong": 75.0,
    "Everfrost": 30.0,
    "Youmuu's Ghostblade": 45.0,
    "Edge of Night": 40.0,
    "Mercurial Scimitar": 90.0,
    "Quicksilver Sash": 90.0,
}


@dataclass
class ItemCooldownState:
    """Tracks a single active item's cooldown for one player."""

    item_name: str = ""
    base_cooldown: float = 0.0
    used_at_game_time: float = -1.0  # -1 = never used
    available: bool = True
    consumed: bool = False  # one-time items like Stopwatch

    def remaining(self, current_game_time: float) -> float:
        if self.available or self.consumed or self.used_at_game_time < 0:
            return 0.0
        elapsed = current_game_time - self.used_at_game_time
        return max(0.0, self.base_cooldown - elapsed)

    def update(self, current_game_time: float) -> None:
        if self.consumed:
            return
        if not self.available and self.remaining(current_game_time) <= 0:
            self.available = True


@dataclass
class PlayerItems:
    """Tracked active items for a single player."""

    champion_name: str = ""
    actives: list[ItemCooldownState] = field(default_factory=list)

    def to_overlay_line(self, current_game_time: float) -> str:
        parts: list[str] = []
        for item in self.actives:
            if item.consumed:
                parts.append(f"❌ {item.item_name}")
            elif item.available:
                parts.append(f"✅ {item.item_name}")
            else:
                rem = item.remaining(current_game_time)
                secs = int(rem)
                parts.append(f"⏳ {item.item_name} {secs}s")
        if not parts:
            return ""
        return f"{self.champion_name}: {' | '.join(parts)}"


class ItemTracker:
    """Track active-item cooldowns for all players.

    Call ``refresh_items()`` each slow tick with player item lists
    from the Live Client API. Call ``mark_used()`` when an item
    active event is detected (via events or OCR).
    """

    def __init__(self) -> None:
        self._players: dict[str, PlayerItems] = {}

    def refresh_items(
        self, champion_name: str, items: list[dict]
    ) -> None:
        """Update known items for a champion from Live Client API.

        *items* is the raw item list from GameData player (list of
        dicts with ``displayName`` keys).
        """
        existing = self._players.get(champion_name)
        existing_names: set[str] = set()
        if existing:
            existing_names = {a.item_name for a in existing.actives}

        actives: list[ItemCooldownState] = []
        if existing:
            actives = list(existing.actives)

        for raw_item in items:
            name = raw_item.get("displayName", "")
            cd = self._lookup_cooldown(name)
            if cd is None:
                continue
            if name in existing_names:
                continue  # already tracking
            actives.append(
                ItemCooldownState(
                    item_name=name,
                    base_cooldown=cd,
                    available=True,
                    consumed=(cd == 0.0),
                )
            )

        self._players[champion_name] = PlayerItems(
            champion_name=champion_name, actives=actives
        )

    def mark_used(
        self, champion_name: str, item_name: str, game_time: float
    ) -> None:
        """Record that a champion used an active item."""
        pi = self._players.get(champion_name)
        if pi is None:
            return
        for item in pi.actives:
            if item.item_name == item_name:
                if item.base_cooldown == 0.0:
                    item.consumed = True
                else:
                    item.used_at_game_time = game_time
                    item.available = False
                return

    def update(self, current_game_time: float) -> None:
        """Tick all item cooldowns."""
        for pi in self._players.values():
            for item in pi.actives:
                item.update(current_game_time)

    def get_enemy_lines(
        self, enemy_champions: list[str], current_game_time: float
    ) -> list[str]:
        """Return overlay lines for enemy active items on CD."""
        self.update(current_game_time)
        lines: list[str] = []
        for champ in enemy_champions:
            pi = self._players.get(champ)
            if pi is None:
                continue
            line = pi.to_overlay_line(current_game_time)
            if line:
                lines.append(line)
        return lines

    def reset(self) -> None:
        self._players.clear()

    @staticmethod
    def _lookup_cooldown(item_name: str) -> Optional[float]:
        """Return the cooldown for an active item, or None if not active."""
        for key, cd in ITEM_COOLDOWNS.items():
            if key in item_name:
                return cd
        return None
