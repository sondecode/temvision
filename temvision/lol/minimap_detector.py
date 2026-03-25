"""Minimap champion position detector using template matching.

Detects enemy champion icon positions on the minimap to track
enemy movement, missing champions, and potential gank paths.
Uses OpenCV template matching with pre-loaded champion icon templates.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "data", "minimap_icons")

# Minimap bounds (x, y, w, h) on a 1920×1080 screen
DEFAULT_MINIMAP_REGION = (1630, 805, 270, 270)

# Match threshold for template matching (0-1)
DEFAULT_MATCH_THRESHOLD = 0.70

# Minimap coordinate ranges (fraction of minimap size)
# Used to convert pixel position to game-map quadrant
MAP_QUADRANTS = {
    "top": (0.0, 0.0, 0.5, 0.5),      # top-left
    "mid": (0.3, 0.3, 0.4, 0.4),       # center
    "bot": (0.5, 0.5, 0.5, 0.5),       # bottom-right
    "top_jungle": (0.0, 0.25, 0.35, 0.35),
    "bot_jungle": (0.35, 0.4, 0.35, 0.35),
    "dragon": (0.55, 0.45, 0.15, 0.15),
    "baron": (0.25, 0.2, 0.15, 0.15),
}


@dataclass
class MinimapDetection:
    """A single champion detection on the minimap."""

    champion_name: str = ""
    x: int = 0  # pixel x in minimap crop
    y: int = 0  # pixel y in minimap crop
    confidence: float = 0.0
    quadrant: str = ""  # top/mid/bot/jungle/dragon/baron


@dataclass
class MinimapSnapshot:
    """All detected champion positions in one frame."""

    detections: list[MinimapDetection] = field(default_factory=list)
    timestamp: float = 0.0

    def enemies_in_quadrant(self, quadrant: str) -> list[MinimapDetection]:
        return [d for d in self.detections if d.quadrant == quadrant]

    def champion_position(self, name: str) -> Optional[MinimapDetection]:
        for d in self.detections:
            if d.champion_name == name:
                return d
        return None

    def overlay_lines(self) -> list[str]:
        if not self.detections:
            return []
        lines: list[str] = []
        by_quad: dict[str, list[str]] = {}
        for d in self.detections:
            q = d.quadrant or "unknown"
            by_quad.setdefault(q, []).append(d.champion_name)
        for quad, champs in sorted(by_quad.items()):
            lines.append(f"  {quad}: {', '.join(champs)}")
        return lines


class MinimapDetector:
    """Detect champion icons on the minimap via template matching.

    Templates are small 24×24 or 32×32 champion icon images stored
    in ``data/minimap_icons/<champion_name>.png``.
    """

    def __init__(
        self,
        template_dir: str = _TEMPLATE_DIR,
        threshold: float = DEFAULT_MATCH_THRESHOLD,
        minimap_region: tuple[int, int, int, int] = DEFAULT_MINIMAP_REGION,
    ) -> None:
        self._template_dir = template_dir
        self._threshold = threshold
        self._minimap_region = minimap_region
        self._templates: dict[str, np.ndarray] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        if not os.path.isdir(self._template_dir):
            logger.debug(
                "Minimap template directory not found: %s", self._template_dir
            )
            return
        for fname in os.listdir(self._template_dir):
            if not fname.endswith(".png"):
                continue
            name = os.path.splitext(fname)[0]
            path = os.path.join(self._template_dir, fname)
            img = cv2.imread(path, cv2.IMREAD_COLOR)
            if img is not None:
                self._templates[name] = img
        logger.info("Loaded %d minimap icon templates", len(self._templates))

    def detect(
        self, frame: np.ndarray, game_time: float = 0.0
    ) -> MinimapSnapshot:
        """Detect champion icons in a full-screen frame.

        Args:
            frame: Full-screen capture (BGR numpy array).
            game_time: Current game time for timestamping.

        Returns:
            MinimapSnapshot with detected positions.
        """
        minimap = self._crop_minimap(frame)
        if minimap is None:
            return MinimapSnapshot(timestamp=game_time)

        snapshot = MinimapSnapshot(timestamp=game_time)

        for champ_name, template in self._templates.items():
            loc = self._match_template(minimap, template)
            if loc is not None:
                x, y, conf = loc
                quadrant = self._determine_quadrant(
                    x, y, minimap.shape[1], minimap.shape[0]
                )
                snapshot.detections.append(
                    MinimapDetection(
                        champion_name=champ_name,
                        x=x,
                        y=y,
                        confidence=conf,
                        quadrant=quadrant,
                    )
                )

        return snapshot

    @property
    def template_count(self) -> int:
        return len(self._templates)

    # ------------------------------------------------------------------

    def _crop_minimap(self, frame: np.ndarray) -> Optional[np.ndarray]:
        x, y, w, h = self._minimap_region
        fh, fw = frame.shape[:2]
        if x + w > fw or y + h > fh:
            return None
        return frame[y : y + h, x : x + w]

    def _match_template(
        self, minimap: np.ndarray, template: np.ndarray
    ) -> Optional[tuple[int, int, float]]:
        """Run cv2.matchTemplate and return best match above threshold."""
        th, tw = template.shape[:2]
        mh, mw = minimap.shape[:2]
        if tw > mw or th > mh:
            return None

        result = cv2.matchTemplate(
            minimap, template, cv2.TM_CCOEFF_NORMED
        )
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= self._threshold:
            cx = max_loc[0] + tw // 2
            cy = max_loc[1] + th // 2
            return (cx, cy, float(max_val))
        return None

    @staticmethod
    def _determine_quadrant(
        x: int, y: int, map_w: int, map_h: int
    ) -> str:
        """Map pixel position to a game-map quadrant."""
        if map_w == 0 or map_h == 0:
            return "unknown"
        fx = x / map_w
        fy = y / map_h

        for name, (qx, qy, qw, qh) in MAP_QUADRANTS.items():
            if qx <= fx <= qx + qw and qy <= fy <= qy + qh:
                return name

        # Fallback by half
        if fx < 0.5 and fy < 0.5:
            return "top"
        if fx > 0.5 and fy > 0.5:
            return "bot"
        return "mid"
