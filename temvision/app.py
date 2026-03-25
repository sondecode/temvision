"""Main Temvision application."""

from __future__ import annotations

import logging
import time
from typing import Any

from temvision.capture.screen import ScreenCapture
from temvision.config.loader import ConfigLoader
from temvision.decision.engine import Decision, DecisionEngine
from temvision.game.adapter import GameAdapter, adapter_registry
from temvision.game.state import GameState
from temvision.lol.game_detector import GamePhase
from temvision.lol.pre_game import PreGameAnalyzer
from temvision.output.overlay import Overlay
from temvision.skills.loader import SkillLoader
from temvision.vision.engine import VisionEngine

# Register game adapters by importing them
import temvision.game.lol  # noqa: F401

logger = logging.getLogger(__name__)


class TemvisionApp:
    """Main application orchestrating the vision-decision pipeline.

    Pipeline:
        Screen Capture → Vision → Game Adapter → Game State
        → Skills → Decision Engine → Overlay / TTS
    """

    def __init__(
        self,
        game: str,
        config_dir: str = "config",
        skills_dir: str = "skills",
        use_gui: bool = False,
        use_llm: bool = False,
    ) -> None:
        self._game = game
        self._use_llm = use_llm

        # Load config
        self._config_loader = ConfigLoader(config_dir)
        self._config = self._config_loader.load(game)

        # Initialize components
        self._capture = ScreenCapture()
        self._vision = VisionEngine()
        alert_cooldown = float(self._config.get("alert_cooldown", 30.0))
        self._overlay = Overlay(use_gui=use_gui, cooldown=alert_cooldown)
        self._pre_game: PreGameAnalyzer | None = None
        self._pre_game_last_fetch: float = 0.0
        self._pre_game_fetch_interval: float = 5.0

        # Load game adapter
        self._adapter: GameAdapter | None = adapter_registry.get(game)
        if self._adapter is None:
            raise ValueError(f"No adapter found for game: {game}")

        if game == "lol":
            self._pre_game = PreGameAnalyzer()

        # Load skills
        self._skill_loader = SkillLoader(skills_dir)
        skills = self._skill_loader.load_all()

        # Initialize decision engine
        self._decision_engine = DecisionEngine()
        self._decision_engine.set_skills(skills)

        self._running = False
        self._loop_interval = 1.0  # seconds between frames

        logger.info("Temvision initialized for game: %s", game)
        logger.info("Loaded %d skills", len(skills))

    @property
    def config(self) -> dict[str, Any]:
        """Get the current game configuration."""
        return self._config

    @property
    def decision_engine(self) -> DecisionEngine:
        """Get the decision engine."""
        return self._decision_engine

    @property
    def overlay(self) -> Overlay:
        """Get the overlay output."""
        return self._overlay

    def run(self) -> None:
        """Start the main vision-decision loop."""
        self._running = True
        self._capture.start()

        logger.info("Starting Temvision main loop...")
        print(f"🔥 Temvision running for {self._game}")
        print("Press Ctrl+C to stop\n")

        try:
            while self._running:
                self._tick()
                time.sleep(self._loop_interval)
        except KeyboardInterrupt:
            print("\n🛑 Stopping Temvision...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the application."""
        self._running = False
        self._capture.stop()
        logger.info("Temvision stopped")

    def _tick(self) -> None:
        """Execute one iteration of the vision-decision pipeline."""
        # --- Phase check ---------------------------------------------------
        # If the adapter supports phase detection, gate the pipeline on it.
        phase = self._adapter.get_phase()
        if phase is not None:
            if phase == GamePhase.CLOSED:
                self._overlay.show_text(
                    f"⏳ Waiting for {self._game.upper()} to start...",
                    priority="normal",
                )
                return
            if phase == GamePhase.CLIENT_OPEN:
                if self._pre_game is not None:
                    self._maybe_show_pre_game()
                else:
                    self._overlay.show_text(
                        "🔵 League client detected – waiting for a match to begin...",
                        priority="normal",
                    )
                return
            # GamePhase.IN_GAME → fall through to the full pipeline
        # -------------------------------------------------------------------

        capture_config = self._config_loader.get_capture_config(self._config)
        vision_config = self._config_loader.get_vision_config(self._config)
        rules = self._config_loader.get_rules(self._config)

        # 1. Capture screen region
        region = capture_config.get("minimap_region")
        if region is None:
            return

        try:
            frame = self._capture.capture_region(region)
        except Exception as e:
            logger.error("Capture error: %s", e)
            return

        # 2. Vision: detect objects
        targets = vision_config.get("detect", [])
        detections = self._vision.detect(frame, targets)

        # 3. Game adapter: process detections → state
        state: GameState = self._adapter.process_detections(
            detections, self._config
        )

        # 4. Decision engine: evaluate rules + skills
        decisions = self._decision_engine.decide(
            state.to_dict(), rules, use_llm=self._use_llm
        )

        # 5. Output: show decisions on overlay
        for decision in decisions:
            self._overlay.show_text(decision.action, decision.priority)

    def process_frame(self, frame: Any) -> list[Decision]:
        """Process a single frame (for testing/API use).

        Args:
            frame: Input frame as numpy array.

        Returns:
            List of decisions.
        """
        vision_config = self._config_loader.get_vision_config(self._config)
        rules = self._config_loader.get_rules(self._config)

        targets = vision_config.get("detect", [])
        detections = self._vision.detect(frame, targets)

        state = self._adapter.process_detections(detections, self._config)

        return self._decision_engine.decide(
            state.to_dict(), rules, use_llm=self._use_llm
        )

    # ------------------------------------------------------------------
    # Pre-game (champ select) overlay for LoL
    def _maybe_show_pre_game(self) -> None:
        now = time.monotonic()
        if now - self._pre_game_last_fetch < self._pre_game_fetch_interval:
            return
        self._pre_game_last_fetch = now

        if self._pre_game is None:
            return

        info = self._pre_game.fetch()
        if info is None:
            self._overlay.show_text(
                "🔵 League client detected – waiting for a match to begin...",
                priority="normal",
            )
            return

        lines = info.overlay_lines()
        if not lines:
            self._overlay.show_text(
                "🔵 Champ select detected – loading data...",
                priority="normal",
            )
            return

        for line in lines:
            self._overlay.show_text(line, priority="normal")
