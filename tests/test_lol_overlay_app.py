"""Tests for LoL Overlay Application."""

import pytest

from temvision.lol.overlay_app import (
    LoLOverlayApp,
    DEFAULT_FAST_INTERVAL,
    DEFAULT_SLOW_INTERVAL,
)
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
            "items": [
                {"itemID": 3006, "displayName": "Berserker's Greaves", "count": 1},
            ],
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

# Sample data with dragon kill event
SAMPLE_RAW_DATA_WITH_DRAGON = {
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
    "events": {
        "Events": [
            {
                "EventName": "DragonKill",
                "EventTime": 350.0,
                "KillerName": "TestPlayer",
                "DragonType": "Infernal",
                "Assisters": [],
            },
        ]
    },
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


class TestLoLOverlayAppDualSpeed:
    """Test dual-speed loop functionality."""

    def test_default_intervals(self):
        app = LoLOverlayApp()
        assert app.fast_interval == DEFAULT_FAST_INTERVAL
        assert app.slow_interval == DEFAULT_SLOW_INTERVAL

    def test_custom_intervals(self):
        app = LoLOverlayApp(fast_interval=0.1, slow_interval=2.0)
        assert app.fast_interval == 0.1
        assert app.slow_interval == 2.0

    def test_default_fast_interval_value(self):
        assert DEFAULT_FAST_INTERVAL == 0.25

    def test_default_slow_interval_value(self):
        assert DEFAULT_SLOW_INTERVAL == 1.0

    def test_has_event_engine(self):
        app = LoLOverlayApp()
        assert app.event_engine is not None

    def test_has_feature_engine(self):
        app = LoLOverlayApp()
        assert app.feature_engine is not None

    def test_has_objective_tracker(self):
        app = LoLOverlayApp()
        assert app.objective_tracker is not None

    def test_has_post_game_analyzer(self):
        app = LoLOverlayApp()
        assert app.post_game_analyzer is not None

    def test_process_tick_populates_features(self):
        app = LoLOverlayApp()
        app.process_tick(SAMPLE_RAW_DATA)

        assert app.last_features is not None
        assert app.last_features.game_phase == "early"  # 720s = 12 min < 15 min
        assert app.last_features.level_diff > 0  # Player level 10 vs enemy 8

    def test_process_tick_populates_events(self):
        app = LoLOverlayApp()
        app.process_tick(SAMPLE_RAW_DATA)

        # Events list should exist (may be empty on first tick)
        assert isinstance(app.last_events, list)

    def test_process_tick_populates_objective_timers(self):
        app = LoLOverlayApp()
        app.process_tick(SAMPLE_RAW_DATA)

        assert app.last_objective_timers is not None

    def test_process_tick_with_dragon_event(self):
        app = LoLOverlayApp()
        app.process_tick(SAMPLE_RAW_DATA_WITH_DRAGON)

        timers = app.last_objective_timers
        assert timers is not None
        assert timers.dragon.kill_count == 1
        assert timers.dragon_kills_ally == 1

    def test_stop_resets_events_and_features(self):
        app = LoLOverlayApp()
        app.process_tick(SAMPLE_RAW_DATA)
        app._running = True
        app._game_active = True
        app.stop()

        assert app._last_events == []
        assert app._last_suggestions == []
        assert app._last_objective_timers is None

    def test_process_tick_returns_suggestions(self):
        app = LoLOverlayApp()
        game_data, suggestions = app.process_tick(SAMPLE_RAW_DATA)

        # With level advantage (10 vs 8), we expect suggestions
        assert len(suggestions) > 0
        assert app._last_suggestions == suggestions
