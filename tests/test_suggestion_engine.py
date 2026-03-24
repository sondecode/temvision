"""Tests for suggestion engine."""

import pytest

from temvision.lol.suggestion_engine import (
    SuggestionEngine,
    Suggestion,
    SuggestionThresholds,
)
from temvision.lol.models import PlayerData, GameData


class TestSuggestion:
    """Test Suggestion dataclass."""

    def test_default_values(self):
        s = Suggestion(text="Test")
        assert s.text == "Test"
        assert s.category == "general"
        assert s.priority == "normal"
        assert s.icon == ""

    def test_display_text_with_icon(self):
        s = Suggestion(text="Test", icon="🔴")
        assert s.display_text == "🔴 Test"

    def test_display_text_without_icon(self):
        s = Suggestion(text="Test")
        assert s.display_text == "Test"


class TestSuggestionThresholds:
    """Test configurable thresholds."""

    def test_default_thresholds(self):
        t = SuggestionThresholds()
        assert t.hp_low_percent == 30.0
        assert t.hp_critical_percent == 15.0
        assert t.gold_advantage == 500.0
        assert t.gold_large_advantage == 1500.0
        assert t.level_advantage == 1

    def test_custom_thresholds(self):
        t = SuggestionThresholds(hp_low_percent=40.0)
        assert t.hp_low_percent == 40.0


class TestSuggestionEngine:
    """Test suggestion engine analysis."""

    def setup_method(self):
        self.engine = SuggestionEngine()

    def test_analyze_no_active_player(self):
        game_data = GameData()
        suggestions = self.engine.analyze(game_data)
        assert suggestions == []

    def test_analyze_low_hp(self):
        game_data = GameData(
            active_player=PlayerData(hp=200, max_hp=1000, level=10),
            enemies=[PlayerData(level=10)],
        )
        suggestions = self.engine.analyze(game_data)
        hp_suggestions = [s for s in suggestions if s.category == "survival"]
        assert len(hp_suggestions) == 1
        assert hp_suggestions[0].priority == "high"

    def test_analyze_critical_hp(self):
        game_data = GameData(
            active_player=PlayerData(hp=100, max_hp=1000, level=10),
            enemies=[PlayerData(level=10)],
        )
        suggestions = self.engine.analyze(game_data)
        hp_suggestions = [s for s in suggestions if s.category == "survival"]
        assert len(hp_suggestions) == 1
        assert hp_suggestions[0].priority == "critical"

    def test_analyze_gold_advantage(self):
        game_data = GameData(
            active_player=PlayerData(
                current_gold=6000, hp=1000, max_hp=1000, level=10
            ),
            enemies=[PlayerData(current_gold=4000, level=10)],
        )
        suggestions = self.engine.analyze(game_data)
        gold_suggestions = [s for s in suggestions if s.category == "aggression"]
        assert len(gold_suggestions) >= 1

    def test_analyze_gold_deficit(self):
        game_data = GameData(
            active_player=PlayerData(
                current_gold=2000, hp=1000, max_hp=1000, level=10
            ),
            enemies=[PlayerData(current_gold=5000, level=10)],
        )
        suggestions = self.engine.analyze(game_data)
        caution_suggestions = [s for s in suggestions if s.category == "caution"]
        assert len(caution_suggestions) >= 1

    def test_analyze_level_advantage(self):
        game_data = GameData(
            active_player=PlayerData(
                level=12, hp=1000, max_hp=1000, current_gold=5000
            ),
            enemies=[PlayerData(level=10, current_gold=5000)],
        )
        suggestions = self.engine.analyze(game_data)
        level_suggestions = [s for s in suggestions if s.category == "aggression"]
        assert len(level_suggestions) >= 1

    def test_analyze_level_disadvantage(self):
        game_data = GameData(
            active_player=PlayerData(
                level=8, hp=1000, max_hp=1000, current_gold=5000
            ),
            enemies=[PlayerData(level=12, current_gold=5000)],
        )
        suggestions = self.engine.analyze(game_data)
        caution_suggestions = [s for s in suggestions if s.category == "caution"]
        assert len(caution_suggestions) >= 1

    def test_analyze_dead_enemies(self):
        game_data = GameData(
            active_player=PlayerData(hp=1000, max_hp=1000, level=10),
            enemies=[
                PlayerData(
                    is_dead=True, champion_name="Caitlyn", level=10
                ),
                PlayerData(
                    is_dead=True, champion_name="Thresh", level=10
                ),
                PlayerData(
                    is_dead=True, champion_name="Zed", level=10
                ),
            ],
        )
        suggestions = self.engine.analyze(game_data)
        obj_suggestions = [s for s in suggestions if s.category == "objective"]
        assert len(obj_suggestions) >= 1
        assert obj_suggestions[0].priority == "critical"

    def test_analyze_cs_deficit(self):
        game_data = GameData(
            active_player=PlayerData(
                creep_score=80, hp=1000, max_hp=1000, level=10
            ),
            enemies=[PlayerData(creep_score=120, level=10)],
        )
        suggestions = self.engine.analyze(game_data)
        farming_suggestions = [s for s in suggestions if s.category == "farming"]
        assert len(farming_suggestions) >= 1

    def test_suggestions_sorted_by_priority(self):
        game_data = GameData(
            active_player=PlayerData(
                hp=100, max_hp=1000, current_gold=2000, level=8
            ),
            enemies=[
                PlayerData(
                    current_gold=5000,
                    level=12,
                    is_dead=False,
                ),
            ],
        )
        suggestions = self.engine.analyze(game_data)
        if len(suggestions) >= 2:
            priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
            for i in range(len(suggestions) - 1):
                assert priority_order.get(
                    suggestions[i].priority, 99
                ) <= priority_order.get(suggestions[i + 1].priority, 99)

    def test_analyze_healthy_player(self):
        """Player with full HP, equal gold/level should get minimal suggestions."""
        game_data = GameData(
            active_player=PlayerData(
                hp=1000, max_hp=1000, current_gold=5000, level=10,
                creep_score=150,
            ),
            enemies=[
                PlayerData(
                    current_gold=5000, level=10, creep_score=150,
                ),
            ],
        )
        suggestions = self.engine.analyze(game_data)
        # Should have no critical/high priority suggestions
        critical = [s for s in suggestions if s.priority == "critical"]
        assert len(critical) == 0

    def test_custom_thresholds(self):
        engine = SuggestionEngine(
            thresholds=SuggestionThresholds(hp_low_percent=50.0)
        )
        game_data = GameData(
            active_player=PlayerData(hp=400, max_hp=1000, level=10),
            enemies=[PlayerData(level=10)],
        )
        suggestions = engine.analyze(game_data)
        hp_suggestions = [s for s in suggestions if s.category == "survival"]
        assert len(hp_suggestions) == 1

    def test_team_down_suggestion(self):
        game_data = GameData(
            active_player=PlayerData(
                hp=1000, max_hp=1000, level=10, is_dead=False
            ),
            allies=[
                PlayerData(is_dead=True),
                PlayerData(is_dead=True),
                PlayerData(is_dead=True),
            ],
            enemies=[PlayerData(level=10)],
        )
        suggestions = self.engine.analyze(game_data)
        caution = [s for s in suggestions if s.category == "caution"]
        assert len(caution) >= 1
