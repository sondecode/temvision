"""Summoner spell cooldown tracker.

Tracks Flash, Teleport, Ignite, etc. cooldowns for all players.
Uses events from the Live Client API and manual tab-press timestamps.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Base cooldown durations (seconds) for common summoner spells.
# Cosmic Insight / Lucidity Boots reduce these by ~5-18 s.
SPELL_COOLDOWNS: dict[str, float] = {
    "Flash": 300.0,
    "Teleport": 360.0,
    "Ignite": 180.0,
    "Heal": 240.0,
    "Barrier": 180.0,
    "Exhaust": 210.0,
    "Ghost": 210.0,
    "Cleanse": 210.0,
    "Smite": 90.0,
    "Mark": 80.0,       # ARAM snowball
}


@dataclass
class SpellState:
    """Tracks a single summoner spell's cooldown for one player."""

    spell_name: str = ""
    base_cooldown: float = 0.0
    used_at_game_time: float = 0.0  # game-time when used (0 = never)
    available: bool = True

    def remaining(self, current_game_time: float) -> float:
        """Seconds until the spell is available again."""
        if self.available:
            return 0.0
        elapsed = current_game_time - self.used_at_game_time
        return max(0.0, self.base_cooldown - elapsed)

    def update(self, current_game_time: float) -> None:
        """Refresh availability flag."""
        if not self.available and self.remaining(current_game_time) <= 0:
            self.available = True


@dataclass
class PlayerSpells:
    """Pair of summoner spells for a single player."""

    summoner_name: str = ""
    champion_name: str = ""
    spell1: SpellState = field(default_factory=SpellState)
    spell2: SpellState = field(default_factory=SpellState)

    def to_overlay_line(self, current_game_time: float) -> str:
        """Format a compact overlay line showing spell availability/CD."""
        s1 = self._fmt(self.spell1, current_game_time)
        s2 = self._fmt(self.spell2, current_game_time)
        return f"{self.champion_name}: {s1}  {s2}"

    @staticmethod
    def _fmt(spell: SpellState, game_time: float) -> str:
        if spell.available:
            return f"✅ {spell.spell_name}"
        rem = spell.remaining(game_time)
        minutes, secs = divmod(int(rem), 60)
        return f"⏳ {spell.spell_name} {minutes}:{secs:02d}"


class SpellTracker:
    """Track summoner spell cooldowns across all 10 players.

    Two ways to register spell usage:
    1. API-based: Call ``mark_used()`` when a spell-used event is detected.
    2. Manual: Future OCR/tab-press detection can call ``mark_used()`` too.
    """

    def __init__(self) -> None:
        self._players: dict[str, PlayerSpells] = {}  # key = champion_name

    def register_player(
        self,
        champion_name: str,
        summoner_name: str,
        spell1_name: str,
        spell2_name: str,
    ) -> None:
        """Register or update a player's spells at game start."""
        self._players[champion_name] = PlayerSpells(
            summoner_name=summoner_name,
            champion_name=champion_name,
            spell1=SpellState(
                spell_name=spell1_name,
                base_cooldown=SPELL_COOLDOWNS.get(spell1_name, 300.0),
                available=True,
            ),
            spell2=SpellState(
                spell_name=spell2_name,
                base_cooldown=SPELL_COOLDOWNS.get(spell2_name, 300.0),
                available=True,
            ),
        )

    def mark_used(
        self,
        champion_name: str,
        spell_name: str,
        game_time: float,
    ) -> None:
        """Record that a champion used a summoner spell."""
        ps = self._players.get(champion_name)
        if ps is None:
            return
        for spell in (ps.spell1, ps.spell2):
            if spell.spell_name == spell_name:
                spell.used_at_game_time = game_time
                spell.available = False
                logger.debug(
                    "%s used %s at %.1f", champion_name, spell_name, game_time
                )
                return

    def update(self, current_game_time: float) -> None:
        """Tick all spell states to refresh availability."""
        for ps in self._players.values():
            ps.spell1.update(current_game_time)
            ps.spell2.update(current_game_time)

    def get_enemy_lines(
        self,
        enemy_champions: list[str],
        current_game_time: float,
    ) -> list[str]:
        """Return compact overlay lines for enemy spell CDs."""
        self.update(current_game_time)
        lines: list[str] = []
        for champ in enemy_champions:
            ps = self._players.get(champ)
            if ps is not None:
                lines.append(ps.to_overlay_line(current_game_time))
        return lines

    def get_all_on_cd(self, current_game_time: float) -> list[dict]:
        """Return dicts of spells currently on cooldown (for overlay)."""
        result: list[dict] = []
        self.update(current_game_time)
        for ps in self._players.values():
            for spell in (ps.spell1, ps.spell2):
                if not spell.available:
                    result.append({
                        "champion": ps.champion_name,
                        "spell": spell.spell_name,
                        "remaining": spell.remaining(current_game_time),
                    })
        return result

    def reset(self) -> None:
        """Clear all tracking data."""
        self._players.clear()
