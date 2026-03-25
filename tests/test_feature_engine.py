"""Tests for feature extraction engine."""

import pytest

from temvision.lol.feature_engine import FeatureEngine, GameFeatures
from temvision.lol.models import PlayerData, GameData


class TestGameFeatures:
    """Test GameFeatures dataclass."""

    def test_default_values(self):
        f = GameFeatures()
        assert f.gold_diff == 0.0
        assert f.level_diff == 0.0
        assert f.hp_ratio == 0.0
        assert f.team_strength == 0.0
        assert f.game_phase == "early"
        assert f.raw == {}

    def test_to_dict(self):
        f = GameFeatures(gold_diff=1.5, level_diff=2.0, hp_ratio=0.8)
        d = f.to_dict()
        assert d["gold_diff"] == 1.5
        assert d["level_diff"] == 2.0
        assert d["hp_ratio"] == 0.8
        assert "game_phase" in d
        assert "team_strength" in d

    def test_to_vector(self):
        f = GameFeatures(
            gold_diff=1.5,
            level_diff=2.0,
            hp_ratio=0.8,
            game_phase="mid",
        )
        v = f.to_vector()
        assert isinstance(v, list)
        assert len(v) == 14
        assert v[0] == 1.5  # gold_diff
        assert v[1] == 2.0  # level_diff
        assert v[2] == 0.8  # hp_ratio
        # game_phase "mid" = 0.5
        assert v[-1] == 0.5

    def test_to_vector_early_phase(self):
        f = GameFeatures(game_phase="early")
        v = f.to_vector()
        assert v[-1] == 0.0

    def test_to_vector_late_phase(self):
        f = GameFeatures(game_phase="late")
        v = f.to_vector()
        assert v[-1] == 1.0


