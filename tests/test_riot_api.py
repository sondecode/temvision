"""Tests for Riot API client."""

import pytest

from temvision.lol.riot_api import RiotAPI, REGIONS, ROUTING_REGIONS
from temvision.lol.models import PreGameStats


class TestRiotAPI:
    """Test Riot API client."""

    def test_not_available_without_key(self):
        api = RiotAPI(api_key="")
        assert api.is_available() is False

    def test_available_with_key(self):
        api = RiotAPI(api_key="test-key")
        assert api.is_available() is True

    def test_default_region(self):
        api = RiotAPI(api_key="test")
        assert api.region == "na"
        assert api.platform == "na1"
        assert api.routing == "americas"

    def test_kr_region(self):
        api = RiotAPI(api_key="test", region="kr")
        assert api.platform == "kr"
        assert api.routing == "asia"

    def test_euw_region(self):
        api = RiotAPI(api_key="test", region="euw")
        assert api.platform == "euw1"
        assert api.routing == "europe"

    def test_get_summoner_without_key_returns_none(self):
        api = RiotAPI(api_key="")
        result = api.get_summoner_by_name("test", "NA1")
        assert result is None

    def test_get_ranked_stats_without_key_returns_none(self):
        api = RiotAPI(api_key="")
        result = api.get_ranked_stats("summoner-id")
        assert result is None

    def test_get_match_history_without_key_returns_none(self):
        api = RiotAPI(api_key="")
        result = api.get_match_history("puuid-123")
        assert result is None

    def test_get_match_detail_without_key_returns_none(self):
        api = RiotAPI(api_key="")
        result = api.get_match_detail("NA1_12345")
        assert result is None

    def test_regions_mapping(self):
        assert "na" in REGIONS
        assert "kr" in REGIONS
        assert "euw" in REGIONS
        assert "vn" in REGIONS

    def test_routing_regions_mapping(self):
        assert ROUTING_REGIONS["na"] == "americas"
        assert ROUTING_REGIONS["kr"] == "asia"
        assert ROUTING_REGIONS["euw"] == "europe"
        assert ROUTING_REGIONS["vn"] == "sea"


class TestBuildPreGameStats:
    """Test building pre-game stats from API data."""

    def setup_method(self):
        self.api = RiotAPI(api_key="test")

    def test_build_stats_with_ranked_data(self):
        ranked = [
            {
                "queueType": "RANKED_SOLO_5x5",
                "tier": "GOLD",
                "rank": "II",
                "leaguePoints": 75,
                "wins": 60,
                "losses": 40,
            }
        ]
        stats = self.api.build_pre_game_stats("Player1", ranked, [])
        assert stats.tier == "GOLD"
        assert stats.rank == "II"
        assert stats.lp == 75
        assert stats.total_games == 100
        assert stats.win_rate == 60.0

    def test_build_stats_with_match_history(self):
        matches = [
            {
                "info": {
                    "participants": [
                        {
                            "riotIdGameName": "Player1",
                            "championName": "Jinx",
                            "win": True,
                            "kills": 10,
                            "deaths": 2,
                            "assists": 8,
                        }
                    ]
                }
            },
            {
                "info": {
                    "participants": [
                        {
                            "riotIdGameName": "Player1",
                            "championName": "Caitlyn",
                            "win": False,
                            "kills": 4,
                            "deaths": 6,
                            "assists": 5,
                        }
                    ]
                }
            },
        ]
        stats = self.api.build_pre_game_stats("Player1", [], matches)
        # Total: 14 kills, 8 deaths, 13 assists → KDA = (14+13)/8 = 3.375
        assert stats.avg_kda == pytest.approx(3.375)
        assert len(stats.recent_matches) == 2

    def test_build_stats_empty_data(self):
        stats = self.api.build_pre_game_stats("Player1", [], [])
        assert stats.summoner_name == "Player1"
        assert stats.tier == ""
        assert stats.avg_kda == 0.0

    def test_build_stats_no_deaths(self):
        matches = [
            {
                "info": {
                    "participants": [
                        {
                            "riotIdGameName": "Player1",
                            "championName": "Jinx",
                            "win": True,
                            "kills": 10,
                            "deaths": 0,
                            "assists": 8,
                        }
                    ]
                }
            },
        ]
        stats = self.api.build_pre_game_stats("Player1", [], matches)
        assert stats.avg_kda == 18.0  # (10+8)/0 → float(10+8)

    def test_build_stats_ignores_flex_queue(self):
        ranked = [
            {
                "queueType": "RANKED_FLEX_SR",
                "tier": "PLATINUM",
                "rank": "I",
                "leaguePoints": 50,
                "wins": 30,
                "losses": 20,
            }
        ]
        stats = self.api.build_pre_game_stats("Player1", ranked, [])
        # Should not pick up flex queue data
        assert stats.tier == ""
        assert stats.rank == ""
