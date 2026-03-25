"""Tests for lane threat scorer."""

import pytest

from temvision.lol.threat_scorer import ThreatScorer, ThreatInfo
from temvision.lol.spell_tracker import SpellTracker
from temvision.lol.models import GameData, PlayerData


def _make_game(enemies, player_gold=5000, player_level=10):
    """Helper to build a minimal GameData."""
    return GameData(
        game_time=1200.0,  # 20 minutes
        active_player=PlayerData(
            summoner_name="Me",
            champion_name="Jinx",
            current_gold=player_gold,
            level=player_level,
            kills=5,
            deaths=2,
            assists=3,
            creep_score=150,
        ),
        allies=[],
        enemies=enemies,
    )


class TestThreatInfo:
    def test_overlay_line(self):
        t = ThreatInfo(champion_name="Zed", threat_score=80, label="Extreme")
        line = t.overlay_line()
        assert "Zed" in line
        assert "80" in line
        assert "🔴" in line

    def test_low_threat(self):
        t = ThreatInfo(champion_name="Soraka", threat_score=15, label="Low")
        assert "🟢" in t.overlay_line()


class TestThreatScorer:
    def test_empty_enemies(self):
        scorer = ThreatScorer()
        game = GameData(game_time=600.0)
        assert scorer.score_all(game) == []

    def test_fed_enemy_high_threat(self):
        scorer = ThreatScorer()
        enemies = [
            PlayerData(
                champion_name="Zed",
                kills=10, deaths=1, assists=5,
                current_gold=12000, level=15,
                creep_score=200,
            ),
        ]
        game = _make_game(enemies)
        threats = scorer.score_all(game, 1200.0)
        assert len(threats) == 1
        assert threats[0].threat_score > 50
        assert threats[0].label in ("High", "Extreme")

    def test_weak_enemy_low_threat(self):
        scorer = ThreatScorer()
        enemies = [
            PlayerData(
                champion_name="Soraka",
                kills=0, deaths=5, assists=1,
                current_gold=2000, level=6,
                creep_score=50, is_dead=True,
            ),
        ]
        game = _make_game(enemies)
        threats = scorer.score_all(game, 1200.0)
        assert len(threats) == 1
        assert threats[0].threat_score < 40
        assert threats[0].label in ("Low", "Medium")

    def test_sorted_by_score(self):
        scorer = ThreatScorer()
        enemies = [
            PlayerData(champion_name="A", kills=1, current_gold=3000, level=8),
            PlayerData(champion_name="B", kills=10, current_gold=15000, level=16, creep_score=200),
        ]
        game = _make_game(enemies)
        threats = scorer.score_all(game, 1200.0)
        assert threats[0].champion_name == "B"

    def test_with_spell_tracker(self):
        tracker = SpellTracker()
        tracker.register_player("Zed", "E1", "Flash", "Ignite")
        tracker.mark_used("Zed", "Flash", 100.0)

        scorer = ThreatScorer(spell_tracker=tracker)
        enemies = [
            PlayerData(
                champion_name="Zed", kills=5, deaths=1,
                current_gold=8000, level=12, creep_score=150,
            ),
        ]
        game = _make_game(enemies)
        threats = scorer.score_all(game, 150.0)
        assert len(threats) == 1
        # Flash on CD should lower threat
        assert "No Flash" in threats[0].reasons

    def test_overlay_lines(self):
        scorer = ThreatScorer()
        enemies = [
            PlayerData(champion_name="A", kills=5, current_gold=8000, level=12, creep_score=100),
            PlayerData(champion_name="B", kills=2, current_gold=4000, level=8, creep_score=60),
        ]
        game = _make_game(enemies)
        lines = scorer.overlay_lines(game, 1200.0, top_n=2)
        assert len(lines) == 2

    def test_label_thresholds(self):
        assert ThreatScorer._label(80) == "Extreme"
        assert ThreatScorer._label(60) == "High"
        assert ThreatScorer._label(40) == "Medium"
        assert ThreatScorer._label(10) == "Low"
