"""Screen capture using mss."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    import mss
    import mss.tools

    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False


class ScreenCapture:
    """Captures screen regions using the mss library."""

    def __init__(self) -> None:
        self._sct: Any = None

    def start(self) -> None:
        """Initialize the screen capture context."""
        if not _MSS_AVAILABLE:
            raise RuntimeError(
                "mss is not installed. Install it with: pip install mss"
            )
        self._sct = mss.mss()

    def stop(self) -> None:
        """Release screen capture resources."""
        if self._sct is not None:
            self._sct.close()
            self._sct = None

    def capture_region(self, region: list[int]) -> np.ndarray:
        """Capture a specific screen region.

        Args:
            region: [x, y, width, height] of the region to capture.

        Returns:
            Captured image as a numpy array (BGR format).
        """
        if self._sct is None:
            raise RuntimeError("ScreenCapture not started. Call start() first.")

        x, y, w, h = region
        monitor = {"left": x, "top": y, "width": w, "height": h}
        screenshot = self._sct.grab(monitor)

        # Convert to numpy array (BGRA -> BGR)
        img = np.array(screenshot)
        return img[:, :, :3]

    def capture_full(self) -> np.ndarray:
        """Capture the full primary screen.

        Returns:
            Full screen image as a numpy array (BGR format).
        """
        if self._sct is None:
            raise RuntimeError("ScreenCapture not started. Call start() first.")

        monitor = self._sct.monitors[1]  # Primary monitor
        screenshot = self._sct.grab(monitor)
        img = np.array(screenshot)
        return img[:, :, :3]
