"""GUI overlay using PySide6 (optional dependency)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from temvision.output.overlay import OverlayMessage


def show_overlay_message(message: OverlayMessage) -> None:
    """Show an overlay message using PySide6.

    This creates a transparent, always-on-top popup window.
    Requires PySide6 to be installed.
    """
    try:
        from PySide6.QtCore import QTimer, Qt
        from PySide6.QtWidgets import QApplication, QLabel

        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        priority_colors = {
            "critical": "#ff4444",
            "high": "#ff8800",
            "normal": "#44ff44",
            "low": "#cccccc",
        }
        color = priority_colors.get(message.priority, "#44ff44")

        label = QLabel(message.text)
        label.setStyleSheet(
            f"background-color: rgba(0, 0, 0, 200); "
            f"color: {color}; "
            f"font-size: 24px; "
            f"font-weight: bold; "
            f"padding: 16px 24px; "
            f"border-radius: 8px;"
        )
        label.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        label.adjustSize()
        label.show()

        # Auto-close after duration
        duration_ms = int(message.duration * 1000)
        QTimer.singleShot(duration_ms, label.close)

    except ImportError:
        print(f"[Overlay] {message.text}")
