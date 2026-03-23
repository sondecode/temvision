"""Game state management."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GameState:
    """Represents the current state of a game.

    Tracks detected objects, derived state variables, and
    provides a dictionary interface for rule evaluation.
    """

    game: str = ""
    timestamp: float = 0.0
    detections: dict[str, bool] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    raw_detections: list[Any] = field(default_factory=list)

    def update_from_detections(
        self,
        detections: list[Any],
        mapping: dict[str, str],
        detect_targets: list[str],
    ) -> None:
        """Update state based on vision detections and config mapping.

        Args:
            detections: List of Detection objects from VisionEngine.
            mapping: Config mapping from detection labels to state keys.
            detect_targets: List of all target labels to detect.
        """
        self.timestamp = time.time()
        self.raw_detections = list(detections)

        # Reset all detection states to False
        for target in detect_targets:
            state_key = mapping.get(target, target)
            self.detections[state_key] = False

        # Set detected objects to True
        detected_labels = {d.label for d in detections}
        for label in detected_labels:
            state_key = mapping.get(label, label)
            self.detections[state_key] = True

        # Update derived variables
        for key, is_detected in self.detections.items():
            self.variables[f"{key}_visible"] = is_detected
            self.variables[f"{key}_count"] = sum(
                1 for d in detections if mapping.get(d.label, d.label) == key
            )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state variable by key."""
        return self.variables.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to a flat dictionary for rule evaluation."""
        result: dict[str, Any] = {
            "game": self.game,
            "timestamp": self.timestamp,
        }
        result.update(self.variables)
        return result

    def reset(self) -> None:
        """Reset all state."""
        self.timestamp = 0.0
        self.detections.clear()
        self.variables.clear()
        self.raw_detections.clear()
