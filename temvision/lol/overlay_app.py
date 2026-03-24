"""Main LoL Overlay Application orchestrator.

Coordinates game detection, data collection, suggestion engine,
and overlay display into a unified desktop overlay experience.
"""

import logging
import time
from typing import Optional

from temvision.lol.client_api import LiveClientAPI
from temvision.lol.game_detector import GameDetector
from temvision.lol.models import GameData
from temvision.lol.suggestion_engine import SuggestionEngine, Suggestion
from temvision.output.overlay import Overlay, OverlayMessage

logger = logging.getLogger(__name__)


class LoLOverlayApp:
    """Desktop overlay application for League of Legends.

    Orchestrates:
    1. Game detection (is LoL running?)
    2. Live data collection (Live Client API)
    3. Suggestion generation (rule-based engine)
    4. Overlay display (transparent overlay)
    """

    def __init__(
        self,
        update_interval: float = 1.0,
        use_gui: bool = False,
    ):
        self.update_interval = update_interval
        self.use_gui = use_gui

        # Core components
        self.detector = GameDetector()
        self.client_api = LiveClientAPI()
        self.suggestion_engine = SuggestionEngine()
        self.overlay = Overlay(use_gui=use_gui)

        # State
        self._running = False
        self._game_active = False
        self._last_game_data: Optional[GameData] = None

    def run(self):
        """Start the overlay application main loop.

        Continuously monitors for LoL game, collects data,
        generates suggestions, and updates the overlay.
        """
        self._running = True
        logger.info("LoL Overlay started. Waiting for game...")
        self.overlay.show_text("LoL Overlay started. Waiting for game...")

        try:
            while self._running:
                self._tick()
                time.sleep(self.update_interval)
        except KeyboardInterrupt:
            logger.info("Overlay stopped by user")
        finally:
            self.stop()

    def stop(self):
        """Stop the overlay application."""
        self._running = False
        self._game_active = False
        self.client_api.close()
        logger.info("LoL Overlay stopped")

    def _tick(self):
        """Single update tick of the main loop."""
        game_running = self.client_api.is_game_running()

        if game_running and not self._game_active:
            self._on_game_start()
        elif not game_running and self._game_active:
            self._on_game_end()

        if self._game_active:
            self._update_game_data()

    def _on_game_start(self):
        """Handle game start event."""
        self._game_active = True
        logger.info("Game detected! Starting overlay...")
        self.overlay.show_text("🎮 Game detected! Loading data...", priority="high")

    def _on_game_end(self):
        """Handle game end event."""
        self._game_active = False
        self._last_game_data = None
        logger.info("Game ended. Waiting for next game...")
        self.overlay.show_text("Game ended. Waiting for next game...")

    def _update_game_data(self):
        """Fetch latest game data, analyze, and update overlay."""
        raw_data = self.client_api.get_all_game_data()
        if raw_data is None:
            return

        game_data = self.client_api.parse_game_data(raw_data)
        self._last_game_data = game_data

        # Generate suggestions
        suggestions = self.suggestion_engine.analyze(game_data)

        # Display suggestions
        self._display_suggestions(game_data, suggestions)

    def _display_suggestions(
        self, game_data: GameData, suggestions: list
    ):
        """Format and display suggestions on the overlay."""
        if not suggestions:
            return

        # Build display text
        lines = []

        # Header with game time
        minutes = int(game_data.game_time // 60)
        seconds = int(game_data.game_time % 60)
        lines.append(f"⏱️ {minutes:02d}:{seconds:02d}")

        # Player stats summary
        if game_data.active_player:
            p = game_data.active_player
            lines.append(
                f"📊 {p.champion_name} | "
                f"KDA: {p.kda_string} | "
                f"CS: {p.creep_score} | "
                f"Lv.{p.level}"
            )

        # Gold/level diff
        gold_diff = game_data.gold_difference
        level_diff = game_data.level_difference
        if gold_diff != 0 or level_diff != 0:
            diff_sign = "+" if gold_diff >= 0 else ""
            lines.append(
                f"💎 Gold: {diff_sign}{gold_diff:.0f} | "
                f"Level: {diff_sign}{level_diff:.0f}"
            )

        lines.append("─" * 30)

        # Suggestions
        for s in suggestions[:5]:
            lines.append(s.display_text)

        text = "\n".join(lines)

        # Determine overall priority from top suggestion
        priority = suggestions[0].priority if suggestions else "normal"
        self.overlay.show(OverlayMessage(text=text, priority=priority))

    def process_tick(self, raw_data: dict) -> tuple:
        """Process a single tick with provided data (for testing).

        Args:
            raw_data: Raw game data dict.

        Returns:
            Tuple of (GameData, list[Suggestion]).
        """
        game_data = self.client_api.parse_game_data(raw_data)
        self._last_game_data = game_data
        suggestions = self.suggestion_engine.analyze(game_data)
        return game_data, suggestions

    @property
    def last_game_data(self) -> Optional[GameData]:
        """Return the last fetched game data."""
        return self._last_game_data
