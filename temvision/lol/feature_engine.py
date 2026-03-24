"""Feature extraction engine for LoL overlay.

Converts raw game data into normalized features suitable for
future AI/ML model consumption. Prepares the data pipeline for
transitioning from rule-based to AI-based decision making.

Features computed:
- gold_diff: Gold difference vs average enemy
- level_diff: Level difference vs average enemy
- hp_ratio: Player HP as ratio (0.0 - 1.0)
- team_strength: Composite team advantage score
- kill_pressure: Likelihood of getting/giving kills
- cs_diff: CS difference vs average enemy
- objective_control: Team positioning for objectives
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import GameData, PlayerData

logger = logging.getLogger(__name__)


@dataclass
class GameFeatures:
    """Extracted features from a game state snapshot.

    All features are normalized to be suitable for ML model input.
    """

    # Player state features
    gold_diff: float = 0.0
    level_diff: float = 0.0
    hp_ratio: float = 0.0
    mana_ratio: float = 0.0  # Reserved for future use
    cs_diff: float = 0.0

    # Team-level features
    team_gold_diff: float = 0.0
    team_level_diff: float = 0.0
    team_kill_diff: float = 0.0
    team_strength: float = 0.0

    # Situational features
    alive_allies: int = 0
    alive_enemies: int = 0
    alive_diff: int = 0
    kill_pressure: float = 0.0

    # Game phase
    game_time_minutes: float = 0.0
    game_phase: str = "early"  # early / mid / late

    # Raw values for reference
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert features to a flat dictionary (for ML input)."""
        return {
            "gold_diff": self.gold_diff,
            "level_diff": self.level_diff,
            "hp_ratio": self.hp_ratio,
            "cs_diff": self.cs_diff,
            "team_gold_diff": self.team_gold_diff,
            "team_level_diff": self.team_level_diff,
            "team_kill_diff": self.team_kill_diff,
            "team_strength": self.team_strength,
            "alive_allies": self.alive_allies,
            "alive_enemies": self.alive_enemies,
            "alive_diff": self.alive_diff,
            "kill_pressure": self.kill_pressure,
            "game_time_minutes": self.game_time_minutes,
            "game_phase": self.game_phase,
        }

    def to_vector(self) -> list:
        """Convert numeric features to a flat list (for ML model input)."""
        phase_map = {"early": 0.0, "mid": 0.5, "late": 1.0}
        return [
            self.gold_diff,
            self.level_diff,
            self.hp_ratio,
            self.cs_diff,
            self.team_gold_diff,
            self.team_level_diff,
            self.team_kill_diff,
            self.team_strength,
            float(self.alive_allies),
            float(self.alive_enemies),
            float(self.alive_diff),
            self.kill_pressure,
            self.game_time_minutes,
            phase_map.get(self.game_phase, 0.5),
        ]


