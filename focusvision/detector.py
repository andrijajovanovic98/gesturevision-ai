"""Face detection wrapper built on MediaPipe Face Detection.

This module is intentionally small: it takes a webcam frame and answers two
questions:
  1. Is there a face? (presence)
  2. If so, where is it, how big is it, and which way is the head turned?

It never stores or returns the image itself - only lightweight metadata -
which keeps the project privacy-first.
"""

from dataclasses import dataclass
from typing import Optional

import mediapipe as mp

from . import config


@dataclass
class FaceInfo:
    """Lightweight description of a detected face (no pixels stored)."""

    detected: bool
    # Normalised face box (0..1) relative to the frame. None if not detected.
    box_ratio_width: float = 0.0
    # "left", "right", "center" or "unknown".
    head_direction: str = "unknown"
    # True if the face fills too much of the frame (user too close).
    too_close: bool = False


class FaceDetector:
    """Thin, reusable wrapper around MediaPipe Face Detection."""

    def __init__(self, min_confidence: float = config.MIN_DETECTION_CONFIDENCE):
        self._mp_face = mp.solutions.face_detection
        # model_selection=0 -> short range model, ideal for a laptop webcam.
        self._detector = self._mp_face.FaceDetection(
            model_selection=0,
            min_detection_confidence=min_confidence,
        )

    def detect(self, frame_rgb) -> FaceInfo:
        """Run detection on an RGB frame and return metadata only.

        `frame_rgb` must be an RGB image (OpenCV gives BGR, so convert first).
        """
        results = self._detector.process(frame_rgb)

        if not results.detections:
            return FaceInfo(detected=False)

        # Use the first (most confident) detection.
        detection = results.detections[0]
        box = detection.location_data.relative_bounding_box
        keypoints = detection.location_data.relative_keypoints

        too_close = box.width >= config.TOO_CLOSE_FACE_RATIO
        head_direction = self._estimate_head_direction(box, keypoints)

        return FaceInfo(
            detected=True,
            box_ratio_width=float(box.width),
            head_direction=head_direction,
            too_close=too_close,
        )

    @staticmethod
    def _estimate_head_direction(box, keypoints) -> str:
        """Rough head direction from the nose position inside the face box.

        MediaPipe keypoint index 2 is the nose tip. If the nose sits clearly
        left or right of the box center, the head is turned that way.
        """
        if keypoints is None or len(keypoints) < 3:
            return "unknown"

        nose = keypoints[2]
        box_center_x = box.xmin + box.width / 2.0
        # Offset as a fraction of the face width (handles near/far faces).
        offset = (nose.x - box_center_x) / max(box.width, 1e-6)

        if offset < -config.HEAD_DIRECTION_THRESHOLD:
            # Nose is to the user's right side of the image -> looking right.
            return "right"
        if offset > config.HEAD_DIRECTION_THRESHOLD:
            return "left"
        return "center"

    def close(self) -> None:
        """Release MediaPipe resources."""
        self._detector.close()

    def __enter__(self) -> "FaceDetector":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
