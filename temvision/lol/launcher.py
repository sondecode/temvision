"""Desktop launcher for Temvision LoL overlay.

Provides:
- Auto-start: detect when League of Legends opens and launch overlay
- Hotkey support: toggle overlay, compact/detail mode
- System tray integration (optional, when pystray is available)
"""

from __future__ import annotations

import logging
import os
import signal
import sys
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Try optional dependencies
try:
    import keyboard  # type: ignore[import-untyped]
    _HAS_KEYBOARD = True
except ImportError:
    _HAS_KEYBOARD = False

try:
    import pystray  # type: ignore[import-untyped]
    from PIL import Image  # type: ignore[import-untyped]
    _HAS_TRAY = True
except ImportError:
    _HAS_TRAY = False


class HotkeyManager:
    """Register and manage global hotkeys.

    Requires the ``keyboard`` package (pip install keyboard).
    Falls back to no-op if not available.
    """

    def __init__(self) -> None:
        self._bindings: dict[str, callable] = {}
        self._active = False

    def register(self, key_combo: str, callback: callable) -> None:
        """Register a hotkey binding (e.g. 'ctrl+shift+t')."""
        self._bindings[key_combo] = callback

    def start(self) -> None:
        if not _HAS_KEYBOARD:
            logger.info("keyboard package not installed – hotkeys disabled")
            return
        for combo, cb in self._bindings.items():
            keyboard.add_hotkey(combo, cb)
            logger.info("Hotkey registered: %s", combo)
        self._active = True

    def stop(self) -> None:
        if self._active and _HAS_KEYBOARD:
            keyboard.unhook_all()
            self._active = False


class Launcher:
    """Desktop launcher that auto-detects League and runs the overlay.

    Usage::

        launcher = Launcher()
        launcher.run()  # blocks until Ctrl+C
    """

    def __init__(
        self,
        poll_interval: float = 5.0,
        use_gui: bool = False,
        hotkey_toggle: str = "ctrl+shift+o",
        hotkey_quit: str = "ctrl+shift+q",
    ) -> None:
        self._poll_interval = poll_interval
        self._use_gui = use_gui
        self._hotkey_toggle = hotkey_toggle
        self._hotkey_quit = hotkey_quit
        self._running = False
        self._overlay_running = False
        self._overlay_thread: Optional[threading.Thread] = None
        self._hotkeys = HotkeyManager()

    def run(self) -> None:
        """Main launcher loop: poll for League, start overlay when found."""
        self._running = True
        self._setup_hotkeys()
        self._hotkeys.start()

        logger.info("Temvision Launcher started. Watching for League of Legends...")
        print("🚀 Temvision Launcher active")
        print(f"   Toggle overlay:  {self._hotkey_toggle}")
        print(f"   Quit:            {self._hotkey_quit}")
        print("   Press Ctrl+C to stop\n")

        # Handle SIGINT gracefully
        signal.signal(signal.SIGINT, lambda *_: self.stop())

        try:
            while self._running:
                if self._should_start_overlay():
                    self._start_overlay()
                time.sleep(self._poll_interval)
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        self._stop_overlay()
        self._hotkeys.stop()
        logger.info("Launcher stopped")

    # ------------------------------------------------------------------

    def _setup_hotkeys(self) -> None:
        self._hotkeys.register(self._hotkey_toggle, self._toggle_overlay)
        self._hotkeys.register(self._hotkey_quit, self.stop)

    def _should_start_overlay(self) -> bool:
        """Check if League is running and overlay is not yet started."""
        if self._overlay_running:
            return False
        from temvision.lol.game_detector import GameDetector
        return GameDetector().is_game_running()

    def _start_overlay(self) -> None:
        if self._overlay_running:
            return
        logger.info("League detected – starting overlay in background thread")
        self._overlay_running = True

        def _run_overlay() -> None:
            try:
                from temvision.lol.overlay_app import LoLOverlayApp
                app = LoLOverlayApp(use_gui=self._use_gui)
                app.run()
            except Exception as exc:
                logger.error("Overlay crashed: %s", exc)
            finally:
                self._overlay_running = False

        self._overlay_thread = threading.Thread(
            target=_run_overlay, daemon=True, name="overlay"
        )
        self._overlay_thread.start()

    def _stop_overlay(self) -> None:
        self._overlay_running = False
        if self._overlay_thread and self._overlay_thread.is_alive():
            self._overlay_thread.join(timeout=3.0)

    def _toggle_overlay(self) -> None:
        if self._overlay_running:
            logger.info("Hotkey: stopping overlay")
            self._stop_overlay()
        else:
            logger.info("Hotkey: starting overlay")
            self._start_overlay()


def main() -> None:
    """CLI entry point for the launcher."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Temvision Desktop Launcher — auto-start LoL overlay"
    )
    parser.add_argument(
        "--gui", action="store_true", help="Enable GUI overlay"
    )
    parser.add_argument(
        "--poll", type=float, default=5.0,
        help="Seconds between League detection polls"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    launcher = Launcher(
        poll_interval=args.poll,
        use_gui=args.gui,
    )
    launcher.run()


if __name__ == "__main__":
    main()
