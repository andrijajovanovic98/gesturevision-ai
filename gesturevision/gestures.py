"""Simple hand-gesture recognition for the Tic-Tac-Toe game.

Built on MediaPipe Hands landmarks (21 points per hand). We expose two
gestures the game needs:

  - POINTING: the index fingertip position, used to hover over a cell.
  - PINCH:    thumb tip and index tip brought close together = "click".

Like the rest of GestureVision, this only ever looks at landmark coordinates,
never the raw image.
"""

from dataclasses import dataclass
from math import hypot
from typing import Optional, Tuple

import mediapipe as mp

# Landmark indices we use.
_WRIST = 0
_THUMB_TIP = 4
_INDEX_TIP = 8
_MIDDLE_MCP = 9   # base knuckle of the middle finger (a stable size reference)

# Pinch is decided by the thumb-index distance *relative to the hand's own
# size* (wrist -> middle knuckle). Using a ratio instead of a raw distance
# makes detection independent of how far away or rotated the hand is, so
# rotating the hand no longer triggers false pinches.
PINCH_RATIO_THRESHOLD = 0.45


@dataclass
class GestureInfo:
    """One frame's gesture reading (all coordinates normalised 0..1)."""

    hand_detected: bool = False
    # Index fingertip position (the "cursor").
    index_pos: Optional[Tuple[float, float]] = None
    # True when thumb + index are pinched together (a "click").
    is_pinching: bool = False
    # Raw normalised pinch distance (useful for tuning / debugging).
    pinch_distance: float = 1.0


class GestureRecognizer:
    """Wraps MediaPipe Hands and reports pointing + pinch gestures."""

    def __init__(self, min_confidence: float = 0.6):
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,            # one hand controls the game
            min_detection_confidence=min_confidence,
            min_tracking_confidence=0.5,
        )

    def detect(self, frame_rgb) -> GestureInfo:
        """Read one RGB frame and return the current gesture state."""
        results = self._hands.process(frame_rgb)

        if not results.multi_hand_landmarks:
            return GestureInfo()

        lm = results.multi_hand_landmarks[0].landmark
        index_tip = lm[_INDEX_TIP]
        thumb_tip = lm[_THUMB_TIP]

        # Distance between thumb and index tips.
        tip_distance = hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)

        # Reference: the size of the hand itself (wrist -> middle knuckle).
        # Scales with distance and stays stable when the hand rotates.
        wrist = lm[_WRIST]
        middle_mcp = lm[_MIDDLE_MCP]
        hand_size = hypot(wrist.x - middle_mcp.x, wrist.y - middle_mcp.y)

        ratio = tip_distance / max(hand_size, 1e-6)

        return GestureInfo(
            hand_detected=True,
            index_pos=(index_tip.x, index_tip.y),
            is_pinching=ratio < PINCH_RATIO_THRESHOLD,
            pinch_distance=ratio,
        )

    def close(self) -> None:
        self._hands.close()

    def __enter__(self) -> "GestureRecognizer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
