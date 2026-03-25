"""Tests for per-champion configuration."""

import pytest
import yaml

from temvision.lol.champion_config import ChampionConfig


class TestChampionConfig:
    """Test per-champion configuration loading and merging."""

    def test_get_empty_when_no_file(self, tmp_path):
        cc = ChampionConfig(config_dir=str(tmp_path))
        assert cc.get("Jinx") == {}

    def test_get_loads_yaml(self, tmp_path):
        data = {"overlay": {"fast_interval": 0.2}, "tips": ["Farm safely"]}
        (tmp_path / "jinx.yaml").write_text(yaml.dump(data))
        cc = ChampionConfig(config_dir=str(tmp_path))
        result = cc.get("Jinx")
        assert result["overlay"]["fast_interval"] == 0.2
        assert result["tips"] == ["Farm safely"]

    def test_get_cached(self, tmp_path):
        data = {"tips": ["test"]}
        (tmp_path / "jinx.yaml").write_text(yaml.dump(data))
        cc = ChampionConfig(config_dir=str(tmp_path))
        r1 = cc.get("Jinx")
        r2 = cc.get("Jinx")
        assert r1 is r2  # same object = cached

    def test_clear_cache(self, tmp_path):
        data = {"tips": ["v1"]}
        (tmp_path / "jinx.yaml").write_text(yaml.dump(data))
        cc = ChampionConfig(config_dir=str(tmp_path))
        cc.get("Jinx")
        cc.clear_cache()
        assert cc._cache == {}

    def test_get_merged(self, tmp_path):
        champ_data = {"overlay": {"fast_interval": 0.15}, "tips": ["Focus CS"]}
        (tmp_path / "jinx.yaml").write_text(yaml.dump(champ_data))
        cc = ChampionConfig(config_dir=str(tmp_path))

        base = {"overlay": {"fast_interval": 0.25, "slow_interval": 1.0}, "game": "lol"}
        merged = cc.get_merged("Jinx", base)

        assert merged["overlay"]["fast_interval"] == 0.15  # overridden
        assert merged["overlay"]["slow_interval"] == 1.0  # kept
        assert merged["game"] == "lol"  # kept
        assert merged["tips"] == ["Focus CS"]  # added

    def test_get_merged_no_override(self, tmp_path):
        cc = ChampionConfig(config_dir=str(tmp_path))
        base = {"game": "lol", "overlay": {"fast_interval": 0.25}}
        merged = cc.get_merged("Nonexistent", base)
        assert merged is base  # same object, no copy needed

    def test_get_tips(self, tmp_path):
        data = {"tips": ["Tip 1", "Tip 2"]}
        (tmp_path / "jinx.yaml").write_text(yaml.dump(data))
        cc = ChampionConfig(config_dir=str(tmp_path))
        tips = cc.get_tips("Jinx")
        assert tips == ["Tip 1", "Tip 2"]

    def test_get_tips_no_file(self, tmp_path):
        cc = ChampionConfig(config_dir=str(tmp_path))
        assert cc.get_tips("Jinx") == []

    def test_available_champions(self, tmp_path):
        (tmp_path / "jinx.yaml").write_text("tips: []")
        (tmp_path / "zed.yaml").write_text("tips: []")
        (tmp_path / "readme.md").write_text("not yaml")
        cc = ChampionConfig(config_dir=str(tmp_path))
        champs = cc.available_champions()
        assert set(champs) == {"jinx", "zed"}

    def test_available_champions_no_dir(self, tmp_path):
        cc = ChampionConfig(config_dir=str(tmp_path / "nonexistent"))
        assert cc.available_champions() == []

    def test_normalize_name(self):
        assert ChampionConfig._normalize("Lee Sin") == "lee_sin"
        assert ChampionConfig._normalize("Kai'Sa") == "kaisa"
        assert ChampionConfig._normalize("JINX") == "jinx"

    def test_deep_merge_nested(self):
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10, "e": 5}, "f": 6}
        result = ChampionConfig._deep_merge(base, override)
        assert result == {"a": {"b": 10, "c": 2, "e": 5}, "d": 3, "f": 6}

    def test_deep_merge_does_not_mutate_base(self):
        base = {"a": {"b": 1}}
        override = {"a": {"b": 2}}
        ChampionConfig._deep_merge(base, override)
        assert base["a"]["b"] == 1

    def test_load_invalid_yaml(self, tmp_path):
        (tmp_path / "bad.yaml").write_text("[unclosed: {bracket")
        cc = ChampionConfig(config_dir=str(tmp_path))
        result = cc.get("Bad")
        assert result == {}

    def test_load_non_dict_yaml(self, tmp_path):
        (tmp_path / "weird.yaml").write_text("just a string")
        cc = ChampionConfig(config_dir=str(tmp_path))
        result = cc.get("Weird")
        assert result == {}
