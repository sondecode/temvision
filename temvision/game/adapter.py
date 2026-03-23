"""Base game adapter and adapter registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from temvision.game.state import GameState
from temvision.vision.engine import Detection


class GameAdapter(ABC):
    """Base class for game-specific adapters.

    A game adapter translates raw detections into game-specific state
    and provides game-specific logic.

    Subclasses must define `game_name` as a class attribute.
    """

    game_name: str = ""

    @abstractmethod
    def process_detections(
        self,
        detections: list[Detection],
        config: dict[str, Any],
    ) -> GameState:
        """Process detections into a game state.

        Args:
            detections: List of detections from VisionEngine.
            config: Game configuration dictionary.

        Returns:
            Updated GameState.
        """

    def get_detect_targets(self, config: dict[str, Any]) -> list[str]:
        """Get the list of detection targets from config."""
        vision_config = config.get("vision", {})
        return vision_config.get("detect", [])


class _AdapterRegistry:
    """Registry of game adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, type[GameAdapter]] = {}

    def register(self, adapter_class: type[GameAdapter]) -> type[GameAdapter]:
        """Register a game adapter class. Can be used as a decorator."""
        name = adapter_class.game_name
        if not name:
            raise ValueError(
                f"Adapter {adapter_class.__name__} must define 'game_name' class attribute"
            )
        self._adapters[name] = adapter_class
        return adapter_class

    def get(self, game: str) -> GameAdapter | None:
        """Get an adapter instance for a game."""
        adapter_class = self._adapters.get(game)
        if adapter_class is None:
            return None
        return adapter_class()

    def list_games(self) -> list[str]:
        """List registered game names."""
        return list(self._adapters.keys())


adapter_registry = _AdapterRegistry()
