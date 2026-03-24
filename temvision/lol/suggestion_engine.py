"""Rule-based suggestion engine for LoL overlay.

Provides gameplay suggestions based on live game state analysis.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import GameData, PlayerData

logger = logging.getLogger(__name__)


@dataclass
class Suggestion:
    """A gameplay suggestion to display in the overlay."""

    text: str
    category: str = "general"
    priority: str = "normal"
    icon: str = ""

    @property
    def display_text(self) -> str:
        """Return formatted display text with icon."""
        if self.icon:
            return f"{self.icon} {self.text}"
        return self.text


# Configurable thresholds for suggestions
@dataclass
class SuggestionThresholds:
    """Thresholds for triggering suggestions."""

    hp_low_percent: float = 30.0
    hp_critical_percent: float = 15.0
    gold_advantage: float = 500.0
    gold_large_advantage: float = 1500.0
    level_advantage: int = 1
    level_large_advantage: int = 2
    cs_advantage: int = 20


class SuggestionEngine:
    """Rule-based suggestion engine for League of Legends.

    Analyzes live game data and generates gameplay suggestions
    based on configurable rules and thresholds.
    """

    def __init__(
        self, thresholds: Optional[SuggestionThresholds] = None
    ):
        self.thresholds = thresholds or SuggestionThresholds()

    def analyze(self, game_data: GameData) -> list:
        """Analyze game state and return suggestions.

        Args:
            game_data: Current live game data.

        Returns:
            List of Suggestion objects sorted by priority.
        """
        suggestions = []

        if game_data.active_player is None:
            return suggestions

        suggestions.extend(self._check_hp(game_data))
        suggestions.extend(self._check_gold(game_data))
        suggestions.extend(self._check_level(game_data))
        suggestions.extend(self._check_cs(game_data))
        suggestions.extend(self._check_death_state(game_data))
        suggestions.extend(self._check_team_fights(game_data))

        return self._sort_by_priority(suggestions)

    def _check_hp(self, game_data: GameData) -> list:
        """Check HP-based suggestions."""
        suggestions = []
        player = game_data.active_player

        hp_pct = player.hp_percent

        if hp_pct < self.thresholds.hp_critical_percent:
            suggestions.append(
                Suggestion(
                    text="Critical HP! Recall or retreat immediately",
                    category="survival",
                    priority="critical",
                    icon="🔴",
                )
            )
        elif hp_pct < self.thresholds.hp_low_percent:
            suggestions.append(
                Suggestion(
                    text="Low HP - play safe and consider retreating",
                    category="survival",
                    priority="high",
                    icon="🟠",
                )
            )

        return suggestions

    def _check_gold(self, game_data: GameData) -> list:
        """Check gold-based suggestions."""
        suggestions = []
        gold_diff = game_data.gold_difference

        if gold_diff > self.thresholds.gold_large_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Large gold lead (+{gold_diff:.0f}g) - press your advantage",
                    category="aggression",
                    priority="high",
                    icon="💰",
                )
            )
        elif gold_diff > self.thresholds.gold_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Gold advantage (+{gold_diff:.0f}g) - look for trades",
                    category="aggression",
                    priority="normal",
                    icon="🪙",
                )
            )
        elif gold_diff < -self.thresholds.gold_large_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Gold deficit ({gold_diff:.0f}g) - farm safely",
                    category="caution",
                    priority="high",
                    icon="⚠️",
                )
            )
        elif gold_diff < -self.thresholds.gold_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Behind in gold ({gold_diff:.0f}g) - focus on CS",
                    category="caution",
                    priority="normal",
                    icon="📉",
                )
            )

        return suggestions

    def _check_level(self, game_data: GameData) -> list:
        """Check level-based suggestions."""
        suggestions = []
        level_diff = game_data.level_difference

        if level_diff >= self.thresholds.level_large_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Level advantage (+{level_diff:.0f}) - strong trade potential",
                    category="aggression",
                    priority="high",
                    icon="⬆️",
                )
            )
        elif level_diff >= self.thresholds.level_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Level up (+{level_diff:.0f}) - consider trading",
                    category="aggression",
                    priority="normal",
                    icon="📈",
                )
            )
        elif level_diff <= -self.thresholds.level_large_advantage:
            suggestions.append(
                Suggestion(
                    text=f"Level disadvantage ({level_diff:.0f}) - avoid fights",
                    category="caution",
                    priority="high",
                    icon="⬇️",
                )
            )

        return suggestions

    def _check_cs(self, game_data: GameData) -> list:
        """Check CS-based suggestions."""
        suggestions = []
        player = game_data.active_player

        if not game_data.enemies:
            return suggestions

        avg_enemy_cs = sum(e.creep_score for e in game_data.enemies) / len(
            game_data.enemies
        )
        cs_diff = player.creep_score - avg_enemy_cs

        if cs_diff < -self.thresholds.cs_advantage:
            suggestions.append(
                Suggestion(
                    text=f"CS behind ({cs_diff:.0f}) - focus on last hitting",
                    category="farming",
                    priority="normal",
                    icon="🌾",
                )
            )

        return suggestions

    def _check_death_state(self, game_data: GameData) -> list:
        """Check for dead enemies (opportunities)."""
        suggestions = []
        dead_enemies = [e for e in game_data.enemies if e.is_dead]

        if len(dead_enemies) >= 3:
            suggestions.append(
                Suggestion(
                    text=f"{len(dead_enemies)} enemies dead - push for objective!",
                    category="objective",
                    priority="critical",
                    icon="🏰",
                )
            )
        elif len(dead_enemies) >= 1:
            names = ", ".join(e.champion_name for e in dead_enemies)
            suggestions.append(
                Suggestion(
                    text=f"Enemy down ({names}) - look for plays",
                    category="objective",
                    priority="normal",
                    icon="💀",
                )
            )

        return suggestions

    def _check_team_fights(self, game_data: GameData) -> list:
        """Check team-level advantage suggestions."""
        suggestions = []

        ally_deaths = sum(
            1 for a in game_data.allies if a.is_dead
        )
        enemy_deaths = sum(
            1 for e in game_data.enemies if e.is_dead
        )

        if ally_deaths >= 3 and not game_data.active_player.is_dead:
            suggestions.append(
                Suggestion(
                    text="Team is down - avoid engaging, play safe",
                    category="caution",
                    priority="high",
                    icon="🛡️",
                )
            )

        return suggestions

    def _sort_by_priority(self, suggestions: list) -> list:
        """Sort suggestions by priority (critical first)."""
        priority_order = {
            "critical": 0,
            "high": 1,
            "normal": 2,
            "low": 3,
        }
        return sorted(
            suggestions,
            key=lambda s: priority_order.get(s.priority, 99),
        )
