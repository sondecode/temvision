"""Tests for HUD OCR parser."""

import pytest
import numpy as np

from temvision.lol.hud_ocr import HUDParser, HUDData, DEFAULT_HUD_REGIONS


class TestHUDData:
    """Test HUDData dataclass."""

    def test_defaults(self):
        d = HUDData()
        assert d.gold is None
        assert d.cs is None
        assert d.kills is None
        assert d.deaths is None
        assert d.assists is None
        assert d.level is None
        assert d.game_time_str is None
        assert d.raw == {}


class TestHUDParser:
    """Test HUD parser logic (mocked OCR)."""

    def test_init_default_regions(self):
        parser = HUDParser()
        assert parser._regions == DEFAULT_HUD_REGIONS

    def test_init_custom_regions(self):
        regions = {"gold": (0, 0, 10, 10)}
        parser = HUDParser(regions=regions)
        assert parser._regions == regions

    def test_crop_valid(self):
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        crop = HUDParser._crop(frame, (870, 880, 120, 30))
        assert crop is not None
        assert crop.shape == (30, 120, 3)

    def test_crop_out_of_bounds(self):
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        crop = HUDParser._crop(frame, (90, 0, 20, 10))
        assert crop is None

    def test_preprocess(self):
        crop = np.zeros((25, 60, 3), dtype=np.uint8)
        result = HUDParser._preprocess(crop)
        # Should be 2x upscaled grayscale
        assert result.shape == (50, 120)

    def test_assign_gold(self):
        d = HUDData()
        HUDParser._assign(d, "gold", "3450")
        assert d.gold == 3450

    def test_assign_cs(self):
        d = HUDData()
        HUDParser._assign(d, "cs", "157")
        assert d.cs == 157

    def test_assign_level(self):
        d = HUDData()
        HUDParser._assign(d, "level", "11")
        assert d.level == 11

    def test_assign_noisy_text(self):
        d = HUDData()
        HUDParser._assign(d, "gold", "3,450g")
        assert d.gold == 3450

    def test_assign_empty(self):
        d = HUDData()
        HUDParser._assign(d, "gold", "")
        assert d.gold is None

    def test_parse_no_pytesseract(self, monkeypatch):
        """Parse returns empty data when pytesseract is not installed."""
        import temvision.lol.hud_ocr as hud_mod
        monkeypatch.setattr(hud_mod, "pytesseract", None)
        parser = HUDParser()
        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
        result = parser.parse(frame)
        assert result.gold is None
        assert result.cs is None
