"""Post-game analysis module for LoL overlay.

Provides performance analysis after a game ends:
- Performance score calculation
- MVP detection
- KDA analysis
- CS per minute
- Grade assignment (S/A/B/C/D)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from temvision.lol.models import GameData, PlayerData, PostGameStats

logger = logging.getLogger(__name__)


class PostGameAnalyzer:
    """Analyzes game data to produce post-game statistics.

    Computes performance scores, grades, and MVP status
    from final game state data.
    """

    def analyze(self, game_data: GameData) -> Optional[PostGameStats]:
        """Analyze final game state to produce post-game stats.

        Args:
            game_data: Final game state at end of game.

        Returns:
            PostGameStats or None if no active player.
        """
        if game_data.active_player is None:
            return None

        player = game_data.active_player
        stats = PostGameStats()

        stats.game_duration = game_data.game_time
        stats.player_champion = player.champion_name
        stats.kills = player.kills
        stats.deaths = player.deaths
        stats.assists = player.assists
        stats.cs = player.creep_score
        stats.gold_earned = player.current_gold

        # Calculate derived stats
        duration_min = max(game_data.game_time / 60.0, 1.0)
        stats.cs_per_min = player.creep_score / duration_min

        if player.deaths > 0:
            stats.kda_ratio = (player.kills + player.assists) / player.deaths
        else:
            stats.kda_ratio = float(player.kills + player.assists)

        # Performance score
        stats.performance_score = self._compute_performance_score(
            player, game_data
        )

        # Grade
        stats.grade = self._compute_grade(stats.performance_score)

        # Collect all player stats for MVP comparison
        all_stats = []
        for p in game_data.all_players:
            p_score = self._compute_player_score(p, game_data)
            all_stats.append({
                "summoner_name": p.summoner_name,
                "champion_name": p.champion_name,
                "team": p.team,
                "kills": p.kills,
                "deaths": p.deaths,
                "assists": p.assists,
                "cs": p.creep_score,
                "performance_score": p_score,
            })
        stats.all_player_stats = all_stats

        # MVP detection
        stats.mvp = self._is_mvp(player, game_data)

        return stats

    def _compute_performance_score(
        self, player: PlayerData, game_data: GameData
    ) -> float:
        """Compute a performance score from 0-100.

        Factors:
        - KDA ratio (weight: 30%)
        - CS per minute (weight: 20%)
        - Kill participation (weight: 25%)
        - Gold share (weight: 15%)
        - Death count penalty (weight: 10%)
        """
        score = 0.0
        duration_min = max(game_data.game_time / 60.0, 1.0)

        # KDA score (0-30)
        if player.deaths > 0:
            kda = (player.kills + player.assists) / player.deaths
        else:
            kda = float(player.kills + player.assists)
        kda_score = min(30.0, kda * 6.0)
        score += kda_score

        # CS per min score (0-20)
        cs_per_min = player.creep_score / duration_min
        cs_score = min(20.0, cs_per_min * 2.5)
        score += cs_score

        # Kill participation (0-25)
        total_team_kills = 0
        if game_data.active_player:
            total_team_kills += game_data.active_player.kills
        total_team_kills += sum(a.kills for a in game_data.allies)
        if total_team_kills > 0:
            kp = (player.kills + player.assists) / total_team_kills
            kp_score = kp * 25.0
        else:
            kp_score = 12.5  # Neutral if no kills
        score += kp_score

        # Gold share (0-15)
        team_gold = player.current_gold + sum(
            a.current_gold for a in game_data.allies
        )
        if team_gold > 0:
            gold_share = player.current_gold / team_gold
            # Expect ~20% share in 5-player team
            gold_score = min(15.0, (gold_share / 0.2) * 7.5)
        else:
            gold_score = 7.5
        score += gold_score

        # Death penalty (0-10, fewer deaths = higher score)
        death_penalty = min(10.0, player.deaths * 1.5)
        score += max(0.0, 10.0 - death_penalty)

        return min(100.0, max(0.0, score))

    def _compute_player_score(
        self, player: PlayerData, game_data: GameData
    ) -> float:
        """Compute performance score for any player."""
        return self._compute_performance_score(player, game_data)

    def _compute_grade(self, performance_score: float) -> str:
        """Assign a letter grade based on performance score.

        S: 80+
        A: 65+
        B: 50+
        C: 35+
        D: below 35
        """
        if performance_score >= 80:
            return "S"
        elif performance_score >= 65:
            return "A"
        elif performance_score >= 50:
            return "B"
        elif performance_score >= 35:
            return "C"
        else:
            return "D"

    def _is_mvp(
        self, player: PlayerData, game_data: GameData
    ) -> bool:
        """Determine if the active player is the MVP.

        MVP = highest performance score on the team.
        """
        player_score = self._compute_performance_score(player, game_data)

        for ally in game_data.allies:
            ally_score = self._compute_performance_score(ally, game_data)
            if ally_score > player_score:
                return False

        return True
