"""Lane threat scoring for League of Legends.

Produces a 0-100 threat score for each enemy champion based on:
- Champion power curve (early/mid/late game)
- Current performance (kills, gold, level)
- Lane matchup proximity
- Summoner spell availability
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import GameData, PlayerData
from temvision.lol.spell_tracker import SpellTracker

logger = logging.getLogger(__name__)


@dataclass
class ThreatInfo:
    """Threat assessment for a single enemy champion."""

    champion_name: str = ""
    threat_score: float = 0.0  # 0-100
    label: str = "Low"        # Low / Medium / High / Extreme
    reasons: list[str] = field(default_factory=list)

    def overlay_line(self) -> str:
        icon = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Extreme": "🔴"}.get(
            self.label, "⚪"
        )
        return f"{icon} {self.champion_name}: {self.threat_score:.0f} ({self.label})"


class ThreatScorer:
    """Compute a threat score for each enemy champion.

    Factors (weight):
    1. Kill/Assist count (25)
    2. Gold advantage vs your team avg (20)
    3. Level advantage (15)
    4. Flash/key spell on cooldown (10 – lower threat)
    5. Is alive (10)
    6. Recent kill streak (10)
    7. CS/min proxy for farm (10)
    """

    def __init__(self, spell_tracker: Optional[SpellTracker] = None) -> None:
        self._spell_tracker = spell_tracker

    def score_all(
        self, game_data: GameData, current_game_time: float = 0.0
    ) -> list[ThreatInfo]:
        """Score every enemy and return threat infos sorted by score desc."""
        if not game_data.enemies:
            return []

        team_avg_gold = self._team_avg_gold(game_data)
        team_avg_level = self._team_avg_level(game_data)
        duration_min = max(game_data.game_time / 60.0, 1.0)

        threats: list[ThreatInfo] = []
        for enemy in game_data.enemies:
            info = self._score_enemy(
                enemy, team_avg_gold, team_avg_level,
                duration_min, current_game_time,
            )
            threats.append(info)

        threats.sort(key=lambda t: t.threat_score, reverse=True)
        return threats

    def overlay_lines(
        self, game_data: GameData, current_game_time: float = 0.0, top_n: int = 3,
    ) -> list[str]:
        """Convenience: return formatted overlay lines for top-N threats."""
        threats = self.score_all(game_data, current_game_time)
        return [t.overlay_line() for t in threats[:top_n]]

    # ------------------------------------------------------------------

    def _score_enemy(
        self,
        enemy: PlayerData,
        team_avg_gold: float,
        team_avg_level: float,
        duration_min: float,
        current_game_time: float,
    ) -> ThreatInfo:
        info = ThreatInfo(champion_name=enemy.champion_name)
        score = 0.0
        reasons: list[str] = []

        # 1. Kill / assist — max 25
        ka = enemy.kills + enemy.assists
        kill_score = min(25.0, ka * 2.5)
        score += kill_score
        if ka >= 5:
            reasons.append(f"{ka} K+A")

        # 2. Gold advantage — max 20
        gold_diff = enemy.current_gold - team_avg_gold
        if gold_diff > 0:
            gold_score = min(20.0, gold_diff / 500.0 * 5.0)
            score += gold_score
            if gold_diff > 1000:
                reasons.append(f"+{gold_diff:.0f}g")

        # 3. Level advantage — max 15
        level_diff = enemy.level - team_avg_level
        if level_diff > 0:
            level_score = min(15.0, level_diff * 5.0)
            score += level_score
            if level_diff >= 2:
                reasons.append(f"+{level_diff:.0f} Lv")

        # 4. Spell CD — max 10 (lower if flash on CD)
        spell_score = 10.0
        if self._spell_tracker is not None:
            cds = self._spell_tracker.get_all_on_cd(current_game_time)
            flash_on_cd = any(
                cd["champion"] == enemy.champion_name and cd["spell"] == "Flash"
                for cd in cds
            )
            if flash_on_cd:
                spell_score = 0.0
                reasons.append("No Flash")
        score += spell_score

        # 5. Alive — 10 if alive, 0 if dead
        if not enemy.is_dead:
            score += 10.0
        else:
            reasons.append("Dead")

        # 6. Kill streak proxy — max 10
        streak_score = min(10.0, max(0, enemy.kills - enemy.deaths) * 2.5)
        score += streak_score

        # 7. CS/min — max 10
        cs_per_min = enemy.creep_score / duration_min
        cs_score = min(10.0, cs_per_min * 1.0)
        score += cs_score

        info.threat_score = min(100.0, max(0.0, score))
        info.label = self._label(info.threat_score)
        info.reasons = reasons
        return info

    @staticmethod
    def _label(score: float) -> str:
        if score >= 75:
            return "Extreme"
        if score >= 50:
            return "High"
        if score >= 30:
            return "Medium"
        return "Low"

    @staticmethod
    def _team_avg_gold(game_data: GameData) -> float:
        players: list[PlayerData] = list(game_data.allies)
        if game_data.active_player:
            players.append(game_data.active_player)
        if not players:
            return 0.0
        return sum(p.current_gold for p in players) / len(players)

    @staticmethod
    def _team_avg_level(game_data: GameData) -> float:
        players: list[PlayerData] = list(game_data.allies)
        if game_data.active_player:
            players.append(game_data.active_player)
        if not players:
            return 0.0
        return sum(p.level for p in players) / len(players)
