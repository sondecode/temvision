"""Tests for build recommender and rune importer."""

import json
import os
import pytest

from temvision.lol.build_recommender import (
    BuildRecommender,
    BuildRecommendation,
    RunePage,
)


@pytest.fixture
def builds_file(tmp_path):
    """Create a temporary builds.json file."""
    data = {
        "aatrox": {
            "default": {
                "runes": {
                    "name": "Test Aatrox",
                    "primary_style": 8000,
                    "sub_style": 8400,
                    "selected_perks": [8010, 9111],
                    "stat_shards": [5008, 5008, 5001],
                },
                "starting_items": ["Doran's Blade", "Health Potion"],
                "core_items": ["Eclipse", "Black Cleaver"],
                "summoner_spells": ["Flash", "Teleport"],
                "skill_order": "Q > E > W",
                "win_rate": 51.2,
            },
            "top": {
                "runes": {
                    "name": "Test Aatrox TOP",
                    "primary_style": 8000,
                    "sub_style": 8400,
                    "selected_perks": [8010, 9111],
                    "stat_shards": [5008, 5008, 5001],
                },
                "starting_items": ["Doran's Blade"],
                "core_items": ["Eclipse"],
                "summoner_spells": ["Flash", "Teleport"],
                "skill_order": "Q > E > W",
                "win_rate": 52.0,
            },
        }
    }
    path = tmp_path / "builds.json"
    path.write_text(json.dumps(data))
    return str(path)


class TestBuildRecommender:
    """Test build recommender lookups."""

    def test_recommend_default(self, builds_file):
        rec = BuildRecommender(builds_path=builds_file)
        result = rec.recommend("Aatrox")
        assert result is not None
        assert result.champion == "Aatrox"
        assert "Eclipse" in result.core_items
        assert result.rune_page is not None
        assert result.rune_page.primary_style == 8000

    def test_recommend_specific_lane(self, builds_file):
        rec = BuildRecommender(builds_path=builds_file)
        result = rec.recommend("Aatrox", lane="top")
        assert result is not None
        assert result.win_rate == 52.0

    def test_recommend_fallback_to_default(self, builds_file):
        rec = BuildRecommender(builds_path=builds_file)
        result = rec.recommend("Aatrox", lane="jungle")
        assert result is not None
        assert result.win_rate == 51.2  # falls back to default

    def test_recommend_unknown_champion(self, builds_file):
        rec = BuildRecommender(builds_path=builds_file)
        result = rec.recommend("UnknownChamp")
        assert result is None

    def test_no_file(self, tmp_path):
        rec = BuildRecommender(builds_path=str(tmp_path / "missing.json"))
        result = rec.recommend("Aatrox")
        assert result is None

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json!")
        rec = BuildRecommender(builds_path=str(path))
        result = rec.recommend("Aatrox")
        assert result is None


class TestRunePage:
    """Test rune page dataclass."""

    def test_default(self):
        rp = RunePage()
        assert rp.name == ""
        assert rp.primary_style == 0
        assert rp.selected_perks == []

    def test_from_data(self):
        rp = RunePage(
            name="Test",
            primary_style=8000,
            sub_style=8400,
            selected_perks=[8010, 9111],
            stat_shards=[5008, 5001],
        )
        assert rp.primary_style == 8000
        assert len(rp.selected_perks) == 2


class TestBuildRecommendation:
    def test_default(self):
        b = BuildRecommendation()
        assert b.champion == ""
        assert b.core_items == []
        assert b.source == "bundled"
