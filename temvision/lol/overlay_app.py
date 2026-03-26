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
from dataclasses import dataclass
from typing import Optional

import yaml

from temvision.lol.build_recommender import BuildRecommender
from temvision.lol.champion_config import ChampionConfig
from temvision.lol.client_api import LiveClientAPI
from temvision.lol.data_sources import (
    LiveGameDataProvider,
    PostGameDataProvider,
    PreGameDataProvider,
)
from temvision.lol.event_engine import EventEngine, GameEvent
from temvision.lol.feature_engine import FeatureEngine, GameFeatures
from temvision.lol.game_detector import GameDetector
from temvision.lol.hud_ocr import HUDParser, HUDData
from temvision.lol.item_tracker import ItemTracker
from temvision.lol.match_history import MatchHistory
from temvision.lol.minimap_detector import MinimapDetector, MinimapSnapshot
from temvision.lol.models import GameData
from temvision.lol.objective_tracker import ObjectiveTracker, ObjectiveTimers
from temvision.lol.post_game import PostGameAnalyzer
from temvision.lol.pre_game import PreGameAnalyzer
from temvision.lol.report import ReportGenerator
from temvision.lol.spell_tracker import SpellTracker
from temvision.lol.suggestion_engine import SuggestionEngine, Suggestion
from temvision.lol.threat_scorer import ThreatScorer
from temvision.capture.screen import ScreenCapture
from temvision.output.overlay import Overlay, OverlayMessage

logger = logging.getLogger(__name__)

# Default loop intervals
DEFAULT_FAST_INTERVAL = 0.25
DEFAULT_SLOW_INTERVAL = 1.0
DEFAULT_OVERLAY_CONFIG = "config/lol.yaml"


