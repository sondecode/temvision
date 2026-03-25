"""Tests for PreGameAnalyzer champ select parsing."""

from unittest.mock import MagicMock

from temvision.lol.pre_game import PreGameAnalyzer
from temvision.lol.riot_api import RiotAPI


def build_session():
    return {
        "myTeam": [
            {
                "summonerName": "ally1",
                "summonerId": "ally1-id",
                "championId": 266,
                "assignedPosition": "TOP",
            },
            {
                "summonerName": "ally2",
                "summonerId": "ally2-id",
                "championId": 64,
                "assignedPosition": "JUNGLE",
            },
        ],
        "theirTeam": [
            {
                "summonerName": "enemy1",
                "summonerId": "enemy1-id",
                "championId": 157,
                "assignedPosition": "MID",
            }
        ],
    }


def test_fetch_builds_players_with_positions():
    lcu = MagicMock()
    lcu.get_champ_select_session.return_value = build_session()

    riot = MagicMock(spec=RiotAPI)
    riot.is_available.return_value = False

    analyzer = PreGameAnalyzer(lcu_client=lcu, riot_api=riot)
    info = analyzer.fetch()

    assert info is not None
    assert len(info.allies) == 2
    assert len(info.enemies) == 1
    assert info.allies[0].position == "TOP"
    assert info.enemies[0].champion_id == 157
    assert info.enemies[0].champion_name == "Yasuo"


def test_fetch_enriches_rank_when_available():
    lcu = MagicMock()
    lcu.get_champ_select_session.return_value = build_session()

    riot = MagicMock(spec=RiotAPI)
    riot.is_available.return_value = True
    riot.get_ranked_stats.return_value = [
        {
            "queueType": "RANKED_SOLO_5x5",
            "tier": "GOLD",
            "rank": "II",
            "leaguePoints": 60,
            "wins": 20,
            "losses": 10,
        }
    ]
    riot.build_pre_game_stats.return_value = MagicMock(
        tier="GOLD", rank="II", lp=60, win_rate=66.6
    )

    analyzer = PreGameAnalyzer(lcu_client=lcu, riot_api=riot)
    info = analyzer.fetch()

    assert info is not None
    assert info.fetched_rank is True
    assert any(p.rank_text for p in info.allies + info.enemies)
    # Champion names still mapped
    assert info.allies[0].champion_name == "Aatrox"