class TestFeatureEngine:
    """Test feature extraction engine."""

    def setup_method(self):
        self.engine = FeatureEngine()

    def test_extract_no_active_player(self):
        game_data = GameData()
        features = self.engine.extract(game_data)
        assert features.gold_diff == 0.0
        assert features.hp_ratio == 0.0

    def test_extract_hp_ratio(self):
        game_data = GameData(
            active_player=PlayerData(hp=500, max_hp=1000, level=10),
        )
        features = self.engine.extract(game_data)
        assert features.hp_ratio == 0.5

    def test_extract_hp_ratio_zero_max(self):
        game_data = GameData(
            active_player=PlayerData(hp=0, max_hp=0, level=10),
        )
        features = self.engine.extract(game_data)
        assert features.hp_ratio == 0.0

    def test_extract_gold_diff(self):
        game_data = GameData(
            active_player=PlayerData(
                current_gold=5000, hp=1000, max_hp=1000, level=10
            ),
            enemies=[PlayerData(current_gold=3000, level=10)],
        )
        features = self.engine.extract(game_data)
        # (5000 - 3000) / 1000 = 2.0
        assert features.gold_diff == pytest.approx(2.0)

    def test_extract_gold_diff_behind(self):
        game_data = GameData(
            active_player=PlayerData(
                current_gold=2000, hp=1000, max_hp=1000, level=10
            ),
            enemies=[PlayerData(current_gold=5000, level=10)],
        )
        features = self.engine.extract(game_data)
        # (2000 - 5000) / 1000 = -3.0
        assert features.gold_diff == pytest.approx(-3.0)

    def test_extract_level_diff(self):
        game_data = GameData(
            active_player=PlayerData(
                level=12, hp=1000, max_hp=1000
            ),
            enemies=[PlayerData(level=10), PlayerData(level=9)],
        )
        features = self.engine.extract(game_data)
        # 12 - avg(10, 9) = 12 - 9.5 = 2.5
        assert features.level_diff == pytest.approx(2.5)

    def test_extract_cs_diff(self):
        game_data = GameData(
            active_player=PlayerData(
                creep_score=150, hp=1000, max_hp=1000, level=10
            ),
            enemies=[PlayerData(creep_score=100, level=10)],
        )
        features = self.engine.extract(game_data)
        assert features.cs_diff == pytest.approx(50.0)

    def test_extract_game_phase_early(self):
        game_data = GameData(
            game_time=600.0,  # 10 minutes
            active_player=PlayerData(hp=1000, max_hp=1000, level=5),
        )
        features = self.engine.extract(game_data)
        assert features.game_phase == "early"
        assert features.game_time_minutes == pytest.approx(10.0)

    def test_extract_game_phase_mid(self):
        game_data = GameData(
            game_time=1200.0,  # 20 minutes
            active_player=PlayerData(hp=1000, max_hp=1000, level=12),
        )
        features = self.engine.extract(game_data)
        assert features.game_phase == "mid"

    def test_extract_game_phase_late(self):
        game_data = GameData(
            game_time=2100.0,  # 35 minutes
            active_player=PlayerData(hp=1000, max_hp=1000, level=18),
        )
        features = self.engine.extract(game_data)
        assert features.game_phase == "late"

    def test_extract_alive_counts(self):
        game_data = GameData(
            active_player=PlayerData(
                hp=1000, max_hp=1000, level=10, is_dead=False
            ),
            allies=[
                PlayerData(is_dead=False),
                PlayerData(is_dead=True),
                PlayerData(is_dead=False),
            ],
            enemies=[
                PlayerData(is_dead=False, level=10),
                PlayerData(is_dead=True, level=10),
            ],
        )
        features = self.engine.extract(game_data)
        # 3 alive allies (2 alive + player)
        assert features.alive_allies == 3
        # 1 alive enemy
        assert features.alive_enemies == 1
        assert features.alive_diff == 2

    def test_extract_team_strength_strong(self):
        """Team with gold, level, and numbers advantage should be strong."""
        game_data = GameData(
            game_time=900.0,
            active_player=PlayerData(
                current_gold=8000, level=12, hp=1000, max_hp=1000,
                kills=5, is_dead=False,
            ),
            allies=[
                PlayerData(
                    current_gold=6000, level=11, kills=3, is_dead=False
                ),
            ],
            enemies=[
                PlayerData(
                    current_gold=3000, level=8, kills=1, is_dead=True
                ),
                PlayerData(
                    current_gold=4000, level=9, kills=2, is_dead=False
                ),
            ],
        )
        features = self.engine.extract(game_data)
        assert features.team_strength > 0.0

    def test_extract_team_strength_weak(self):
        """Team behind in gold and levels should be weak."""
        game_data = GameData(
            game_time=900.0,
            active_player=PlayerData(
                current_gold=2000, level=7, hp=500, max_hp=1000,
                kills=1, is_dead=False,
            ),
            allies=[
                PlayerData(
                    current_gold=1500, level=6, kills=0, is_dead=True
                ),
            ],
            enemies=[
                PlayerData(
                    current_gold=7000, level=12, kills=8, is_dead=False
                ),
                PlayerData(
                    current_gold=6000, level=11, kills=5, is_dead=False
                ),
            ],
        )
        features = self.engine.extract(game_data)
        assert features.team_strength < 0.0

    def test_extract_kill_pressure(self):
        """Player with advantages should have high kill pressure."""
        game_data = GameData(
            active_player=PlayerData(
                current_gold=8000, level=12, hp=1000, max_hp=1000,
                is_dead=False,
            ),
            allies=[
                PlayerData(is_dead=False),
                PlayerData(is_dead=False),
            ],
            enemies=[
                PlayerData(
                    current_gold=4000, level=8, is_dead=False
                ),
            ],
        )
        features = self.engine.extract(game_data)
        assert features.kill_pressure > 0.5

    def test_extract_kill_pressure_low(self):
        """Player behind with low HP should have low kill pressure."""
        game_data = GameData(
            active_player=PlayerData(
                current_gold=2000, level=7, hp=200, max_hp=1000,
                is_dead=False,
            ),
            allies=[],
            enemies=[
                PlayerData(
                    current_gold=6000, level=12, is_dead=False
                ),
            ],
        )
        features = self.engine.extract(game_data)
        assert features.kill_pressure < 0.5

    def test_extract_team_gold_diff(self):
        game_data = GameData(
            active_player=PlayerData(
                current_gold=5000, hp=1000, max_hp=1000, level=10
            ),
            allies=[
                PlayerData(current_gold=4000),
            ],
            enemies=[
                PlayerData(current_gold=3000, level=10),
                PlayerData(current_gold=3000, level=10),
            ],
        )
        features = self.engine.extract(game_data)
        # Team: 5000+4000=9000, Enemies: 3000+3000=6000
        # Diff: (9000-6000)/1000 = 3.0
        assert features.team_gold_diff == pytest.approx(3.0)

    def test_extract_team_kill_diff(self):
        game_data = GameData(
            active_player=PlayerData(
                kills=5, hp=1000, max_hp=1000, level=10
            ),
            allies=[PlayerData(kills=3)],
            enemies=[
                PlayerData(kills=2, level=10),
                PlayerData(kills=1, level=10),
            ],
        )
        features = self.engine.extract(game_data)
        # Team kills: 5+3=8, Enemy kills: 2+1=3, diff = 5
        assert features.team_kill_diff == pytest.approx(5.0)

    def test_extract_no_enemies(self):
        game_data = GameData(
            active_player=PlayerData(hp=1000, max_hp=1000, level=10),
            enemies=[],
        )
        features = self.engine.extract(game_data)
        assert features.gold_diff == 0.0
        assert features.level_diff == 0.0
        assert features.cs_diff == 0.0

    def test_extract_raw_values(self):
        game_data = GameData(
            active_player=PlayerData(
                current_gold=5000, level=10, hp=800, max_hp=1000,
                creep_score=120, kills=3, deaths=1, assists=5,
            ),
        )
        features = self.engine.extract(game_data)
        assert features.raw["player_gold"] == 5000
        assert features.raw["player_level"] == 10
        assert features.raw["player_hp"] == 800
        assert features.raw["player_cs"] == 120
