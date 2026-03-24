"""Tests for LoL Overlay Application."""

import pytest

from temvision.lol.overlay_app import LoLOverlayApp
from temvision.lol.models import GameData


# Sample game data for testing
SAMPLE_RAW_DATA = {
    "activePlayer": {
        "riotIdGameName": "TestPlayer",
        "summonerName": "TestPlayer",
        "level": 10,
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
            "items": [],
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "Flash"},
                "summonerSpellTwo": {"displayName": "Heal"},
            },
        },
        {
            "riotIdGameName": "Enemy1",
            "summonerName": "Enemy1",
            "championName": "Caitlyn",
            "team": "CHAOS",
            "level": 8,
            "position": "BOTTOM",
            "isDead": False,
            "respawnTimer": 0.0,
            "scores": {
                "kills": 2,
                "deaths": 5,
                "assists": 3,
                "creepScore": 100,
            },
            "items": [],
            "summonerSpells": {
                "summonerSpellOne": {"displayName": "Flash"},
                "summonerSpellTwo": {"displayName": "Heal"},
            },
        },
    ],
    "gameData": {
        "gameTime": 720.0,
        "gameMode": "CLASSIC",
        "mapName": "Map11",
    },
    "events": {"Events": []},
}


class TestLoLOverlayApp:
    """Test LoL Overlay Application."""

    def test_create_app(self):
        app = LoLOverlayApp()
        assert app.update_interval == 1.0
        assert app.use_gui is False
        assert app._running is False
        assert app._game_active is False

    def test_process_tick(self):
        app = LoLOverlayApp()
        game_data, suggestions = app.process_tick(SAMPLE_RAW_DATA)

        assert isinstance(game_data, GameData)
        assert game_data.active_player_name == "TestPlayer"
        assert game_data.active_player.champion_name == "Jinx"
        assert game_data.game_time == 720.0

    def test_process_tick_generates_suggestions(self):
        app = LoLOverlayApp()
        game_data, suggestions = app.process_tick(SAMPLE_RAW_DATA)

        # With level advantage (10 vs 8) and CS advantage,
        # the engine should generate suggestions
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_last_game_data(self):
        app = LoLOverlayApp()
        assert app.last_game_data is None

        app.process_tick(SAMPLE_RAW_DATA)
        assert app.last_game_data is not None
        assert app.last_game_data.active_player_name == "TestPlayer"

    def test_stop(self):
        app = LoLOverlayApp()
        app._running = True
        app._game_active = True
        app.stop()
        assert app._running is False
        assert app._game_active is False

    def test_custom_interval(self):
        app = LoLOverlayApp(update_interval=0.5)
        assert app.update_interval == 0.5

    def test_process_tick_with_empty_data(self):
        app = LoLOverlayApp()
        game_data, suggestions = app.process_tick({})
        assert game_data.active_player is None
        assert suggestions == []
