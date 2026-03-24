"""League of Legends Live Client API reader.

Reads real-time game data from the League Client API at:
https://127.0.0.1:2999/liveclientdata/allgamedata

Reference: https://developer.riotgames.com/docs/lol#game-client-api
"""

import logging
from typing import Optional

import warnings

import requests
import urllib3

from temvision.lol.models import PlayerData, GameData

logger = logging.getLogger(__name__)

BASE_URL = "https://127.0.0.1:2999"

ENDPOINTS = {
    "all_game_data": "/liveclientdata/allgamedata",
    "active_player": "/liveclientdata/activeplayer",
    "player_list": "/liveclientdata/playerlist",
    "player_scores": "/liveclientdata/playerscores",
    "game_stats": "/liveclientdata/gamestats",
    "event_data": "/liveclientdata/eventdata",
}


class LiveClientAPI:
    """Reads live game data from League of Legends Client API."""

    def __init__(self, base_url: str = BASE_URL, timeout: float = 2.0):
        self.base_url = base_url
        self.timeout = timeout
        self._session = requests.Session()
        # The League Client uses a self-signed certificate on localhost,
        # so SSL verification must be disabled for this specific session.
        self._session.verify = False
        # Suppress InsecureRequestWarning only for this session's adapter
        warnings.filterwarnings(
            "ignore",
            message="Unverified HTTPS request",
            category=urllib3.exceptions.InsecureRequestWarning,
        )

    def is_game_running(self) -> bool:
        """Check if a League game is currently active by pinging the API."""
        try:
            resp = self._session.get(
                f"{self.base_url}{ENDPOINTS['game_stats']}",
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except requests.ConnectionError:
            return False
        except requests.RequestException:
            return False

    def get_all_game_data(self) -> Optional[dict]:
        """Fetch all game data from the Live Client API."""
        try:
            resp = self._session.get(
                f"{self.base_url}{ENDPOINTS['all_game_data']}",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.debug("Failed to fetch game data: %s", e)
            return None

    def get_active_player(self) -> Optional[dict]:
        """Fetch active player data."""
        try:
            resp = self._session.get(
                f"{self.base_url}{ENDPOINTS['active_player']}",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.debug("Failed to fetch active player: %s", e)
            return None

    def get_player_list(self) -> Optional[list]:
        """Fetch the list of all players in the game."""
        try:
            resp = self._session.get(
                f"{self.base_url}{ENDPOINTS['player_list']}",
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.debug("Failed to fetch player list: %s", e)
            return None

    def parse_game_data(self, raw_data: dict) -> GameData:
        """Parse raw API response into GameData model.

        Args:
            raw_data: Raw JSON response from allgamedata endpoint.

        Returns:
            Parsed GameData object.
        """
        game_data = GameData()

        # Parse game stats
        game_stats = raw_data.get("gameData", {})
        game_data.game_time = game_stats.get("gameTime", 0.0)
        game_data.game_mode = game_stats.get("gameMode", "")
        game_data.map_name = game_stats.get("mapName", "")

        # Parse active player name
        active_player = raw_data.get("activePlayer", {})
        game_data.active_player_name = active_player.get(
            "riotIdGameName",
            active_player.get("summonerName", ""),
        )

        # Parse all players
        all_players_raw = raw_data.get("allPlayers", [])
        active_team = ""

        for p in all_players_raw:
            player = self._parse_player(p)
            game_data.all_players.append(player)

            player_name = p.get(
                "riotIdGameName", p.get("summonerName", "")
            )
            if player_name == game_data.active_player_name:
                game_data.active_player = player
                active_team = player.team

        # Separate allies and enemies
        for player in game_data.all_players:
            if player.summoner_name == game_data.active_player_name:
                continue
            if player.team == active_team:
                game_data.allies.append(player)
            else:
                game_data.enemies.append(player)

        # Parse events
        events_data = raw_data.get("events", {})
        game_data.events = events_data.get("Events", [])

        return game_data

    def _parse_player(self, player_data: dict) -> PlayerData:
        """Parse a single player's data from the API response."""
        player = PlayerData()
        player.summoner_name = player_data.get(
            "riotIdGameName",
            player_data.get("summonerName", ""),
        )
        player.champion_name = player_data.get("championName", "")
        player.team = player_data.get("team", "")
        player.level = player_data.get("level", 0)
        player.position = player_data.get("position", "")
        player.is_dead = player_data.get("isDead", False)
        player.respawn_timer = player_data.get("respawnTimer", 0.0)

        # Parse scores (KDA, CS)
        scores = player_data.get("scores", {})
        player.kills = scores.get("kills", 0)
        player.deaths = scores.get("deaths", 0)
        player.assists = scores.get("assists", 0)
        player.creep_score = scores.get("creepScore", 0)

        # Parse items
        items_raw = player_data.get("items", [])
        player.items = [
            {
                "itemID": item.get("itemID", 0),
                "displayName": item.get("displayName", ""),
                "count": item.get("count", 1),
            }
            for item in items_raw
        ]

        # Parse summoner spells
        spells = player_data.get("summonerSpells", {})
        player.summoner_spells = [
            spells.get("summonerSpellOne", {}).get("displayName", ""),
            spells.get("summonerSpellTwo", {}).get("displayName", ""),
        ]

        return player

    def close(self):
        """Close the HTTP session."""
        self._session.close()
