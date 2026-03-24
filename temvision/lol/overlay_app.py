"""Main LoL Overlay Application orchestrator.

Coordinates game detection, data collection, suggestion engine,
event engine, feature engine, and overlay display into a unified
desktop overlay experience.

Uses a dual-speed update loop:
- Fast loop (0.25s): HP changes, combat detection, events
- Slow loop (1.0s): Gold diff, objectives, full suggestions
"""

import logging
import time
from typing import Optional

from temvision.lol.client_api import LiveClientAPI
from temvision.lol.event_engine import EventEngine, GameEvent
from temvision.lol.feature_engine import FeatureEngine, GameFeatures
from temvision.lol.game_detector import GameDetector
from temvision.lol.models import GameData
from temvision.lol.suggestion_engine import SuggestionEngine, Suggestion
from temvision.output.overlay import Overlay, OverlayMessage

logger = logging.getLogger(__name__)

# Default loop intervals
DEFAULT_FAST_INTERVAL = 0.25
DEFAULT_SLOW_INTERVAL = 1.0


class LoLOverlayApp:
    """Desktop overlay application for League of Legends.

    Orchestrates:
    1. Game detection (is LoL running?)
    2. Live data collection (Live Client API)
    3. Event detection (enemy missing, power spikes, gank risk)
    4. Feature extraction (gold_diff, hp_ratio, team_strength)
    5. Suggestion generation (rule-based engine)
    6. Overlay display (transparent overlay)

    Uses dual-speed loop for smooth overlay updates:
    - Fast loop (0.25s): HP changes, combat, events
    - Slow loop (1.0s): Gold diff, objectives, full analysis
    """

    def __init__(
        self,
        update_interval: float = 1.0,
        fast_interval: float = DEFAULT_FAST_INTERVAL,
        slow_interval: float = DEFAULT_SLOW_INTERVAL,
        use_gui: bool = False,
    ):
        self.update_interval = update_interval
        self.fast_interval = fast_interval
        self.slow_interval = slow_interval
        self.use_gui = use_gui

        # Core components
        self.detector = GameDetector()
        self.client_api = LiveClientAPI()
        self.suggestion_engine = SuggestionEngine()
        self.event_engine = EventEngine()
        self.feature_engine = FeatureEngine()
        self.overlay = Overlay(use_gui=use_gui)

        # State
        self._running = False
        self._game_active = False
        self._last_game_data: Optional[GameData] = None
        self._last_features: Optional[GameFeatures] = None
        self._last_events: list = []
        self._last_suggestions: list = []
        self._tick_count: int = 0
        self._last_slow_tick: float = 0.0

    def run(self):
        """Start the overlay application main loop.

        Uses dual-speed loop: fast ticks run every fast_interval,
        slow ticks run every slow_interval.
        """
        self._running = True
        self._last_slow_tick = 0.0
        logger.info("LoL Overlay started. Waiting for game...")
        self.overlay.show_text("LoL Overlay started. Waiting for game...")

        try:
            while self._running:
                self._tick()
                time.sleep(self.fast_interval)
        except KeyboardInterrupt:
            logger.info("Overlay stopped by user")
        finally:
            self.stop()

    def stop(self):
        """Stop the overlay application."""
        self._running = False
        self._game_active = False
        self._last_events = []
        self._last_suggestions = []
        self.event_engine.reset()
        self.client_api.close()
        logger.info("LoL Overlay stopped")

    def _tick(self):
        """Single update tick of the main loop.

        Every tick: check game state, run fast updates.
        On slow interval: run full analysis (suggestions, features).
        """
        now = time.monotonic()
        self._tick_count += 1

        game_running = self.client_api.is_game_running()

        if game_running and not self._game_active:
            self._on_game_start()
        elif not game_running and self._game_active:
            self._on_game_end()

        if self._game_active:
            raw_data = self.client_api.get_all_game_data()
            if raw_data is None:
                return

            game_data = self.client_api.parse_game_data(raw_data)
            self._last_game_data = game_data

            # Fast update: events (HP changes, combat, enemy missing)
            self._fast_update(game_data)

            # Slow update: full analysis (suggestions, features)
            if now - self._last_slow_tick >= self.slow_interval:
                self._slow_update(game_data)
                self._last_slow_tick = now

            # Display combined results
            self._display_overlay(game_data)

    def _fast_update(self, game_data: GameData):
        """Fast loop update: events and combat detection.

        Runs every fast_interval (default 0.25s).
        """
        self._last_events = self.event_engine.process(game_data)

    def _slow_update(self, game_data: GameData):
        """Slow loop update: full analysis.

        Runs every slow_interval (default 1.0s).
        """
        self._last_suggestions = self.suggestion_engine.analyze(game_data)
        self._last_features = self.feature_engine.extract(game_data)

    def _on_game_start(self):
        """Handle game start event."""
        self._game_active = True
        self._tick_count = 0
        self._last_slow_tick = 0.0
        self.event_engine.reset()
        logger.info("Game detected! Starting overlay...")
        self.overlay.show_text("🎮 Game detected! Loading data...", priority="high")

    def _on_game_end(self):
        """Handle game end event."""
        self._game_active = False
        self._last_game_data = None
        self._last_features = None
        self._last_events = []
        self._last_suggestions = []
        self.event_engine.reset()
        logger.info("Game ended. Waiting for next game...")
        self.overlay.show_text("Game ended. Waiting for next game...")

    def _display_overlay(self, game_data: GameData):
        """Combine events and suggestions into overlay display."""
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

        # Team strength (from feature engine)
        if self._last_features is not None:
            ts = self._last_features.team_strength
            ts_label = "Strong" if ts > 0.2 else "Weak" if ts < -0.2 else "Even"
            lines.append(f"🏆 Team: {ts_label} ({ts:+.2f})")

        lines.append("─" * 30)

        # Events (from fast loop - shown first as they are urgent)
        for e in self._last_events[:3]:
            lines.append(e.display_text)

        # Suggestions (from slow loop)
        for s in self._last_suggestions[:5]:
            lines.append(s.display_text)

        if not self._last_events and not self._last_suggestions:
            return

        text = "\n".join(lines)

        # Priority: events take precedence
        if self._last_events:
            priority = self._last_events[0].priority
        elif self._last_suggestions:
            priority = self._last_suggestions[0].priority
        else:
            priority = "normal"

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
        events = self.event_engine.process(game_data)
        features = self.feature_engine.extract(game_data)
        self._last_events = events
        self._last_features = features
        self._last_suggestions = suggestions
        return game_data, suggestions

    @property
    def last_game_data(self) -> Optional[GameData]:
        """Return the last fetched game data."""
        return self._last_game_data

    @property
    def last_features(self) -> Optional[GameFeatures]:
        """Return the last extracted features."""
        return self._last_features

    @property
    def last_events(self) -> list:
        """Return the last detected events."""
        return self._last_events