class FeatureEngine:
    """Extracts normalized features from live game data.

    Converts raw GameData into GameFeatures suitable for
    AI model consumption or advanced rule evaluation.
    """

    def extract(self, game_data: GameData) -> GameFeatures:
        """Extract features from a game state snapshot.

        Args:
            game_data: Current live game data.

        Returns:
            GameFeatures with all computed values.
        """
        features = GameFeatures()

        if game_data.active_player is None:
            return features

        player = game_data.active_player
        enemies = game_data.enemies
        allies = game_data.allies

        # Time / phase
        features.game_time_minutes = game_data.game_time / 60.0
        features.game_phase = self._determine_game_phase(
            features.game_time_minutes
        )

        # Player features
        features.hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0.0
        features.gold_diff = self._compute_gold_diff(player, enemies)
        features.level_diff = self._compute_level_diff(player, enemies)
        features.cs_diff = self._compute_cs_diff(player, enemies)

        # Team features
        features.team_gold_diff = self._compute_team_gold_diff(
            player, allies, enemies
        )
        features.team_level_diff = self._compute_team_level_diff(
            player, allies, enemies
        )
        features.team_kill_diff = self._compute_team_kill_diff(
            player, allies, enemies
        )

        # Alive counts
        features.alive_allies = sum(
            1 for a in allies if not a.is_dead
        ) + (0 if player.is_dead else 1)
        features.alive_enemies = sum(
            1 for e in enemies if not e.is_dead
        )
        features.alive_diff = features.alive_allies - features.alive_enemies

        # Composite scores
        features.team_strength = self._compute_team_strength(features)
        features.kill_pressure = self._compute_kill_pressure(
            player, enemies, features
        )

        # Store raw values for debugging
        features.raw = {
            "player_gold": player.current_gold,
            "player_level": player.level,
            "player_hp": player.hp,
            "player_max_hp": player.max_hp,
            "player_cs": player.creep_score,
            "player_kda": player.kda_string,
        }

        return features

    def _determine_game_phase(self, minutes: float) -> str:
        """Determine current game phase based on time."""
        if minutes < 15.0:
            return "early"
        elif minutes < 30.0:
            return "mid"
        else:
            return "late"

    def _compute_gold_diff(
        self, player: PlayerData, enemies: list
    ) -> float:
        """Compute normalized gold difference vs average enemy."""
        if not enemies:
            return 0.0
        avg_enemy_gold = sum(e.current_gold for e in enemies) / len(enemies)
        if avg_enemy_gold == 0 and player.current_gold == 0:
            return 0.0
        # Normalize: positive = ahead, negative = behind
        # Scale by 1000g increments
        return (player.current_gold - avg_enemy_gold) / 1000.0

    def _compute_level_diff(
        self, player: PlayerData, enemies: list
    ) -> float:
        """Compute level difference vs average enemy."""
        if not enemies:
            return 0.0
        avg_enemy_level = sum(e.level for e in enemies) / len(enemies)
        return player.level - avg_enemy_level

    def _compute_cs_diff(
        self, player: PlayerData, enemies: list
    ) -> float:
        """Compute CS difference vs average enemy."""
        if not enemies:
            return 0.0
        avg_enemy_cs = sum(e.creep_score for e in enemies) / len(enemies)
        return player.creep_score - avg_enemy_cs

    def _compute_team_gold_diff(
        self,
        player: PlayerData,
        allies: list,
        enemies: list,
    ) -> float:
        """Compute total team gold difference (normalized)."""
        team_gold = player.current_gold + sum(
            a.current_gold for a in allies
        )
        enemy_gold = sum(e.current_gold for e in enemies)
        if not enemies:
            return 0.0
        return (team_gold - enemy_gold) / 1000.0

    def _compute_team_level_diff(
        self,
        player: PlayerData,
        allies: list,
        enemies: list,
    ) -> float:
        """Compute average team level difference."""
        team_levels = [player.level] + [a.level for a in allies]
        enemy_levels = [e.level for e in enemies]
        if not enemy_levels:
            return 0.0
        avg_team = sum(team_levels) / len(team_levels)
        avg_enemy = sum(enemy_levels) / len(enemy_levels)
        return avg_team - avg_enemy

    def _compute_team_kill_diff(
        self,
        player: PlayerData,
        allies: list,
        enemies: list,
    ) -> float:
        """Compute team kill difference."""
        team_kills = player.kills + sum(a.kills for a in allies)
        enemy_kills = sum(e.kills for e in enemies)
        return float(team_kills - enemy_kills)

    def _compute_team_strength(self, features: GameFeatures) -> float:
        """Compute composite team strength score.

        Combines gold, level, and alive advantages into a single
        normalized score from -1.0 (very weak) to 1.0 (very strong).
        """
        # Weighted combination of factors
        gold_weight = 0.4
        level_weight = 0.3
        alive_weight = 0.3

        # Normalize each factor to roughly -1..1 range
        gold_score = max(-1.0, min(1.0, features.team_gold_diff / 10.0))
        level_score = max(-1.0, min(1.0, features.team_level_diff / 3.0))
        alive_score = max(
            -1.0, min(1.0, features.alive_diff / 3.0)
        )

        return (
            gold_weight * gold_score
            + level_weight * level_score
            + alive_weight * alive_score
        )

    def _compute_kill_pressure(
        self,
        player: PlayerData,
        enemies: list,
        features: GameFeatures,
    ) -> float:
        """Compute kill pressure score.

        Estimates likelihood of securing a kill based on
        current advantages. Range: 0.0 (no pressure) to 1.0 (high).
        """
        if not enemies:
            return 0.0

        score = 0.5  # Neutral baseline

        # Gold advantage increases kill pressure
        score += features.gold_diff * 0.1

        # Level advantage
        score += features.level_diff * 0.1

        # HP advantage
        if player.hp_percent > 70:
            score += 0.1
        elif player.hp_percent < 30:
            score -= 0.2

        # Alive advantage
        score += features.alive_diff * 0.1

        return max(0.0, min(1.0, score))
