"""League of Legends game adapter."""

from __future__ import annotations

from typing import Any

from temvision.game.adapter import GameAdapter, adapter_registry
from temvision.game.state import GameState
from temvision.vision.engine import Detection


@adapter_registry.register
class LoLAdapter(GameAdapter):
    """Adapter for League of Legends."""

    game_name = "lol"

    def __init__(self) -> None:
        self._state = GameState(game="lol")

    def process_detections(
        self,
        detections: list[Detection],
        config: dict[str, Any],
    ) -> GameState:
        """Process detections into LoL-specific game state."""
        mapping = config.get("mapping", {})
        detect_targets = self.get_detect_targets(config)

        self._state.update_from_detections(detections, mapping, detect_targets)

        return self._state
