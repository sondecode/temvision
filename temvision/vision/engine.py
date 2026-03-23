"""Vision engine for object detection and OCR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np


@dataclass
class Detection:
    """Represents a detected object in a frame."""

    label: str
    confidence: float
    bbox: tuple[int, int, int, int]  # x, y, w, h
    metadata: dict[str, Any] = field(default_factory=dict)


class VisionEngine:
    """Processes frames to detect game objects using OpenCV.

    Uses template matching for object detection. Can be extended
    with YOLO or other models for more advanced detection.
    """

    def __init__(self) -> None:
        self._templates: dict[str, np.ndarray] = {}
        self._threshold: float = 0.7

    def set_threshold(self, threshold: float) -> None:
        """Set the detection confidence threshold."""
        self._threshold = threshold

    def load_template(self, label: str, template_image: np.ndarray) -> None:
        """Load a template image for template matching.

        Args:
            label: Label name for this template.
            template_image: Template image as numpy array (BGR).
        """
        if template_image is not None and template_image.size > 0:
            gray = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
            self._templates[label] = gray

    def detect(
        self, frame: np.ndarray, targets: list[str] | None = None
    ) -> list[Detection]:
        """Run detection on a frame.

        Args:
            frame: Input frame as numpy array (BGR).
            targets: Optional list of target labels to detect.
                     If None, all loaded templates are used.

        Returns:
            List of Detection objects found in the frame.
        """
        if frame is None or frame.size == 0:
            return []

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections: list[Detection] = []

        templates_to_check = self._templates
        if targets is not None:
            templates_to_check = {
                k: v for k, v in self._templates.items() if k in targets
            }

        for label, template in templates_to_check.items():
            th, tw = template.shape[:2]

            if gray_frame.shape[0] < th or gray_frame.shape[1] < tw:
                continue

            result = cv2.matchTemplate(
                gray_frame, template, cv2.TM_CCOEFF_NORMED
            )
            locations = np.where(result >= self._threshold)

            for pt_y, pt_x in zip(*locations):
                confidence = float(result[pt_y, pt_x])
                detections.append(
                    Detection(
                        label=label,
                        confidence=confidence,
                        bbox=(int(pt_x), int(pt_y), tw, th),
                    )
                )

        return self._non_max_suppression(detections)

    def _non_max_suppression(
        self, detections: list[Detection], iou_threshold: float = 0.5
    ) -> list[Detection]:
        """Apply non-maximum suppression to remove overlapping detections."""
        if not detections:
            return []

        # Sort by confidence descending
        detections.sort(key=lambda d: d.confidence, reverse=True)

        keep: list[Detection] = []
        for det in detections:
            should_keep = True
            for kept in keep:
                if det.label == kept.label and self._iou(det.bbox, kept.bbox) > iou_threshold:
                    should_keep = False
                    break
            if should_keep:
                keep.append(det)

        return keep

    @staticmethod
    def _iou(
        box1: tuple[int, int, int, int], box2: tuple[int, int, int, int]
    ) -> float:
        """Compute Intersection over Union between two bounding boxes."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2

        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)

        inter_w = max(0, xi2 - xi1)
        inter_h = max(0, yi2 - yi1)
        inter_area = inter_w * inter_h

        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area

        if union_area == 0:
            return 0.0

        return inter_area / union_area
