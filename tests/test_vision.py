"""Tests for the vision engine."""

import numpy as np
import pytest

from temvision.vision.engine import Detection, VisionEngine


class TestVisionEngine:
    def test_detect_empty_frame(self):
        engine = VisionEngine()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = engine.detect(frame)
        assert detections == []

    def test_detect_none_frame(self):
        engine = VisionEngine()
        detections = engine.detect(None)
        assert detections == []

    def test_load_template(self):
        engine = VisionEngine()
        template = np.zeros((20, 20, 3), dtype=np.uint8)
        engine.load_template("test", template)
        assert "test" in engine._templates

    def test_detect_with_template(self):
        engine = VisionEngine()
        engine.set_threshold(0.9)

        # Create a template (white square on black bg)
        template = np.ones((20, 20, 3), dtype=np.uint8) * 255
        engine.load_template("target", template)

        # Create a frame containing the template
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        frame[30:50, 40:60] = 255  # Place white square

        detections = engine.detect(frame)
        assert len(detections) >= 1
        assert detections[0].label == "target"

    def test_detect_with_targets_filter(self):
        engine = VisionEngine()
        template1 = np.ones((10, 10, 3), dtype=np.uint8) * 255
        template2 = np.ones((10, 10, 3), dtype=np.uint8) * 128

        engine.load_template("a", template1)
        engine.load_template("b", template2)

        frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
        detections = engine.detect(frame, targets=["a"])
        labels = {d.label for d in detections}
        assert "b" not in labels

    def test_set_threshold(self):
        engine = VisionEngine()
        engine.set_threshold(0.95)
        assert engine._threshold == 0.95

    def test_template_larger_than_frame(self):
        engine = VisionEngine()
        template = np.zeros((200, 200, 3), dtype=np.uint8)
        engine.load_template("big", template)

        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = engine.detect(frame, targets=["big"])
        assert detections == []


class TestDetection:
    def test_detection_fields(self):
        det = Detection(label="enemy", confidence=0.95, bbox=(10, 20, 30, 40))
        assert det.label == "enemy"
        assert det.confidence == 0.95
        assert det.bbox == (10, 20, 30, 40)
        assert det.metadata == {}

    def test_detection_with_metadata(self):
        det = Detection(
            label="enemy",
            confidence=0.9,
            bbox=(0, 0, 10, 10),
            metadata={"type": "champion"},
        )
        assert det.metadata["type"] == "champion"


class TestIOU:
    def test_no_overlap(self):
        iou = VisionEngine._iou((0, 0, 10, 10), (20, 20, 10, 10))
        assert iou == 0.0

    def test_full_overlap(self):
        iou = VisionEngine._iou((0, 0, 10, 10), (0, 0, 10, 10))
        assert iou == 1.0

    def test_partial_overlap(self):
        iou = VisionEngine._iou((0, 0, 10, 10), (5, 5, 10, 10))
        assert 0 < iou < 1

    def test_zero_area(self):
        iou = VisionEngine._iou((0, 0, 0, 0), (0, 0, 0, 0))
        assert iou == 0.0
