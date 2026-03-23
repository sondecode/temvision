"""Overlay output for displaying decisions."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OverlayMessage:
    """A message to display on the overlay."""

    text: str
    priority: str = "normal"
    duration: float = 3.0


class Overlay:
    """Manages overlay display for game decisions.

    In headless/CLI mode, messages are logged to console.
    When PySide6 is available, a transparent overlay window is used.
    """

    def __init__(self, use_gui: bool = False) -> None:
        self._use_gui = use_gui
        self._message_history: list[OverlayMessage] = []
        self._gui_window = None

    def show(self, message: OverlayMessage) -> None:
        """Display a message on the overlay.

        Args:
            message: The OverlayMessage to display.
        """
        self._message_history.append(message)

        if self._use_gui:
            self._show_gui(message)
        else:
            self._show_console(message)

    def show_text(self, text: str, priority: str = "normal") -> None:
        """Convenience method to show a text message."""
        self.show(OverlayMessage(text=text, priority=priority))

    def get_history(self) -> list[OverlayMessage]:
        """Get the message history."""
        return list(self._message_history)

    def clear_history(self) -> None:
        """Clear the message history."""
        self._message_history.clear()

    def _show_console(self, message: OverlayMessage) -> None:
        """Display message in console."""
        priority_icons = {
            "critical": "🔴",
            "high": "🟠",
            "normal": "🟢",
            "low": "⚪",
        }
        icon = priority_icons.get(message.priority, "🟢")
        print(f"{icon} {message.text}")

    def _show_gui(self, message: OverlayMessage) -> None:
        """Display message in GUI overlay (requires PySide6)."""
        try:
            from temvision.output.gui_overlay import show_overlay_message

            show_overlay_message(message)
        except ImportError:
            logger.warning(
                "PySide6 not available, falling back to console overlay"
            )
            self._show_console(message)
