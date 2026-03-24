"""Data models for LoL desktop overlay."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlayerData:
    """Represents a single player's live game data."""

    summoner_name: str = ""
    champion_name: str = ""
    team: str = ""
    level: int = 0
    current_gold: float = 0.0
    hp: float = 0.0
    max_hp: float = 0.0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    creep_score: int = 0
    items: list = field(default_factory=list)
    summoner_spells: list = field(default_factory=list)
    position: str = ""
    is_dead: bool = False
    respawn_timer: float = 0.0

    @property
    def kda_string(self) -> str:
        """Return KDA as formatted string."""
        return f"{self.kills}/{self.deaths}/{self.assists}"

    @property
    def kda_ratio(self) -> float:
        """Calculate KDA ratio."""
        if self.deaths == 0:
            return float(self.kills + self.assists)
        return (self.kills + self.assists) / self.deaths

    @property
    def hp_percent(self) -> float:
        """Calculate HP percentage."""
        if self.max_hp == 0:
            return 0.0
        return (self.hp / self.max_hp) * 100.0


@dataclass
class GameData:
    """Represents the full live game state."""

    game_time: float = 0.0
    game_mode: str = ""
    map_name: str = ""
    active_player_name: str = ""
    active_player: Optional[PlayerData] = None
    allies: list = field(default_factory=list)
    enemies: list = field(default_factory=list)
    all_players: list = field(default_factory=list)
    events: list = field(default_factory=list)

    @property
    def gold_difference(self) -> float:
        """Calculate gold difference between active player and enemy laner."""
        if self.active_player is None or not self.enemies:
            return 0.0
        enemy_golds = [e.current_gold for e in self.enemies]
        if not enemy_golds:
            return 0.0
        avg_enemy_gold = sum(enemy_golds) / len(enemy_golds)
        return self.active_player.current_gold - avg_enemy_gold

    @property
    def level_difference(self) -> float:
        """Calculate level difference between active player and avg enemy."""
        if self.active_player is None or not self.enemies:
            return 0.0
        avg_enemy_level = sum(e.level for e in self.enemies) / len(self.enemies)
        return self.active_player.level - avg_enemy_level

    def get_enemy_by_position(self, position: str) -> Optional[PlayerData]:
        """Get enemy player by position."""
        for enemy in self.enemies:
            if enemy.position.lower() == position.lower():
                return enemy
        return None


@dataclass
class PreGameStats:
    """Pre-game analysis data from Riot API."""

    summoner_name: str = ""
    rank: str = ""
    tier: str = ""
    lp: int = 0
    win_rate: float = 0.0
    total_games: int = 0
    champion_win_rate: float = 0.0
    champion_games: int = 0
    avg_kda: float = 0.0
    avg_cs_per_min: float = 0.0
    recent_matches: list = field(default_factory=list)

    @property
    def rank_string(self) -> str:
        """Return formatted rank string."""
        if not self.tier:
            return "Unranked"
        return f"{self.tier} {self.rank} ({self.lp} LP)"
