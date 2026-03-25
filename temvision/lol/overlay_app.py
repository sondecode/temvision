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

from temvision.lol.build_recommender import BuildRecommender
from temvision.lol.client_api import LiveClientAPI
from temvision.lol.event_engine import EventEngine, GameEvent
from temvision.lol.feature_engine import FeatureEngine, GameFeatures
from temvision.lol.game_detector import GameDetector
from temvision.lol.hud_ocr import HUDParser, HUDData
from temvision.lol.match_history import MatchHistory
from temvision.lol.models import GameData
from temvision.lol.objective_tracker import ObjectiveTracker, ObjectiveTimers
from temvision.lol.post_game import PostGameAnalyzer
from temvision.lol.spell_tracker import SpellTracker
from temvision.lol.suggestion_engine import SuggestionEngine, Suggestion
from temvision.lol.threat_scorer import ThreatScorer
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
    5. Objective tracking (dragon, baron, herald timers)
    6. Suggestion generation (rule-based engine)
    7. Post-game analysis (performance score, MVP)
    8. Overlay display (transparent overlay)

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
        self.objective_tracker = ObjectiveTracker()
        self.post_game_analyzer = PostGameAnalyzer()
        self.spell_tracker = SpellTracker()
        self.threat_scorer = ThreatScorer(spell_tracker=self.spell_tracker)
        self.hud_parser = HUDParser()
        self.match_history = MatchHistory()
        self.build_recommender = BuildRecommender()
        self.overlay = Overlay(use_gui=use_gui)

        # State
        self._running = False
        self._game_active = False
        self._last_game_data: Optional[GameData] = None
        self._last_features: Optional[GameFeatures] = None
        self._last_events: list = []
        self._last_suggestions: list = []
        self._last_objective_timers: Optional[ObjectiveTimers] = None
        self._last_threats: list = []
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
        self._last_objective_timers = None
        self.event_engine.reset()
        self.objective_tracker.reset()
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

            # Register spells on first data tick
            if self._tick_count == 1:
                self._init_spell_tracker(game_data)

            # Fast update: events (HP changes, combat, enemy missing)
            self._fast_update(game_data)

            # Slow update: full analysis (suggestions, features)
            if now - self._last_slow_tick >= self.slow_interval:
                self._slow_update(game_data)
                self._last_slow_tick = now

            # Display combined results
            self._display_overlay(game_data)

    def _init_spell_tracker(self, game_data: GameData) -> None:
        """Register all players' summoner spells on first tick."""
        for player in game_data.all_players:
            spells = player.summoner_spells or []
            s1 = spells[0] if len(spells) > 0 else ""
            s2 = spells[1] if len(spells) > 1 else ""
            self.spell_tracker.register_player(
                champion_name=player.champion_name,
                summoner_name=player.summoner_name,
                spell1_name=s1,
                spell2_name=s2,
            )

    def _fast_update(self, game_data: GameData):
        """Fast loop update: events, combat detection, spell tracker.

        Runs every fast_interval (default 0.25s).
        """
        self._last_events = self.event_engine.process(game_data)
        self.spell_tracker.update(game_data.game_time)

    def _slow_update(self, game_data: GameData):
        """Slow loop update: full analysis.

        Runs every slow_interval (default 1.0s).
        """
        self._last_suggestions = self.suggestion_engine.analyze(game_data)
        self._last_features = self.feature_engine.extract(game_data)
        self._last_objective_timers = self.objective_tracker.process(game_data)
        self._last_threats = self.threat_scorer.score_all(
            game_data, game_data.game_time
        )

    def _on_game_start(self):
        """Handle game start event."""
        self._game_active = True
        self._tick_count = 0
        self._last_slow_tick = 0.0
        self.event_engine.reset()
        self.objective_tracker.reset()
        self.spell_tracker.reset()
        logger.info("Game detected! Starting overlay...")
        self.overlay.show_text("🎮 Game detected! Loading data...", priority="high")

    def _on_game_end(self):
        """Handle game end event."""
        # Run post-game analysis before clearing data
        if self._last_game_data is not None:
            post_game = self.post_game_analyzer.analyze(self._last_game_data)
            if post_game is not None:
                self._display_post_game(post_game)
                self.match_history.save(post_game)

        self._game_active = False
        self._last_game_data = None
        self._last_features = None
        self._last_events = []
        self._last_suggestions = []
        self._last_objective_timers = None
        self._last_threats = []
        self.event_engine.reset()
        self.objective_tracker.reset()
        self.spell_tracker.reset()
        logger.info("Game ended. Waiting for next game...")
        self.overlay.show_text("Game ended. Waiting for next game...")

    def _display_overlay(self, game_data: GameData):
        """Combine events, suggestions, team info, and objectives into overlay."""
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
            # Items summary
            if p.items:
                item_names = [i.get("displayName", "") for i in p.items[:6]]
                item_names = [n for n in item_names if n]
                if item_names:
                    lines.append(f"🎒 {', '.join(item_names)}")

        # Team info
        team_gold = game_data.team_total_gold
        enemy_gold = game_data.enemy_total_gold
        team_kills = game_data.team_total_kills
        enemy_kills = game_data.enemy_total_kills
        lines.append(
            f"👥 Team: {team_kills}K {team_gold:.0f}g | "
            f"Enemy: {enemy_kills}K {enemy_gold:.0f}g"
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

        # Objective timers
        if self._last_objective_timers is not None:
            obj = self._last_objective_timers
            obj_parts = []
            if not obj.dragon.alive and obj.dragon.next_spawn_time > 0:
                remaining = obj.dragon.remaining_time(game_data.game_time)
                if remaining > 0:
                    obj_parts.append(f"🐉 {remaining:.0f}s")
            if not obj.baron.alive and obj.baron.next_spawn_time > 0:
                remaining = obj.baron.remaining_time(game_data.game_time)
                if remaining > 0:
                    obj_parts.append(f"👾 {remaining:.0f}s")
            if obj.dragon_kills_ally > 0 or obj.dragon_kills_enemy > 0:
                obj_parts.append(
                    f"Dragons: {obj.dragon_kills_ally}v{obj.dragon_kills_enemy}"
                )
            if obj_parts:
                lines.append(" | ".join(obj_parts))

        # Threat scores
        if self._last_threats:
            lines.append("⚠️ Threats:")
            for t in self._last_threats[:3]:
                lines.append(t.overlay_line())

        # Enemy spell cooldowns
        enemy_champs = [e.champion_name for e in game_data.enemies]
        spell_lines = self.spell_tracker.get_enemy_lines(
            enemy_champs, game_data.game_time
        )
        if spell_lines:
            lines.append("🔮 Spell CDs:")
            lines.extend(spell_lines)

        # Enemy info (top 3 threats by level/kills)
        if game_data.enemies:
            enemies_sorted = sorted(
                game_data.enemies,
                key=lambda e: (e.kills + e.assists, e.level),
                reverse=True,
            )
            enemy_lines = []
            for e in enemies_sorted[:3]:
                status = "💀" if e.is_dead else "👁️"
                enemy_lines.append(
                    f"{status} {e.champion_name} "
                    f"{e.kda_string} Lv.{e.level}"
                )
            if enemy_lines:
                lines.append("─" * 30)
                lines.append("🔴 Enemies:")
                lines.extend(enemy_lines)

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

    def _display_post_game(self, post_game):
        """Display post-game analysis on the overlay."""
        lines = [
            "─" * 30,
            "📊 POST-GAME ANALYSIS",
            f"🏆 {post_game.player_champion} | "
            f"KDA: {post_game.kda_string} | "
            f"CS: {post_game.cs}",
            f"📈 Performance: {post_game.performance_score:.0f}/100 "
            f"(Grade: {post_game.grade})",
            f"{'🥇 MVP!' if post_game.mvp else ''}",
            "─" * 30,
        ]
        text = "\n".join(lines)
        self.overlay.show(OverlayMessage(text=text, priority="high"))

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
        objective_timers = self.objective_tracker.process(game_data)
        self._last_events = events
        self._last_features = features
        self._last_suggestions = suggestions
        self._last_objective_timers = objective_timers
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

    @property
    def last_objective_timers(self) -> Optional[ObjectiveTimers]:
        """Return the last objective timers."""
        return self._last_objective_timers
