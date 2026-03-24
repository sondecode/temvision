"""Tests for LoL data models."""

import pytest

from temvision.lol.models import PlayerData, GameData, PreGameStats, PostGameStats


class TestPlayerData:
    """Test PlayerData model."""

    def test_default_values(self):
        player = PlayerData()
        assert player.summoner_name == ""
        assert player.champion_name == ""
        assert player.level == 0
        assert player.current_gold == 0.0
        assert player.hp == 0.0
        assert player.max_hp == 0.0
        assert player.kills == 0
        assert player.deaths == 0
        assert player.assists == 0
        assert player.items == []
        assert player.is_dead is False

    def test_kda_string(self):
        player = PlayerData(kills=5, deaths=2, assists=10)
        assert player.kda_string == "5/2/10"

    def test_kda_ratio(self):
        player = PlayerData(kills=5, deaths=2, assists=10)
        assert player.kda_ratio == 7.5

    def test_kda_ratio_zero_deaths(self):
        player = PlayerData(kills=5, deaths=0, assists=10)
        assert player.kda_ratio == 15.0

    def test_hp_percent(self):
        player = PlayerData(hp=500, max_hp=1000)
        assert player.hp_percent == 50.0

    def test_hp_percent_zero_max(self):
        player = PlayerData(hp=0, max_hp=0)
        assert player.hp_percent == 0.0

    def test_hp_percent_full(self):
        player = PlayerData(hp=1000, max_hp=1000)
        assert player.hp_percent == 100.0


class TestGameData:
    """Test GameData model."""

    def test_default_values(self):
        game = GameData()
        assert game.game_time == 0.0
        assert game.game_mode == ""
        assert game.active_player is None
        assert game.allies == []
        assert game.enemies == []

    def test_gold_difference_no_player(self):
        game = GameData()
        assert game.gold_difference == 0.0

    def test_gold_difference_no_enemies(self):
        game = GameData(active_player=PlayerData(current_gold=5000))
        assert game.gold_difference == 0.0

    def test_gold_difference(self):
        game = GameData(
            active_player=PlayerData(current_gold=5000),
            enemies=[
                PlayerData(current_gold=4000),
                PlayerData(current_gold=3000),
            ],
        )
        # avg enemy gold = 3500, diff = 5000 - 3500 = 1500
        assert game.gold_difference == 1500.0

    def test_level_difference(self):
        game = GameData(
            active_player=PlayerData(level=10),
            enemies=[
                PlayerData(level=8),
                PlayerData(level=9),
            ],
        )
        # avg enemy level = 8.5, diff = 10 - 8.5 = 1.5
        assert game.level_difference == 1.5

    def test_level_difference_no_enemies(self):
        game = GameData(active_player=PlayerData(level=10))
        assert game.level_difference == 0.0

    def test_get_enemy_by_position(self):
        enemy = PlayerData(position="TOP", champion_name="Garen")
        game = GameData(enemies=[enemy])
        found = game.get_enemy_by_position("top")
        assert found is not None
        assert found.champion_name == "Garen"

    def test_get_enemy_by_position_not_found(self):
        game = GameData(enemies=[PlayerData(position="MID")])
        assert game.get_enemy_by_position("TOP") is None

    def test_team_total_gold(self):
        game = GameData(
            active_player=PlayerData(current_gold=5000),
            allies=[
                PlayerData(current_gold=4000),
                PlayerData(current_gold=3000),
            ],
        )
        assert game.team_total_gold == 12000.0

    def test_team_total_gold_no_player(self):
        game = GameData(
            allies=[PlayerData(current_gold=4000)],
        )
        assert game.team_total_gold == 4000.0

    def test_enemy_total_gold(self):
        game = GameData(
            enemies=[
                PlayerData(current_gold=4000),
                PlayerData(current_gold=3000),
            ],
        )
        assert game.enemy_total_gold == 7000.0

    def test_team_total_kills(self):
        game = GameData(
            active_player=PlayerData(kills=5),
            allies=[
                PlayerData(kills=3),
                PlayerData(kills=2),
            ],
        )
        assert game.team_total_kills == 10

    def test_enemy_total_kills(self):
        game = GameData(
            enemies=[
                PlayerData(kills=4),
                PlayerData(kills=6),
            ],
        )
        assert game.enemy_total_kills == 10

    def test_team_gold_diff(self):
        game = GameData(
            active_player=PlayerData(current_gold=5000),
            allies=[PlayerData(current_gold=4000)],
            enemies=[
                PlayerData(current_gold=3000),
                PlayerData(current_gold=2000),
            ],
        )
        # team: 9000, enemy: 5000, diff = 4000
        assert game.team_gold_diff == 4000.0

    def test_team_kill_diff(self):
        game = GameData(
            active_player=PlayerData(kills=5),
            allies=[PlayerData(kills=3)],
            enemies=[
                PlayerData(kills=2),
                PlayerData(kills=4),
            ],
        )
        # team: 8, enemy: 6, diff = 2
        assert game.team_kill_diff == 2


class TestPostGameStats:
    """Test PostGameStats model."""

    def test_default_values(self):
        stats = PostGameStats()
        assert stats.game_duration == 0.0
        assert stats.kills == 0
        assert stats.deaths == 0
        assert stats.assists == 0
        assert stats.performance_score == 0.0
        assert stats.mvp is False

    def test_kda_string(self):
        stats = PostGameStats(kills=5, deaths=2, assists=8)
        assert stats.kda_string == "5/2/8"


class TestPreGameStats:
    """Test PreGameStats model."""

    def test_default_values(self):
        stats = PreGameStats()
        assert stats.summoner_name == ""
        assert stats.rank == ""
        assert stats.tier == ""
        assert stats.win_rate == 0.0

    def test_rank_string(self):
        stats = PreGameStats(tier="GOLD", rank="II", lp=75)
        assert stats.rank_string == "GOLD II (75 LP)"

    def test_rank_string_unranked(self):
        stats = PreGameStats()
        assert stats.rank_string == "Unranked"
