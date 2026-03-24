"""Event detection engine for LoL overlay.

Detects game events by tracking state changes over time:
- Enemy missing (jungle/laner not visible)
- Level up (power spike detection)
- Power spike (key item completions, ultimate availability)
- Jungle gank risk assessment
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import GameData, PlayerData

logger = logging.getLogger(__name__)


@dataclass
class GameEvent:
    """Represents a detected game event."""

    event_type: str
    message: str
    priority: str = "normal"
    icon: str = ""
    timestamp: float = 0.0
    metadata: dict = field(default_factory=dict)

    @property
    def display_text(self) -> str:
        """Return formatted display text with icon."""
        if self.icon:
            return f"{self.icon} {self.message}"
        return self.message


# Key levels that represent power spikes in League of Legends
POWER_SPIKE_LEVELS = {6, 11, 16}

# Thresholds for event detection
@dataclass
class EventThresholds:
    """Configurable thresholds for event detection."""

    enemy_missing_seconds: float = 20.0
    jungle_missing_seconds: float = 15.0
    hp_burst_threshold: float = 20.0
    combat_hp_drop_threshold: float = 10.0


class EventEngine:
    """Detects game events by comparing successive game states.

    Tracks:
    - Enemy visibility (missing detection)
    - Level changes (level-up / power spike)
    - HP changes (burst / combat detection)
    - Jungle position (gank risk)
    """

    def __init__(self, thresholds: Optional[EventThresholds] = None):
        self.thresholds = thresholds or EventThresholds()

        # Tracking state
        self._previous_game_data: Optional[GameData] = None
        self._enemy_last_seen: dict = {}  # champion_name -> timestamp
        self._previous_levels: dict = {}  # champion_name -> level
        self._previous_hp: dict = {}  # champion_name -> hp_percent

    def process(self, game_data: GameData) -> list:
        """Process a game state snapshot and return detected events.

        Args:
            game_data: Current game state.

        Returns:
            List of GameEvent objects.
        """
        events = []

        if game_data.active_player is None:
            self._previous_game_data = game_data
            return events

        now = game_data.game_time

        events.extend(self._detect_enemy_missing(game_data, now))
        events.extend(self._detect_level_ups(game_data))
        events.extend(self._detect_power_spikes(game_data))
        events.extend(self._detect_jungle_gank_risk(game_data, now))
        events.extend(self._detect_combat(game_data))

        self._update_tracking(game_data, now)
        self._previous_game_data = game_data

        return events

    def reset(self):
        """Reset all tracking state."""
        self._previous_game_data = None
        self._enemy_last_seen.clear()
        self._previous_levels.clear()
        self._previous_hp.clear()

    def _detect_enemy_missing(
        self, game_data: GameData, now: float
    ) -> list:
        """Detect enemies that have been missing for too long."""
        events = []

        for enemy in game_data.enemies:
            name = enemy.champion_name
            if not name:
                continue

            if enemy.is_dead:
                # Dead enemies are accounted for, update last seen
                self._enemy_last_seen[name] = now
                continue

            # If enemy is visible (has recent score updates), mark as seen
            # In the Live Client API, we infer visibility from data freshness
            # For now, we track based on whether enemy state changed
            if self._previous_game_data is not None:
                prev_enemy = self._find_enemy(
                    self._previous_game_data, name
                )
                if prev_enemy is not None:
                    # Check if any stats changed (indicates visibility)
                    if (
                        enemy.kills != prev_enemy.kills
                        or enemy.deaths != prev_enemy.deaths
                        or enemy.assists != prev_enemy.assists
                        or enemy.creep_score != prev_enemy.creep_score
                        or enemy.level != prev_enemy.level
                    ):
                        self._enemy_last_seen[name] = now
                        continue

            # Check if enemy has been missing too long
            last_seen = self._enemy_last_seen.get(name, now)
            missing_duration = now - last_seen

            if missing_duration > self.thresholds.enemy_missing_seconds:
                events.append(
                    GameEvent(
                        event_type="enemy_missing",
                        message=f"{name} missing for {missing_duration:.0f}s - be careful!",
                        priority="high",
                        icon="⚠️",
                        timestamp=now,
                        metadata={
                            "champion": name,
                            "duration": missing_duration,
                        },
                    )
                )

        return events

    def _detect_level_ups(self, game_data: GameData) -> list:
        """Detect level-up events for the active player."""
        events = []
        player = game_data.active_player
        name = player.champion_name

        prev_level = self._previous_levels.get(name, 0)

        if prev_level > 0 and player.level > prev_level:
            events.append(
                GameEvent(
                    event_type="level_up",
                    message=f"Level up! Now level {player.level}",
                    priority="normal",
                    icon="⬆️",
                    timestamp=game_data.game_time,
                    metadata={
                        "champion": name,
                        "new_level": player.level,
                        "old_level": prev_level,
                    },
                )
            )

        return events

    def _detect_power_spikes(self, game_data: GameData) -> list:
        """Detect power spike events (key level thresholds)."""
        events = []
        player = game_data.active_player
        name = player.champion_name

        prev_level = self._previous_levels.get(name, 0)

        if (
            prev_level > 0
            and player.level > prev_level
            and player.level in POWER_SPIKE_LEVELS
        ):
            if player.level == 6:
                msg = "POWER SPIKE! Ultimate unlocked - look for aggressive plays"
            elif player.level == 11:
                msg = "POWER SPIKE! Level 11 - ultimate upgraded"
            else:
                msg = "POWER SPIKE! Level 16 - ultimate maxed"

            events.append(
                GameEvent(
                    event_type="power_spike",
                    message=msg,
                    priority="high",
                    icon="🔥",
                    timestamp=game_data.game_time,
                    metadata={
                        "champion": name,
                        "level": player.level,
                        "spike_type": "level",
                    },
                )
            )

        # Detect enemy power spikes too
        for enemy in game_data.enemies:
            ename = enemy.champion_name
            eprev = self._previous_levels.get(ename, 0)
            if (
                eprev > 0
                and enemy.level > eprev
                and enemy.level in POWER_SPIKE_LEVELS
            ):
                events.append(
                    GameEvent(
                        event_type="enemy_power_spike",
                        message=f"⚠️ {ename} hit level {enemy.level} - be cautious!",
                        priority="high",
                        icon="🔶",
                        timestamp=game_data.game_time,
                        metadata={
                            "champion": ename,
                            "level": enemy.level,
                            "spike_type": "level",
                        },
                    )
                )

        return events

    def _detect_jungle_gank_risk(
        self, game_data: GameData, now: float
    ) -> list:
        """Assess jungle gank risk based on enemy jungler visibility."""
        events = []

        # Find enemy jungler
        jungler = game_data.get_enemy_by_position("JUNGLE")
        if jungler is None:
            return events

        jname = jungler.champion_name
        if not jname or jungler.is_dead:
            return events

        last_seen = self._enemy_last_seen.get(jname, now)
        missing_duration = now - last_seen

        if missing_duration > self.thresholds.jungle_missing_seconds:
            events.append(
                GameEvent(
                    event_type="gank_risk",
                    message=f"Possible gank! {jname} missing {missing_duration:.0f}s",
                    priority="critical",
                    icon="🚨",
                    timestamp=now,
                    metadata={
                        "jungler": jname,
                        "missing_duration": missing_duration,
                    },
                )
            )

        return events

    def _detect_combat(self, game_data: GameData) -> list:
        """Detect if the active player is in combat (rapid HP drop)."""
        events = []
        player = game_data.active_player
        name = player.champion_name

        prev_hp = self._previous_hp.get(name)
        if prev_hp is not None:
            hp_drop = prev_hp - player.hp_percent
            if hp_drop > self.thresholds.hp_burst_threshold:
                events.append(
                    GameEvent(
                        event_type="combat_burst",
                        message=f"Taking heavy damage! HP dropped {hp_drop:.0f}%",
                        priority="critical",
                        icon="💥",
                        timestamp=game_data.game_time,
                        metadata={
                            "hp_drop": hp_drop,
                            "current_hp_pct": player.hp_percent,
                        },
                    )
                )
            elif hp_drop > self.thresholds.combat_hp_drop_threshold:
                events.append(
                    GameEvent(
                        event_type="combat_detected",
                        message="In combat - watch your health",
                        priority="high",
                        icon="⚔️",
                        timestamp=game_data.game_time,
                        metadata={
                            "hp_drop": hp_drop,
                            "current_hp_pct": player.hp_percent,
                        },
                    )
                )

        return events

    def _update_tracking(self, game_data: GameData, now: float):
        """Update internal tracking state after processing."""
        # Track active player
        if game_data.active_player:
            p = game_data.active_player
            self._previous_levels[p.champion_name] = p.level
            self._previous_hp[p.champion_name] = p.hp_percent

        # Track enemy levels
        for enemy in game_data.enemies:
            if enemy.champion_name:
                self._previous_levels[enemy.champion_name] = enemy.level

        # Initialize last_seen for new enemies
        for enemy in game_data.enemies:
            if enemy.champion_name and enemy.champion_name not in self._enemy_last_seen:
                self._enemy_last_seen[enemy.champion_name] = now

    def _find_enemy(
        self, game_data: GameData, champion_name: str
    ) -> Optional[PlayerData]:
        """Find an enemy player by champion name in a game state."""
        for enemy in game_data.enemies:
            if enemy.champion_name == champion_name:
                return enemy
        return None
