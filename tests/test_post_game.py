"""Tests for post-game analysis."""

import pytest

from temvision.lol.post_game import PostGameAnalyzer
from temvision.lol.models import PlayerData, GameData, PostGameStats


class TestPostGameStats:
    """Test PostGameStats dataclass."""

    def test_default_values(self):
        s = PostGameStats()
        assert s.game_duration == 0.0
        assert s.kills == 0
        assert s.deaths == 0
        assert s.assists == 0
        assert s.performance_score == 0.0
        assert s.mvp is False
        assert s.grade == ""

    def test_kda_string(self):
        s = PostGameStats(kills=5, deaths=2, assists=8)
        assert s.kda_string == "5/2/8"


class TestPostGameAnalyzer:
    """Test post-game analyzer."""

    def setup_method(self):
        self.analyzer = PostGameAnalyzer()

    def test_analyze_no_active_player(self):
        game_data = GameData()
        result = self.analyzer.analyze(game_data)
        assert result is None

    def test_analyze_basic(self):
        game_data = GameData(
            game_time=1800.0,  # 30 min game
            active_player=PlayerData(
                champion_name="Jinx",
                summoner_name="TestPlayer",
                kills=10,
                deaths=3,
                assists=8,
                creep_score=250,
                current_gold=15000,
            ),
            allies=[
                PlayerData(
                    summoner_name="Ally1", kills=5, deaths=4,
                    assists=6, creep_score=180, current_gold=12000,
                ),
            ],
            enemies=[
                PlayerData(
                    summoner_name="Enemy1", kills=3, deaths=5,
                    assists=4, creep_score=200, current_gold=11000,
                ),
            ],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    summoner_name="TestPlayer",
                    kills=10, deaths=3, assists=8,
                    creep_score=250, current_gold=15000,
                ),
                PlayerData(
                    summoner_name="Ally1", kills=5, deaths=4,
                    assists=6, creep_score=180, current_gold=12000,
                ),
                PlayerData(
                    summoner_name="Enemy1", kills=3, deaths=5,
                    assists=4, creep_score=200, current_gold=11000,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result is not None
        assert result.player_champion == "Jinx"
        assert result.kills == 10
        assert result.deaths == 3
        assert result.assists == 8
        assert result.cs == 250
        assert result.game_duration == 1800.0

    def test_analyze_performance_score(self):
        game_data = GameData(
            game_time=1800.0,
            active_player=PlayerData(
                champion_name="Jinx",
                kills=10,
                deaths=2,
                assists=8,
                creep_score=250,
                current_gold=15000,
            ),
            allies=[],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    kills=10, deaths=2, assists=8,
                    creep_score=250, current_gold=15000,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.performance_score > 0
        assert result.performance_score <= 100

    def test_analyze_grade_s(self):
        """High performing player should get S grade."""
        game_data = GameData(
            game_time=1800.0,
            active_player=PlayerData(
                champion_name="Jinx",
                kills=15,
                deaths=1,
                assists=10,
                creep_score=300,
                current_gold=20000,
            ),
            allies=[],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    kills=15, deaths=1, assists=10,
                    creep_score=300, current_gold=20000,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.grade in ("S", "A")  # Very high performance

    def test_analyze_grade_low(self):
        """Poor performing player should get low grade."""
        game_data = GameData(
            game_time=1800.0,
            active_player=PlayerData(
                champion_name="Jinx",
                kills=0,
                deaths=10,
                assists=1,
                creep_score=50,
                current_gold=5000,
            ),
            allies=[],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    kills=0, deaths=10, assists=1,
                    creep_score=50, current_gold=5000,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.grade in ("C", "D")

    def test_analyze_mvp_yes(self):
        """Player with highest score should be MVP."""
        game_data = GameData(
            game_time=1800.0,
            active_player=PlayerData(
                champion_name="Jinx",
                summoner_name="TestPlayer",
                kills=15,
                deaths=1,
                assists=10,
                creep_score=300,
                current_gold=20000,
            ),
            allies=[
                PlayerData(
                    summoner_name="Ally1",
                    kills=3,
                    deaths=5,
                    assists=6,
                    creep_score=150,
                    current_gold=10000,
                ),
            ],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    summoner_name="TestPlayer",
                    kills=15, deaths=1, assists=10,
                    creep_score=300, current_gold=20000,
                ),
                PlayerData(
                    summoner_name="Ally1",
                    kills=3, deaths=5, assists=6,
                    creep_score=150, current_gold=10000,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.mvp is True

    def test_analyze_mvp_no(self):
        """Player with lower score should not be MVP."""
        game_data = GameData(
            game_time=1800.0,
            active_player=PlayerData(
                champion_name="Jinx",
                summoner_name="TestPlayer",
                kills=2,
                deaths=8,
                assists=3,
                creep_score=100,
                current_gold=8000,
            ),
            allies=[
                PlayerData(
                    summoner_name="Ally1",
                    kills=15,
                    deaths=1,
                    assists=10,
                    creep_score=300,
                    current_gold=20000,
                ),
            ],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    summoner_name="TestPlayer",
                    kills=2, deaths=8, assists=3,
                    creep_score=100, current_gold=8000,
                ),
                PlayerData(
                    summoner_name="Ally1",
                    kills=15, deaths=1, assists=10,
                    creep_score=300, current_gold=20000,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.mvp is False

    def test_analyze_cs_per_min(self):
        game_data = GameData(
            game_time=1200.0,  # 20 min
            active_player=PlayerData(
                champion_name="Jinx",
                creep_score=160,
            ),
            allies=[],
            enemies=[],
            all_players=[
                PlayerData(champion_name="Jinx", creep_score=160),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.cs_per_min == pytest.approx(8.0)

    def test_analyze_kda_ratio_no_deaths(self):
        game_data = GameData(
            game_time=1200.0,
            active_player=PlayerData(
                champion_name="Jinx",
                kills=5,
                deaths=0,
                assists=10,
            ),
            allies=[],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    kills=5, deaths=0, assists=10,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert result.kda_ratio == 15.0

    def test_analyze_all_player_stats(self):
        """All player stats should be populated."""
        game_data = GameData(
            game_time=1200.0,
            active_player=PlayerData(
                champion_name="Jinx",
                summoner_name="Player1",
                kills=5, deaths=2, assists=8,
            ),
            allies=[],
            enemies=[],
            all_players=[
                PlayerData(
                    champion_name="Jinx",
                    summoner_name="Player1",
                    kills=5, deaths=2, assists=8,
                ),
                PlayerData(
                    champion_name="Zed",
                    summoner_name="Player2",
                    kills=3, deaths=4, assists=5,
                ),
            ],
        )
        result = self.analyzer.analyze(game_data)
        assert len(result.all_player_stats) == 2
        assert result.all_player_stats[0]["champion_name"] == "Jinx"
        assert result.all_player_stats[1]["champion_name"] == "Zed"
