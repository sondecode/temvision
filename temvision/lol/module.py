"""Unified League of Legends module entry.

This module is the integration point for LoL-specific runtime features:
- game-phase detection
- live client ingestion
- pre-game / post-game pipelines
- tactical suggestion and event overlays

It wraps the existing LoL overlay runtime so the main application can keep
one entrypoint (`python main.py --game=lol`) while remaining extensible for
future game modules (TFT, Poker, etc.).
"""

from __future__ import annotations

from typing import Optional

from temvision.lol.models import GameData
from temvision.lol.overlay_app import LoLOverlayApp


class LoLModule:
    """Unified LoL runtime module used by the main app."""

    def __init__(self, use_gui: bool = False, config_path: str = "config/lol.yaml"):
        self._runtime = LoLOverlayApp(use_gui=use_gui, config_path=config_path)

    def run(self) -> None:
        self._runtime.run()

    def stop(self) -> None:
        self._runtime.stop()

    def process_tick(self, raw_data: dict) -> tuple[GameData, list]:
        return self._runtime.process_tick(raw_data)

    @property
    def runtime(self) -> LoLOverlayApp:
        return self._runtime
