"""Per-champion configuration support.

Allows champion-specific overlay settings that override the
global LoL config defaults: HUD regions, preferred builds,
notification preferences, and play-style tips.

Config file: ``~/.temvision/champions/<champion_name>.yaml``
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".temvision", "champions")


class ChampionConfig:
    """Per-champion configuration manager.

    Loads champion YAML files from ``~/.temvision/champions/``
    and merges them with the global LoL config on a per-key basis.

    Example ``~/.temvision/champions/jinx.yaml``::

        overlay:
          fast_interval: 0.2   # faster updates for ADC
        threat_scorer:
          top_n: 5             # show more threats
        tips:
          - "Farm safely until 2 items"
          - "Position behind frontline in teamfights"
    """

    def __init__(self, config_dir: str = _DEFAULT_DIR) -> None:
        self._config_dir = config_dir
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, champion_name: str) -> dict[str, Any]:
        """Return config for a champion (cached). Empty dict if none."""
        key = self._normalize(champion_name)
        if key in self._cache:
            return self._cache[key]

        data = self._load(key)
        self._cache[key] = data
        return data

    def get_merged(
        self, champion_name: str, base_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Return base config with champion overrides deep-merged on top."""
        overrides = self.get(champion_name)
        if not overrides:
            return base_config
        return self._deep_merge(base_config, overrides)

    def get_tips(self, champion_name: str) -> list[str]:
        """Return champion-specific gameplay tips."""
        data = self.get(champion_name)
        return data.get("tips", [])

    def available_champions(self) -> list[str]:
        """List champions with custom configs."""
        if not os.path.isdir(self._config_dir):
            return []
        return [
            f.replace(".yaml", "")
            for f in sorted(os.listdir(self._config_dir))
            if f.endswith(".yaml")
        ]

    def clear_cache(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------------

    def _load(self, key: str) -> dict[str, Any]:
        path = os.path.join(self._config_dir, f"{key}.yaml")
        if not os.path.isfile(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            logger.warning("Failed to load champion config %s: %s", path, exc)
            return {}

    @staticmethod
    def _normalize(name: str) -> str:
        """Normalize champion name to lowercase filename-safe key."""
        return name.lower().replace(" ", "_").replace("'", "")

    @staticmethod
    def _deep_merge(
        base: dict[str, Any], override: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively merge *override* into a copy of *base*."""
        merged = dict(base)
        for key, val in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(val, dict)
            ):
                merged[key] = ChampionConfig._deep_merge(merged[key], val)
            else:
                merged[key] = val
        return merged
