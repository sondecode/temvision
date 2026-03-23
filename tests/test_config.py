"""Tests for the configuration loader."""

import os
import tempfile

import pytest
import yaml

from temvision.config.loader import ConfigLoader


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory with test configs."""
    config = {
        "game": "lol",
        "capture": {"minimap_region": [1600, 800, 300, 300]},
        "vision": {"detect": ["enemy_icon"]},
        "mapping": {"enemy_icon": "enemy"},
        "rules": [
            {
                "name": "enemy_missing",
                "condition": "enemy_visible == false",
                "action": "⚠️ Enemy missing",
                "priority": "high",
            }
        ],
    }
    config_path = tmp_path / "lol.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)
    return str(tmp_path)


class TestConfigLoader:
    def test_load_valid_config(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("lol")
        assert config["game"] == "lol"
        assert config["capture"]["minimap_region"] == [1600, 800, 300, 300]

    def test_load_missing_config(self, tmp_path):
        loader = ConfigLoader(str(tmp_path))
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent")

    def test_get_capture_config(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("lol")
        capture = loader.get_capture_config(config)
        assert "minimap_region" in capture

    def test_get_vision_config(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("lol")
        vision = loader.get_vision_config(config)
        assert "detect" in vision
        assert "enemy_icon" in vision["detect"]

    def test_get_rules(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("lol")
        rules = loader.get_rules(config)
        assert len(rules) == 1
        assert rules[0]["name"] == "enemy_missing"

    def test_get_mapping(self, config_dir):
        loader = ConfigLoader(config_dir)
        config = loader.load("lol")
        mapping = loader.get_mapping(config)
        assert mapping["enemy_icon"] == "enemy"

    def test_list_games(self, config_dir):
        loader = ConfigLoader(config_dir)
        games = loader.list_games()
        assert "lol" in games

    def test_config_caching(self, config_dir):
        loader = ConfigLoader(config_dir)
        config1 = loader.load("lol")
        config2 = loader.load("lol")
        assert config1 is config2

    def test_empty_config(self, tmp_path):
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")
        loader = ConfigLoader(str(tmp_path))
        config = loader.load("empty")
        assert config == {}

    def test_list_games_missing_dir(self):
        loader = ConfigLoader("/nonexistent/path")
        assert loader.list_games() == []
