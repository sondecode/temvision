"""Tests for Live Client API reader."""

import pytest

from temvision.lol.client_api import LiveClientAPI
from temvision.lol.models import PlayerData, GameData


# Sample API response matching League Live Client API format
SAMPLE_GAME_DATA = {
    "activePlayer": {
        "riotIdGameName": "TestPlayer",
        "summonerName": "TestPlayer",
        "level": 10,
        "currentGold": 5500.0,
    },
    "allPlayers": [
        {
            "riotIdGameName": "TestPlayer",
            "summonerName": "TestPlayer",
            "championName": "Jinx",
            "team": "ORDER",
            "level": 10,
            "position": "BOTTOM",
            "isDead": False,
            "respawnTimer": 0.0,
            "scores": {
                "kills": 5,
                "deaths": 2,
                "assists": 8,
                "creepScore": 150,
            },
            "items": [
                {"itemID": 3006, "displayName": "Berserker's Greaves", "count": 1},
                {"itemID": 6672, "displayName": "Kraken Slayer", "count": 1},
            ],
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "Flash"},
                "summonerSpellTwo": {"displayName": "Heal"},
            },
        },
        {
            "riotIdGameName": "Ally1",
            "summonerName": "Ally1",
            "championName": "Leona",
            "team": "ORDER",
            "level": 9,
            "position": "UTILITY",
            "isDead": False,
            "respawnTimer": 0.0,
            "scores": {
                "kills": 1,
                "deaths": 3,
                "assists": 12,
                "creepScore": 25,
            },
            "items": [],
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "Flash"},
                "summonerSpellTwo": {"displayName": "Ignite"},
            },
        },
        {
            "riotIdGameName": "Enemy1",
            "summonerName": "Enemy1",
            "championName": "Caitlyn",
            "team": "CHAOS",
            "level": 9,
            "position": "BOTTOM",
            "isDead": False,
            "respawnTimer": 0.0,
            "scores": {
                "kills": 3,
                "deaths": 4,
                "assists": 5,
                "creepScore": 130,
            },
            "items": [],
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "Flash"},
                "summonerSpellTwo": {"displayName": "Heal"},
            },
        },
        {
            "riotIdGameName": "Enemy2",
            "summonerName": "Enemy2",
            "championName": "Thresh",
            "team": "CHAOS",
            "level": 8,
            "position": "UTILITY",
            "isDead": True,
            "respawnTimer": 15.0,
            "scores": {
                "kills": 0,
                "deaths": 5,
                "assists": 3,
                "creepScore": 20,
            },
            "items": [],
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "Flash"},
                "summonerSpellTwo": {"displayName": "Ignite"},
            },
        },
    ],
    "gameData": {
        "gameTime": 900.5,
        "gameMode": "CLASSIC",
        "mapName": "Map11",
    },
    "events": {
        "Events": [
            {"EventName": "GameStart", "EventTime": 0.0},
        ]
    },
}


class TestLiveClientAPI:
    """Test Live Client API data parsing."""

    def setup_method(self):
        self.api = LiveClientAPI()

    def test_parse_game_data_basic(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        assert isinstance(game_data, GameData)
        assert game_data.game_time == 900.5
        assert game_data.game_mode == "CLASSIC"

    def test_parse_active_player(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        assert game_data.active_player_name == "TestPlayer"
        assert game_data.active_player is not None
        assert game_data.active_player.champion_name == "Jinx"
        assert game_data.active_player.level == 10

    def test_parse_player_kda(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        player = game_data.active_player
        assert player.kills == 5
        assert player.deaths == 2
        assert player.assists == 8
        assert player.kda_string == "5/2/8"

    def test_parse_player_items(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        player = game_data.active_player
        assert len(player.items) == 2
        assert player.items[0]["displayName"] == "Berserker's Greaves"

    def test_parse_summoner_spells(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        player = game_data.active_player
        assert player.summoner_spells == ["Flash", "Heal"]

    def test_parse_allies_and_enemies(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        # Active player is ORDER, Ally1 is ORDER, Enemy1/2 are CHAOS
        assert len(game_data.allies) == 1
        assert len(game_data.enemies) == 2
        assert game_data.allies[0].champion_name == "Leona"

    def test_parse_enemy_death_state(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        enemy2 = [e for e in game_data.enemies if e.champion_name == "Thresh"][0]
        assert enemy2.is_dead is True
        assert enemy2.respawn_timer == 15.0

    def test_parse_all_players(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        assert len(game_data.all_players) == 4

    def test_parse_events(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        assert len(game_data.events) == 1
        assert game_data.events[0]["EventName"] == "GameStart"

    def test_parse_empty_data(self):
        game_data = self.api.parse_game_data({})
        assert game_data.game_time == 0.0
        assert game_data.active_player is None
        assert game_data.all_players == []

    def test_is_game_running_connection_refused(self):
        """Test that is_game_running returns False when no game is running."""
        api = LiveClientAPI(base_url="https://127.0.0.1:29999", timeout=0.5)
        assert api.is_game_running() is False

    def test_get_all_game_data_connection_refused(self):
        """Test that get_all_game_data returns None when no game is running."""
        api = LiveClientAPI(base_url="https://127.0.0.1:29999", timeout=0.5)
        assert api.get_all_game_data() is None

    def test_parse_player_creep_score(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        assert game_data.active_player.creep_score == 150

    def test_parse_player_position(self):
        game_data = self.api.parse_game_data(SAMPLE_GAME_DATA)
        assert game_data.active_player.position == "BOTTOM"
