"""Tests for the game adapter system."""

import pytest
from unittest.mock import patch, MagicMock

from temvision.game.adapter import adapter_registry
from temvision.game.state import GameState
from temvision.lol.game_detector import GamePhase
from temvision.vision.engine import Detection

# Ensure LoL adapter is registered
import temvision.game.lol  # noqa: F401


class TestAdapterRegistry:
    def test_get_lol_adapter(self):
        adapter = adapter_registry.get("lol")
        assert adapter is not None
        assert adapter.game_name == "lol"

    def test_get_nonexistent_adapter(self):
        adapter = adapter_registry.get("nonexistent_game")
        assert adapter is None

    def test_list_games(self):
        games = adapter_registry.list_games()
        assert "lol" in games


class TestLoLAdapter:
    def test_process_detections(self):
        adapter = adapter_registry.get("lol")
        config = {
            "vision": {"detect": ["enemy_icon"]},
            "mapping": {"enemy_icon": "enemy"},
        }
        detections = [
            Detection(label="enemy_icon", confidence=0.9, bbox=(10, 20, 30, 30))
        ]

        state = adapter.process_detections(detections, config)
        assert isinstance(state, GameState)
        assert state.variables["enemy_visible"] is True

    def test_process_empty_detections(self):
        adapter = adapter_registry.get("lol")
        config = {
            "vision": {"detect": ["enemy_icon"]},
            "mapping": {"enemy_icon": "enemy"},
        }

        state = adapter.process_detections([], config)
        assert state.variables["enemy_visible"] is False

    def test_get_detect_targets(self):
        adapter = adapter_registry.get("lol")
        config = {"vision": {"detect": ["enemy_icon", "ally_icon"]}}
        targets = adapter.get_detect_targets(config)
        assert targets == ["enemy_icon", "ally_icon"]


class TestLoLAdapterPhase:
    """Test LoLAdapter.get_phase() returns correct GamePhase values."""

    def test_phase_closed_when_lol_not_running(self):
        adapter = adapter_registry.get("lol")
        with patch.object(adapter._live_api, "is_game_running", return_value=False), \
             patch.object(adapter._detector, "is_game_running", return_value=False):
            assert adapter.get_phase() == GamePhase.CLOSED

    def test_phase_client_open_when_client_running_no_match(self):
        adapter = adapter_registry.get("lol")
        with patch.object(adapter._live_api, "is_game_running", return_value=False), \
             patch.object(adapter._detector, "is_game_running", return_value=True):
            assert adapter.get_phase() == GamePhase.CLIENT_OPEN

    def test_phase_in_game_when_live_api_responds(self):
        adapter = adapter_registry.get("lol")
        with patch.object(adapter._live_api, "is_game_running", return_value=True):
            assert adapter.get_phase() == GamePhase.IN_GAME
