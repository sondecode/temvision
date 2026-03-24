"""Objective tracker for LoL overlay.

Tracks major objective timers and provides AI-driven suggestions:
- Dragon timer and type tracking
- Baron Nashor timer
- Rift Herald timer
- Buff timers (Red/Blue)

Parses game events from the Live Client API to detect objective kills
and calculates respawn timers.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import GameData

logger = logging.getLogger(__name__)

# Objective respawn times (seconds)
DRAGON_RESPAWN = 300.0  # 5 minutes
BARON_RESPAWN = 360.0  # 6 minutes
HERALD_DESPAWN_TIME = 1200.0  # Herald despawns at 20 min (replaced by Baron)
BARON_SPAWN_TIME = 1200.0  # Baron spawns at 20 min
BUFF_RESPAWN = 300.0  # 5 minutes


@dataclass
class ObjectiveState:
    """Tracks the state of a single objective."""

    name: str = ""
    alive: bool = True
    last_killed_time: float = 0.0
    respawn_time: float = 0.0
    next_spawn_time: float = 0.0
    kill_count: int = 0
    killed_by_team: str = ""  # "ORDER" or "CHAOS"

    @property
    def time_until_spawn(self) -> float:
        """Seconds until the objective respawns (0 if alive)."""
        if self.alive:
            return 0.0
        return max(0.0, self.next_spawn_time - self.last_killed_time)

    def remaining_time(self, current_time: float) -> float:
        """Remaining seconds until respawn given current game time."""
        if self.alive:
            return 0.0
        return max(0.0, self.next_spawn_time - current_time)


@dataclass
class ObjectiveTimers:
    """All tracked objective timers."""

    dragon: ObjectiveState = field(
        default_factory=lambda: ObjectiveState(
            name="Dragon", respawn_time=DRAGON_RESPAWN
        )
    )
    baron: ObjectiveState = field(
        default_factory=lambda: ObjectiveState(
            name="Baron", respawn_time=BARON_RESPAWN
        )
    )
    herald: ObjectiveState = field(
        default_factory=lambda: ObjectiveState(
            name="Herald", respawn_time=0.0
        )
    )
    dragon_kills_ally: int = 0
    dragon_kills_enemy: int = 0
    dragon_types: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for display or serialization."""
        return {
            "dragon": {
                "alive": self.dragon.alive,
                "kill_count": self.dragon.kill_count,
                "next_spawn_time": self.dragon.next_spawn_time,
            },
            "baron": {
                "alive": self.baron.alive,
                "kill_count": self.baron.kill_count,
                "next_spawn_time": self.baron.next_spawn_time,
            },
            "herald": {
                "alive": self.herald.alive,
                "kill_count": self.herald.kill_count,
            },
            "dragon_kills_ally": self.dragon_kills_ally,
            "dragon_kills_enemy": self.dragon_kills_enemy,
            "dragon_types": self.dragon_types,
        }


# Event names from the Live Client API
DRAGON_EVENTS = {"DragonKill"}
BARON_EVENTS = {"BaronKill"}
HERALD_EVENTS = {"HeraldKill"}


