"""Tests for SQLite match history."""

import os
import pytest

from temvision.lol.match_history import MatchHistory, MatchRecord
from temvision.lol.models import PostGameStats


@pytest.fixture
def db(tmp_path):
    """Create a MatchHistory with a temp database."""
    return MatchHistory(db_path=str(tmp_path / "test.db"))


class TestMatchRecord:
    def test_kda_string(self):
        r = MatchRecord(kills=5, deaths=2, assists=8)
        assert r.kda_string == "5/2/8"

    def test_defaults(self):
        r = MatchRecord()
        assert r.champion == ""
        assert r.win is False
        assert r.mvp is False


class TestMatchHistory:
    def test_save_and_recent(self, db):
        stats = PostGameStats(
            player_champion="Jinx",
            kills=10,
            deaths=3,
            assists=8,
            cs=250,
            cs_per_min=8.3,
            gold_earned=15000,
            game_duration=1800.0,
            kda_ratio=6.0,
            performance_score=85.0,
            grade="S",
            mvp=True,
            win=True,
        )
        row_id = db.save(stats)
        assert row_id > 0

        recent = db.recent(limit=10)
        assert len(recent) == 1
        assert recent[0].champion == "Jinx"
        assert recent[0].kills == 10
        assert recent[0].grade == "S"
        assert recent[0].mvp is True
        assert recent[0].win is True

    def test_multiple_saves(self, db):
        for i in range(5):
            stats = PostGameStats(
                player_champion=f"Champ{i}",
                kills=i,
                deaths=1,
                assists=i + 1,
            )
            db.save(stats)

        recent = db.recent(limit=3)
        assert len(recent) == 3
        # Newest first
        assert recent[0].champion == "Champ4"

    def test_champion_stats(self, db):
        for _ in range(3):
            db.save(PostGameStats(
                player_champion="Jinx",
                kills=10,
                deaths=2,
                kda_ratio=6.0,
                cs_per_min=8.0,
                performance_score=80.0,
                win=True,
            ))
        db.save(PostGameStats(
            player_champion="Jinx",
            kills=2,
            deaths=5,
            kda_ratio=0.4,
            cs_per_min=5.0,
            performance_score=30.0,
            win=False,
        ))

        stats = db.champion_stats("Jinx")
        assert stats["games"] == 4
        assert stats["wins"] == 3

    def test_champion_stats_unknown(self, db):
        stats = db.champion_stats("Unknown")
        assert stats["games"] == 0

    def test_overall_stats(self, db):
        db.save(PostGameStats(player_champion="A", win=True, kda_ratio=5.0))
        db.save(PostGameStats(player_champion="B", win=False, kda_ratio=1.0))
        overall = db.overall_stats()
        assert overall["games"] == 2
        assert overall["wins"] == 1
        assert overall["win_rate"] == 50.0

    def test_overall_stats_empty(self, db):
        overall = db.overall_stats()
        assert overall["games"] == 0
        assert overall["win_rate"] == 0.0

    def test_overlay_summary_empty(self, db):
        lines = db.overlay_summary()
        assert len(lines) == 1
        assert "No match history" in lines[0]

    def test_overlay_summary_with_data(self, db):
        db.save(PostGameStats(
            player_champion="Jinx",
            kills=10,
            deaths=2,
            assists=8,
            grade="S",
            performance_score=85.0,
            win=True,
        ))
        lines = db.overlay_summary()
        assert len(lines) >= 1
        assert "1 games" in lines[0]
