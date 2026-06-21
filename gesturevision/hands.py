"""Hand detection & finger counting built on MediaPipe Hands.

Given a webcam frame, this answers: how many fingers are being held up?
MediaPipe returns 21 landmarks per hand; we use simple geometry on the
fingertip vs. lower-joint positions to decide which fingers are extended.

Like the rest of the project this is privacy-first: only landmark
coordinates (numbers) are used, never the image itself.
"""

from dataclasses import dataclass, field
from typing import List

import mediapipe as mp

from . import config


# MediaPipe Hands landmark indices we care about.
# Fingertips: thumb=4, index=8, middle=12, ring=16, pinky=20.
# The joint just below each fingertip (PIP for fingers, IP for thumb).
_FINGERTIPS = [8, 12, 16, 20]          # four fingers (not thumb)
_FINGER_PIPS = [6, 10, 14, 18]         # joint below each fingertip
_THUMB_TIP = 4
_THUMB_IP = 3
_WRIST = 0


@dataclass
class HandsInfo:
    """Result of one finger-count detection (metadata only)."""

    hands_detected: int = 0
    # Total fingers extended across all detected hands.
    total_fingers: int = 0
    # Per-hand finger counts, e.g. [5, 2].
    per_hand: List[int] = field(default_factory=list)
    # Normalised landmark lists per hand, for optional drawing.
    landmarks: list = field(default_factory=list)


class HandCounter:
    """Reusable wrapper around MediaPipe Hands that counts raised fingers."""

    def __init__(self, max_hands: int = 2,
                 min_confidence: float = config.MIN_DETECTION_CONFIDENCE):
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=min_confidence,
            min_tracking_confidence=0.5,
        )

    def detect(self, frame_rgb) -> HandsInfo:
        """Run hand detection on an RGB frame; return finger counts only."""
        results = self._hands.process(frame_rgb)

        if not results.multi_hand_landmarks:
            return HandsInfo()

        per_hand: List[int] = []
        all_landmarks = []

        # `multi_handedness` tells us Left vs Right, needed for the thumb.
        handedness = results.multi_handedness or []
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            lm = hand_landmarks.landmark
            label = (
                handedness[idx].classification[0].label
                if idx < len(handedness) else "Right"
            )
            per_hand.append(self._count_fingers(lm, label))
            all_landmarks.append(hand_landmarks)

        return HandsInfo(
            hands_detected=len(per_hand),
            total_fingers=sum(per_hand),
            per_hand=per_hand,
            landmarks=all_landmarks,
        )

    @staticmethod
    def _count_fingers(lm, handedness_label: str) -> int:
        """Count extended fingers for a single hand from its 21 landmarks.

        Four fingers: tip is "up" if it sits higher (smaller y) than its PIP
        joint. Thumb: compared horizontally (x) because it points sideways,
        with direction depending on which hand it is.
        """
        count = 0

        # Four fingers (index, middle, ring, pinky).
        for tip, pip in zip(_FINGERTIPS, _FINGER_PIPS):
            if lm[tip].y < lm[pip].y:
                count += 1

        # Thumb: MediaPipe mirrors the image, so a "Right" hand's thumb is
        # extended when its tip is to the left (smaller x) of the IP joint,
        # and vice versa for the "Left" hand.
        if handedness_label == "Right":
            if lm[_THUMB_TIP].x < lm[_THUMB_IP].x:
                count += 1
        else:
            if lm[_THUMB_TIP].x > lm[_THUMB_IP].x:
                count += 1

        return count

    def close(self) -> None:
        self._hands.close()

    def __enter__(self) -> "HandCounter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
