"""YAML configuration loader for game configs."""

from __future__ import annotations

import os
from typing import Any

import yaml


class ConfigLoader:
    """Loads and manages YAML-based game configuration."""

    def __init__(self, config_dir: str = "config") -> None:
        self.config_dir = config_dir
        self._configs: dict[str, dict[str, Any]] = {}

    def load(self, game: str) -> dict[str, Any]:
        """Load a game configuration by name.

        Args:
            game: The game identifier (e.g., 'lol', 'valorant').

        Returns:
            Parsed configuration dictionary.

        Raises:
            FileNotFoundError: If the config file does not exist.
        """
        if game in self._configs:
            return self._configs[game]

        config_path = os.path.join(self.config_dir, f"{game}.yaml")
        if not os.path.isfile(config_path):
            raise FileNotFoundError(
                f"Config file not found: {config_path}"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            config = {}

        self._configs[game] = config
        return config

    def get_capture_config(self, game_config: dict[str, Any]) -> dict[str, Any]:
        """Extract capture configuration from a game config."""
        return game_config.get("capture", {})

    def get_vision_config(self, game_config: dict[str, Any]) -> dict[str, Any]:
        """Extract vision configuration from a game config."""
        return game_config.get("vision", {})

    def get_rules(self, game_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract rules from a game config."""
        return game_config.get("rules", [])

    def get_mapping(self, game_config: dict[str, Any]) -> dict[str, str]:
        """Extract detection-to-state mapping from a game config."""
        return game_config.get("mapping", {})

    def list_games(self) -> list[str]:
        """List all available game configurations."""
        if not os.path.isdir(self.config_dir):
            return []
        return [
            f.replace(".yaml", "")
            for f in os.listdir(self.config_dir)
            if f.endswith(".yaml")
        ]
