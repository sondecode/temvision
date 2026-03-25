"""League of Legends game adapter."""

from __future__ import annotations

from typing import Any

from temvision.game.adapter import GameAdapter, adapter_registry
from temvision.game.state import GameState
from temvision.lol.client_api import LiveClientAPI
from temvision.lol.game_detector import GameDetector, GamePhase
from temvision.vision.engine import Detection


@adapter_registry.register
class LoLAdapter(GameAdapter):
    """Adapter for League of Legends."""

    game_name = "lol"

    def __init__(self) -> None:
        self._state = GameState(game="lol")
        self._detector = GameDetector()
        self._live_api = LiveClientAPI()

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

    def get_phase(self) -> GamePhase:
        """Return the current LoL session phase.

        - CLOSED       → League client not running
        - CLIENT_OPEN  → Client open (lobby / champion select)
        - IN_GAME      → Active match in progress
        """
        live_api_running = self._live_api.is_game_running()
        return self._detector.get_phase(live_api_running=live_api_running)