@dataclass
class LoLFeatureFlags:
    live_api: bool = True
    pre_game: bool = True
    post_game: bool = True
    ocr_fallback: bool = True
    minimap_detector: bool = True


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
        config_path: str = DEFAULT_OVERLAY_CONFIG,
    ):
        self._config = self._load_overlay_config(config_path)
        config_overlay = self._config.get("overlay", {})

        self.update_interval = float(
            config_overlay.get("update_interval", update_interval)
        )
        self.fast_interval = float(
            config_overlay.get("fast_interval", fast_interval)
        )
        self.slow_interval = float(
            config_overlay.get("slow_interval", slow_interval)
        )
        self.use_gui = use_gui
        self.feature_flags = self._load_feature_flags(self._config)

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
        self.report_generator = ReportGenerator(match_history=self.match_history)
        self.item_tracker = ItemTracker()
        self.minimap_detector = MinimapDetector()
        self.screen_capture = ScreenCapture()
        self.champion_config = ChampionConfig()
        self.overlay = Overlay(use_gui=use_gui)
        self.pre_game_analyzer = PreGameAnalyzer()

        self.live_provider = LiveGameDataProvider(
            api=self.client_api,
            enabled=self.feature_flags.live_api,
        )
        self.pre_game_provider = PreGameDataProvider(
            analyzer=self.pre_game_analyzer,
            enabled=self.feature_flags.pre_game,
        )
        self.post_game_provider = PostGameDataProvider(
            analyzer=self.post_game_analyzer,
            history=self.match_history,
            enabled=self.feature_flags.post_game,
        )

        # State
        self._running = False
        self._game_active = False
        self._api_healthy = True
        self._api_fail_count = 0
        self._last_game_data: Optional[GameData] = None
        self._last_features: Optional[GameFeatures] = None
        self._last_events: list = []
        self._last_suggestions: list = []
        self._last_objective_timers: Optional[ObjectiveTimers] = None
        self._last_threats: list = []
        self._last_minimap: Optional[MinimapSnapshot] = None
        self._last_hud: Optional[HUDData] = None
        self._tick_count: int = 0
        self._last_slow_tick: float = 0.0

    def run(self):
        """Start the overlay application main loop.

        Uses dual-speed loop: fast ticks run every fast_interval,
        slow ticks run every slow_interval.
        """
        self._running = True
        self._last_slow_tick = 0.0
        self.screen_capture.start()
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

    @staticmethod
    def _load_overlay_config(config_path: str) -> dict:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            if not isinstance(cfg, dict):
                return {}
            return cfg
        except OSError:
            return {}

    @staticmethod
    def _load_feature_flags(config: dict) -> LoLFeatureFlags:
        raw = config.get("data_sources", {})
        return LoLFeatureFlags(
            live_api=bool(raw.get("live_api", True)),
            pre_game=bool(raw.get("pre_game", True)),
            post_game=bool(raw.get("post_game", True)),
            ocr_fallback=bool(raw.get("ocr_fallback", True)),
            minimap_detector=bool(raw.get("minimap_detector", True)),
        )

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
        self.screen_capture.stop()
        logger.info("LoL Overlay stopped")

    def _tick(self):
        """Single update tick of the main loop.

        Every tick: check game state, run fast updates.
        On slow interval: run full analysis (suggestions, features).
        """
        now = time.monotonic()
        self._tick_count += 1

        game_running = (
            self.client_api.is_game_running()
            if self.feature_flags.live_api
            else False
        )

        if game_running and not self._game_active:
            self._on_game_start()
        elif not game_running and self._game_active:
            self._on_game_end()

        if not self._game_active and self.pre_game_provider.is_enabled():
            info = self.pre_game_provider.fetch()
            if info is not None:
                lines = info.overlay_lines()
                if lines:
                    self.overlay.show(
                        OverlayMessage(
                            text="\n".join(lines[:4]), priority="normal"
                        )
                    )
                return

        if self._game_active:
            raw_data = self.live_provider.fetch()

            # --- API watchdog: degrade to OCR if API fails ---
            if raw_data is None:
                self._api_fail_count += 1
                if self._api_fail_count >= 3:
                    self._api_healthy = False
                    logger.debug("API unhealthy – falling back to OCR")
                if self.feature_flags.ocr_fallback:
                    self._run_ocr_fallback()
                return
            else:
                if not self._api_healthy:
                    logger.info("API recovered")
                self._api_healthy = True
                self._api_fail_count = 0

            game_data = self.client_api.parse_game_data(raw_data)
            self._last_game_data = game_data

            # Register spells on first data tick
            if self._tick_count == 1:
                self._init_spell_tracker(game_data)
                # Load per-champion config & tips
                if game_data.active_player:
                    champ = game_data.active_player.champion_name
                    self._champion_tips = self.champion_config.get_tips(champ)

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

        # Refresh item actives for all players
        for player in game_data.all_players:
            self.item_tracker.refresh_items(
                player.champion_name, player.items or []
            )
        self.item_tracker.update(game_data.game_time)

        # Minimap detection (screen capture)
        if self.feature_flags.minimap_detector:
            try:
                frame = self.screen_capture.capture_full()
                if frame is not None:
                    self._last_minimap = self.minimap_detector.detect(
                        frame, game_data.game_time
                    )
            except Exception as exc:
                logger.debug("Minimap capture failed: %s", exc)

    def _on_game_start(self):
        """Handle game start event."""
        self._game_active = True
        self._tick_count = 0
        self._last_slow_tick = 0.0
        self._api_healthy = True
        self._api_fail_count = 0
        self.event_engine.reset()
        self.objective_tracker.reset()
        self.spell_tracker.reset()
        self.item_tracker.reset()
        self._champion_tips: list[str] = []
        logger.info("Game detected! Starting overlay...")
        self.overlay.show_text("🎮 Game detected! Loading data...", priority="high")

    def _on_game_end(self):
        """Handle game end event."""
        # Run post-game analysis before clearing data
        if self._last_game_data is not None:
            post_game = self.post_game_provider.analyze(self._last_game_data)
            if post_game is not None:
                self._display_post_game(post_game)
                self.post_game_provider.persist(post_game)
                # Generate improvement report
                report = self.report_generator.generate(post_game)
                report_lines = report.overlay_lines()
                self.overlay.show(OverlayMessage(
                    text="\n".join(report_lines), priority="normal"
                ))

        self._game_active = False
        self._last_game_data = None
        self._last_features = None
        self._last_events = []
        self._last_suggestions = []
        self._last_objective_timers = None
        self._last_threats = []
        self._last_minimap = None
        self._last_hud = None
        self.event_engine.reset()
        self.objective_tracker.reset()
        self.spell_tracker.reset()
        self.item_tracker.reset()
        logger.info("Game ended. Waiting for next game...")
        self.overlay.show_text("Game ended. Waiting for next game...")

    def _run_ocr_fallback(self) -> None:
        """Degrade to OCR-only when Live Client API is unavailable.

        Captures full screen and uses HUDParser to read gold/CS/KDA.
        """
        try:
            frame = self.screen_capture.capture_full()
            if frame is None:
                return
        except Exception as exc:
            logger.debug("OCR fallback capture failed: %s", exc)
            return

        hud = self.hud_parser.parse(frame)
        self._last_hud = hud

        lines: list[str] = ["⏱️ OCR Mode (API unavailable)"]
        if hud.gold is not None:
            lines.append(f"💰 Gold: {hud.gold}")
        if hud.cs is not None:
            lines.append(f"🗡️  CS: {hud.cs}")
        if hud.kills is not None and hud.deaths is not None and hud.assists is not None:
            lines.append(f"📊 KDA: {hud.kills}/{hud.deaths}/{hud.assists}")
        if hud.level is not None:
            lines.append(f"⬆️  Level: {hud.level}")
        if hud.game_time_str:
            lines.append(f"⏱️ {hud.game_time_str}")

        # Minimap detection still works in OCR mode
        if self.feature_flags.minimap_detector:
            minimap = self.minimap_detector.detect(frame)
            if minimap.detections:
                lines.append("🗺️  Minimap:")
                lines.extend(minimap.overlay_lines())

        if len(lines) > 1:
            self.overlay.show(OverlayMessage(
                text="\n".join(lines), priority="normal"
            ))

    def _display_overlay(self, game_data: GameData):
        """Combine all data into a structured lane-panel overlay.

        Layout:
          ┌ HEADER: time, player stats, team summary ┐
          ├ OBJECTIVES: dragon/baron timers            │
          ├ LANE PANELS: per-lane ally vs enemy        │
          ├ THREATS & CDs: spell/item cooldowns        │
          ├ MINIMAP: detected positions                │
          ├ EVENTS (urgent): from fast loop            │
          └ SUGGESTIONS: from slow loop               ┘
        """
        lines: list[str] = []

        # ── HEADER ──────────────────────────────────────
        minutes = int(game_data.game_time // 60)
        seconds = int(game_data.game_time % 60)

        if game_data.active_player:
            p = game_data.active_player
            lines.append(
                f"⏱️ {minutes:02d}:{seconds:02d}  "
                f"📊 {p.champion_name}  "
                f"KDA {p.kda_string}  "
                f"CS {p.creep_score}  "
                f"Lv.{p.level}"
            )
        else:
            lines.append(f"⏱️ {minutes:02d}:{seconds:02d}")

        # Team gold/kills
        tdiff = game_data.team_gold_diff
        diff_icon = "🔺" if tdiff > 0 else "🔻" if tdiff < 0 else "⚖️"
        lines.append(
            f"{diff_icon} Team {game_data.team_total_kills}K "
            f"{game_data.team_total_gold:.0f}g  vs  "
            f"Enemy {game_data.enemy_total_kills}K "
            f"{game_data.enemy_total_gold:.0f}g"
        )

        # Team strength
        if self._last_features is not None:
            ts = self._last_features.team_strength
            ts_label = "Strong" if ts > 0.2 else "Weak" if ts < -0.2 else "Even"
            lines[-1] += f"  ({ts_label})"

        # ── OBJECTIVES ──────────────────────────────────
        if self._last_objective_timers is not None:
            obj = self._last_objective_timers
            obj_parts: list[str] = []
            if not obj.dragon.alive and obj.dragon.next_spawn_time > 0:
                rem = obj.dragon.remaining_time(game_data.game_time)
                if rem > 0:
                    obj_parts.append(f"🐉 {rem:.0f}s")
            if not obj.baron.alive and obj.baron.next_spawn_time > 0:
                rem = obj.baron.remaining_time(game_data.game_time)
                if rem > 0:
                    obj_parts.append(f"👾 {rem:.0f}s")
            if obj.dragon_kills_ally > 0 or obj.dragon_kills_enemy > 0:
                obj_parts.append(
                    f"Drk {obj.dragon_kills_ally}v{obj.dragon_kills_enemy}"
                )
            if obj_parts:
                lines.append(" | ".join(obj_parts))

        # ── LANE PANELS ─────────────────────────────────
        # Build a lane map: position → (ally, enemy)
        lane_map: dict[str, dict[str, list]] = {}
        if game_data.active_player:
            pos = game_data.active_player.position or "?"
            lane_map.setdefault(pos, {"ally": [], "enemy": []})
            lane_map[pos]["ally"].append(game_data.active_player)
        for a in game_data.allies:
            pos = a.position or "?"
            lane_map.setdefault(pos, {"ally": [], "enemy": []})
            lane_map[pos]["ally"].append(a)
        for e in game_data.enemies:
            pos = e.position or "?"
            lane_map.setdefault(pos, {"ally": [], "enemy": []})
            lane_map[pos]["enemy"].append(e)

        if lane_map:
            lines.append("─── Lane Panels ───")
            for lane, sides in sorted(lane_map.items()):
                parts: list[str] = []
                for a in sides["ally"]:
                    parts.append(
                        f"🟢{a.champion_name} {a.kda_string}"
                    )
                for e in sides["enemy"]:
                    status = "💀" if e.is_dead else "🔴"
                    parts.append(
                        f"{status}{e.champion_name} {e.kda_string}"
                    )
                lines.append(f"  {lane.upper()}: {' vs '.join(parts)}")

        # ── THREATS ─────────────────────────────────────
        if self._last_threats:
            top_threats = [
                t for t in self._last_threats[:3]
                if t.label in ("High", "Extreme")
            ]
            if top_threats:
                lines.append("⚠️ " + " | ".join(
                    t.overlay_line() for t in top_threats
                ))

        # ── SPELL & ITEM CDs ───────────────────────────
        enemy_champs = [e.champion_name for e in game_data.enemies]
        spell_lines = self.spell_tracker.get_enemy_lines(
            enemy_champs, game_data.game_time
        )
        # Only show spells on cooldown (compact)
        cd_entries: list[str] = []
        for sl in spell_lines:
            if "⏳" in sl:
                cd_entries.append(sl)
        item_lines = self.item_tracker.get_enemy_lines(
            enemy_champs, game_data.game_time
        )
        cd_entries.extend(item_lines)
        if cd_entries:
            lines.append("🔮 CDs: " + " | ".join(cd_entries[:5]))

        # ── MINIMAP ─────────────────────────────────────
        if self._last_minimap and self._last_minimap.detections:
            lines.append("🗺️  " + " ".join(
                f"{d.champion_name}@{d.quadrant}"
                for d in self._last_minimap.detections[:5]
            ))

        # ── EVENTS (urgent) ─────────────────────────────
        for ev in self._last_events[:3]:
            lines.append(ev.display_text)

        # ── SUGGESTIONS ─────────────────────────────────
        for s in self._last_suggestions[:3]:
            lines.append(s.display_text)

        # ── CHAMPION TIPS ───────────────────────────────
        if self._champion_tips:
            lines.append(f"💡 {self._champion_tips[0]}")

        if not self._last_events and not self._last_suggestions:
            return

        text = "\n".join(lines)

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