class ObjectiveTracker:
    """Tracks objective timers from live game events.

    Parses the events list from the Live Client API to detect
    dragon, baron, and herald kills, then calculates respawn timers.
    """

    def __init__(self):
        self._timers = ObjectiveTimers()
        self._processed_events: set = set()
        self._active_player_team: str = ""

    @property
    def timers(self) -> ObjectiveTimers:
        """Return current objective timers."""
        return self._timers

    def process(self, game_data: GameData) -> ObjectiveTimers:
        """Process game data and update objective timers.

        Args:
            game_data: Current game state including events.

        Returns:
            Updated ObjectiveTimers.
        """
        if game_data.active_player is not None:
            self._active_player_team = game_data.active_player.team

        # Update alive status based on game time
        self._update_respawns(game_data.game_time)

        # Process new events
        for event in game_data.events:
            event_id = self._event_id(event)
            if event_id in self._processed_events:
                continue

            event_name = event.get("EventName", "")
            event_time = event.get("EventTime", 0.0)

            if event_name in DRAGON_EVENTS:
                self._on_dragon_kill(event, event_time)
            elif event_name in BARON_EVENTS:
                self._on_baron_kill(event, event_time)
            elif event_name in HERALD_EVENTS:
                self._on_herald_kill(event, event_time)

            self._processed_events.add(event_id)

        return self._timers

    def reset(self):
        """Reset all tracking state."""
        self._timers = ObjectiveTimers()
        self._processed_events.clear()
        self._active_player_team = ""

    def get_suggestions(self, game_data: GameData) -> list:
        """Generate objective-related suggestions.

        Args:
            game_data: Current game state.

        Returns:
            List of suggestion strings with priorities.
        """
        suggestions = []
        game_time = game_data.game_time

        # Dragon spawning soon
        dragon_remaining = self._timers.dragon.remaining_time(game_time)
        if not self._timers.dragon.alive and 0 < dragon_remaining <= 60:
            suggestions.append({
                "text": f"Dragon spawning in {dragon_remaining:.0f}s - prepare!",
                "priority": "high",
                "category": "objective",
            })

        # Baron spawning soon
        baron_remaining = self._timers.baron.remaining_time(game_time)
        if not self._timers.baron.alive and 0 < baron_remaining <= 60:
            suggestions.append({
                "text": f"Baron spawning in {baron_remaining:.0f}s - group!",
                "priority": "critical",
                "category": "objective",
            })

        # Baron available with numbers advantage
        if self._timers.baron.alive and game_time >= BARON_SPAWN_TIME:
            dead_enemies = sum(
                1 for e in game_data.enemies if e.is_dead
            )
            if dead_enemies >= 2:
                suggestions.append({
                    "text": f"Baron available + {dead_enemies} enemies dead - consider Baron!",
                    "priority": "critical",
                    "category": "objective",
                })

        # Dragon advantage/disadvantage
        diff = self._timers.dragon_kills_ally - self._timers.dragon_kills_enemy
        if diff <= -2:
            suggestions.append({
                "text": f"Behind in dragons ({self._timers.dragon_kills_ally} vs {self._timers.dragon_kills_enemy}) - prioritize next dragon",
                "priority": "high",
                "category": "objective",
            })

        return suggestions

    def _on_dragon_kill(self, event: dict, event_time: float):
        """Handle dragon kill event."""
        self._timers.dragon.alive = False
        self._timers.dragon.last_killed_time = event_time
        self._timers.dragon.next_spawn_time = event_time + DRAGON_RESPAWN
        self._timers.dragon.kill_count += 1

        # Track which team killed it
        killer = event.get("KillerName", "")
        dragon_type = event.get("DragonType", "Unknown")
        self._timers.dragon_types.append(dragon_type)

        # Determine team based on killer (simplified)
        killed_by = event.get("Assisters", [])
        self._timers.dragon.killed_by_team = self._guess_killer_team(
            killer, killed_by
        )

        if self._timers.dragon.killed_by_team == self._active_player_team:
            self._timers.dragon_kills_ally += 1
        else:
            self._timers.dragon_kills_enemy += 1

        logger.info(
            "Dragon killed at %.0fs (type: %s). Next spawn: %.0fs",
            event_time,
            dragon_type,
            self._timers.dragon.next_spawn_time,
        )

    def _on_baron_kill(self, event: dict, event_time: float):
        """Handle baron kill event."""
        self._timers.baron.alive = False
        self._timers.baron.last_killed_time = event_time
        self._timers.baron.next_spawn_time = event_time + BARON_RESPAWN
        self._timers.baron.kill_count += 1

        killer = event.get("KillerName", "")
        killed_by = event.get("Assisters", [])
        self._timers.baron.killed_by_team = self._guess_killer_team(
            killer, killed_by
        )

        logger.info(
            "Baron killed at %.0fs. Next spawn: %.0fs",
            event_time,
            self._timers.baron.next_spawn_time,
        )

    def _on_herald_kill(self, event: dict, event_time: float):
        """Handle herald kill event."""
        self._timers.herald.alive = False
        self._timers.herald.last_killed_time = event_time
        self._timers.herald.kill_count += 1

        killer = event.get("KillerName", "")
        killed_by = event.get("Assisters", [])
        self._timers.herald.killed_by_team = self._guess_killer_team(
            killer, killed_by
        )

        logger.info("Herald killed at %.0fs", event_time)

    def _update_respawns(self, game_time: float):
        """Update objective alive status based on respawn timers."""
        # Dragon respawn
        if (
            not self._timers.dragon.alive
            and self._timers.dragon.next_spawn_time > 0
            and game_time >= self._timers.dragon.next_spawn_time
        ):
            self._timers.dragon.alive = True

        # Baron respawn
        if (
            not self._timers.baron.alive
            and self._timers.baron.next_spawn_time > 0
            and game_time >= self._timers.baron.next_spawn_time
        ):
            self._timers.baron.alive = True

    def _guess_killer_team(
        self, killer_name: str, assisters: list
    ) -> str:
        """Best-effort guess of which team killed the objective.

        Uses active player team as default since the Live Client API
        doesn't directly tell us which team killed objectives.
        """
        # Default to active player team (most common case)
        return self._active_player_team or "ORDER"

    def _event_id(self, event: dict) -> str:
        """Create a unique ID for an event to avoid double-processing."""
        return f"{event.get('EventName', '')}_{event.get('EventTime', 0)}"
