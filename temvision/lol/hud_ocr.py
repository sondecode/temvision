"""OCR-based HUD parser for League of Legends.

Reads on-screen HUD elements (gold, CS, KDA, level, spell cooldowns)
using Tesseract OCR on captured screen regions.

Each HUD element has a configurable screen region.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import cv2
import numpy as np

try:
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Default HUD regions (x, y, w, h) for 1920×1080 resolution.
# Users can override via config/lol.yaml → hud_regions.
DEFAULT_HUD_REGIONS: dict[str, tuple[int, int, int, int]] = {
    "gold": (870, 880, 120, 30),
    "cs": (1060, 880, 60, 25),
    "kda": (160, 880, 140, 25),
    "level": (30, 830, 30, 25),
    "game_time": (930, 0, 60, 25),
}


@dataclass
class HUDData:
    """Parsed values from the in-game HUD."""

    gold: Optional[int] = None
    cs: Optional[int] = None
    kills: Optional[int] = None
    deaths: Optional[int] = None
    assists: Optional[int] = None
    level: Optional[int] = None
    game_time_str: Optional[str] = None
    raw: dict[str, str] = field(default_factory=dict)


class HUDParser:
    """Extract HUD information from a full-screen capture via OCR."""

    def __init__(
        self,
        regions: Optional[dict[str, tuple[int, int, int, int]]] = None,
        tesseract_config: str = "--oem 3 --psm 7",
    ) -> None:
        self._regions = regions or dict(DEFAULT_HUD_REGIONS)
        self._tess_config = tesseract_config

    def parse(self, frame: np.ndarray) -> HUDData:
        """Run OCR on each HUD region and return parsed data.

        Args:
            frame: Full-screen capture as BGR numpy array.

        Returns:
            Parsed HUDData with whatever could be extracted.
        """
        if pytesseract is None:
            logger.warning("pytesseract not installed – HUD OCR disabled")
            return HUDData()

        data = HUDData()

        for name, region in self._regions.items():
            crop = self._crop(frame, region)
            if crop is None:
                continue
            processed = self._preprocess(crop)
            text = self._ocr(processed).strip()
            data.raw[name] = text
            self._assign(data, name, text)

        return data

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _crop(
        frame: np.ndarray, region: tuple[int, int, int, int]
    ) -> Optional[np.ndarray]:
        x, y, w, h = region
        fh, fw = frame.shape[:2]
        if x + w > fw or y + h > fh:
            return None
        return frame[y : y + h, x : x + w]

    @staticmethod
    def _preprocess(crop: np.ndarray) -> np.ndarray:
        """Convert to grayscale, threshold, and upscale for better OCR."""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        # Upscale 2× for small HUD text
        gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def _ocr(self, image: np.ndarray) -> str:
        try:
            return pytesseract.image_to_string(image, config=self._tess_config)
        except Exception as exc:
            logger.debug("OCR error: %s", exc)
            return ""

    @staticmethod
    def _assign(data: HUDData, name: str, text: str) -> None:
        """Map raw OCR text to the correct HUDData field."""
        digits = re.sub(r"[^\d]", "", text)

        if name == "gold" and digits:
            data.gold = int(digits)

        elif name == "cs" and digits:
            data.cs = int(digits)

        elif name == "level" and digits:
            data.level = int(digits)

        elif name == "game_time":
            data.game_time_str = text.strip()

        elif name == "kda":
            # Expect pattern like "3/1/5"
            match = re.search(r"(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", text)
            if match:
                data.kills = int(match.group(1))
                data.deaths = int(match.group(2))
                data.assists = int(match.group(3))
