"""Tests for game state management."""

import pytest

from temvision.game.state import GameState
from temvision.vision.engine import Detection


class TestGameState:
    def test_initial_state(self):
        state = GameState(game="lol")
        assert state.game == "lol"
        assert state.timestamp == 0.0
        assert state.detections == {}
        assert state.variables == {}

    def test_update_from_detections_with_enemy(self):
        state = GameState(game="lol")
        detections = [
            Detection(label="enemy_icon", confidence=0.9, bbox=(10, 20, 30, 30))
        ]
        mapping = {"enemy_icon": "enemy"}
        targets = ["enemy_icon"]

        state.update_from_detections(detections, mapping, targets)

        assert state.detections["enemy"] is True
        assert state.variables["enemy_visible"] is True
        assert state.variables["enemy_count"] == 1

    def test_update_from_detections_no_enemy(self):
        state = GameState(game="lol")
        detections = []
        mapping = {"enemy_icon": "enemy"}
        targets = ["enemy_icon"]

        state.update_from_detections(detections, mapping, targets)

        assert state.detections["enemy"] is False
        assert state.variables["enemy_visible"] is False
        assert state.variables["enemy_count"] == 0

    def test_to_dict(self):
        state = GameState(game="lol")
        state.variables["enemy_visible"] = False
        result = state.to_dict()

        assert result["game"] == "lol"
        assert result["enemy_visible"] is False

    def test_get(self):
        state = GameState(game="lol")
        state.variables["health"] = 100
        assert state.get("health") == 100
        assert state.get("nonexistent") is None
        assert state.get("nonexistent", 0) == 0

    def test_reset(self):
        state = GameState(game="lol")
        state.variables["x"] = 1
        state.detections["y"] = True
        state.reset()

        assert state.variables == {}
        assert state.detections == {}
        assert state.timestamp == 0.0

    def test_multiple_detections(self):
        state = GameState(game="lol")
        detections = [
            Detection(label="enemy_icon", confidence=0.9, bbox=(10, 20, 30, 30)),
            Detection(label="enemy_icon", confidence=0.85, bbox=(50, 60, 30, 30)),
        ]
        mapping = {"enemy_icon": "enemy"}
        targets = ["enemy_icon"]

        state.update_from_detections(detections, mapping, targets)

        assert state.variables["enemy_count"] == 2
        assert state.variables["enemy_visible"] is True
