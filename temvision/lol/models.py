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

    @property
    def team_total_gold(self) -> float:
        """Calculate total team gold (including active player)."""
        total = 0.0
        if self.active_player:
            total += self.active_player.current_gold
        total += sum(a.current_gold for a in self.allies)
        return total

    @property
    def enemy_total_gold(self) -> float:
        """Calculate total enemy team gold."""
        return sum(e.current_gold for e in self.enemies)

    @property
    def team_total_kills(self) -> int:
        """Calculate total team kills."""
        total = 0
        if self.active_player:
            total += self.active_player.kills
        total += sum(a.kills for a in self.allies)
        return total

    @property
    def enemy_total_kills(self) -> int:
        """Calculate total enemy kills."""
        return sum(e.kills for e in self.enemies)

    @property
    def team_gold_diff(self) -> float:
        """Calculate total gold difference (team vs enemy team)."""
        return self.team_total_gold - self.enemy_total_gold

    @property
    def team_kill_diff(self) -> int:
        """Calculate total kill difference (team vs enemy team)."""
        return self.team_total_kills - self.enemy_total_kills

    def get_enemy_by_position(self, position: str) -> Optional[PlayerData]:
        """Get enemy player by position."""
        for enemy in self.enemies:
            if enemy.position.lower() == position.lower():
                return enemy
        return None


@dataclass
class PostGameStats:
    """Post-game analysis data."""

    game_duration: float = 0.0
    player_champion: str = ""
    win: bool = False
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    total_damage: float = 0.0
    gold_earned: float = 0.0
    cs: int = 0
    cs_per_min: float = 0.0
    vision_score: float = 0.0
    kda_ratio: float = 0.0
    performance_score: float = 0.0
    mvp: bool = False
    grade: str = ""
    all_player_stats: list = field(default_factory=list)

    @property
    def kda_string(self) -> str:
        """Return KDA as formatted string."""
        return f"{self.kills}/{self.deaths}/{self.assists}"


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
