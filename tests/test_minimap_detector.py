"""Tests for minimap champion position detector."""

import pytest
import numpy as np

from temvision.lol.minimap_detector import (
    DEFAULT_MATCH_THRESHOLD,
    DEFAULT_MINIMAP_REGION,
    MAP_QUADRANTS,
    MinimapDetection,
    MinimapDetector,
    MinimapSnapshot,
)


class TestMinimapDetection:
    """Test MinimapDetection dataclass."""

    def test_defaults(self):
        d = MinimapDetection()
        assert d.champion_name == ""
        assert d.x == 0
        assert d.y == 0
        assert d.confidence == 0.0
        assert d.quadrant == ""

    def test_custom_values(self):
        d = MinimapDetection(
            champion_name="Zed", x=100, y=50, confidence=0.85, quadrant="top"
        )
        assert d.champion_name == "Zed"
        assert d.confidence == 0.85


class TestMinimapSnapshot:
    """Test MinimapSnapshot grouping and querying."""

    def _make_snapshot(self):
        return MinimapSnapshot(
            detections=[
                MinimapDetection(champion_name="Zed", x=30, y=30, confidence=0.9, quadrant="top"),
                MinimapDetection(champion_name="Jinx", x=200, y=200, confidence=0.8, quadrant="bot"),
                MinimapDetection(champion_name="Ahri", x=100, y=100, confidence=0.75, quadrant="mid"),
                MinimapDetection(champion_name="Lee Sin", x=50, y=50, confidence=0.7, quadrant="top"),
            ],
            timestamp=300.0,
        )

    def test_enemies_in_quadrant(self):
        snap = self._make_snapshot()
        top = snap.enemies_in_quadrant("top")
        assert len(top) == 2
        names = {d.champion_name for d in top}
        assert names == {"Zed", "Lee Sin"}

    def test_enemies_in_quadrant_empty(self):
        snap = self._make_snapshot()
        dragon = snap.enemies_in_quadrant("dragon")
        assert dragon == []

    def test_champion_position_found(self):
        snap = self._make_snapshot()
        pos = snap.champion_position("Ahri")
        assert pos is not None
        assert pos.quadrant == "mid"

    def test_champion_position_not_found(self):
        snap = self._make_snapshot()
        pos = snap.champion_position("Thresh")
        assert pos is None

    def test_overlay_lines(self):
        snap = self._make_snapshot()
        lines = snap.overlay_lines()
        assert len(lines) > 0
        joined = "\n".join(lines)
        assert "top" in joined
        assert "bot" in joined
        assert "mid" in joined

    def test_overlay_lines_empty_snapshot(self):
        snap = MinimapSnapshot()
        assert snap.overlay_lines() == []


class TestMinimapDetector:
    """Test MinimapDetector template matching logic."""

    def test_init_no_templates_dir(self, tmp_path):
        """Detector works with empty template directory."""
        detector = MinimapDetector(template_dir=str(tmp_path / "nonexistent"))
        assert detector.template_count == 0

    def test_detect_returns_empty_for_small_frame(self, tmp_path):
        """Detect on too-small frame returns empty snapshot."""
        detector = MinimapDetector(template_dir=str(tmp_path))
        small = np.zeros((100, 100, 3), dtype=np.uint8)
        snap = detector.detect(small, game_time=10.0)
        assert snap.timestamp == 10.0
        assert snap.detections == []

    def test_detect_full_frame_no_templates(self, tmp_path):
        """Full-size frame with no templates gives empty detections."""
        detector = MinimapDetector(template_dir=str(tmp_path))
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        snap = detector.detect(frame, game_time=60.0)
        assert snap.detections == []

    def test_crop_minimap_valid(self, tmp_path):
        detector = MinimapDetector(
            template_dir=str(tmp_path),
            minimap_region=(0, 0, 100, 100),
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        cropped = detector._crop_minimap(frame)
        assert cropped is not None
        assert cropped.shape == (100, 100, 3)

    def test_crop_minimap_out_of_bounds(self, tmp_path):
        detector = MinimapDetector(
            template_dir=str(tmp_path),
            minimap_region=(150, 150, 100, 100),
        )
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        cropped = detector._crop_minimap(frame)
        assert cropped is None

    def test_determine_quadrant_top(self, tmp_path):
        detector = MinimapDetector(template_dir=str(tmp_path))
        q = detector._determine_quadrant(25, 25, 270, 270)
        assert q == "top"

    def test_determine_quadrant_bot(self, tmp_path):
        detector = MinimapDetector(template_dir=str(tmp_path))
        q = detector._determine_quadrant(200, 200, 270, 270)
        assert q == "bot"

    def test_determine_quadrant_mid(self, tmp_path):
        detector = MinimapDetector(template_dir=str(tmp_path))
        # mid: (0.3-0.7, 0.3-0.7); must be outside top (0.0-0.5, 0.0-0.5)
        # 149/270 ≈ 0.55, 95/270 ≈ 0.35 → in mid but NOT in top
        q = detector._determine_quadrant(149, 95, 270, 270)
        assert q == "mid"

    def test_determine_quadrant_zero_size(self, tmp_path):
        detector = MinimapDetector(template_dir=str(tmp_path))
        q = detector._determine_quadrant(0, 0, 0, 0)
        assert q == "unknown"

    def test_constants(self):
        assert DEFAULT_MATCH_THRESHOLD == 0.70
        assert len(DEFAULT_MINIMAP_REGION) == 4
        assert "top" in MAP_QUADRANTS
        assert "bot" in MAP_QUADRANTS
        assert "mid" in MAP_QUADRANTS
        assert "dragon" in MAP_QUADRANTS
        assert "baron" in MAP_QUADRANTS
