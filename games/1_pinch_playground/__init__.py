"""Pinch Playground: practice the pinch gesture (with a live counter) while
seeing finger counting and presence/head info.

The hub (app.py) imports this package and uses:
  - draw(frame, tracker, face, hands_info, pinch_count)

The actual pinch counting / presence logic stays in app.py because it reuses
the shared detectors; this module only handles this mode's drawing.
"""

import cv2
import mediapipe as mp

from gesturevision import config, ui
from gesturevision.stats import format_duration

__all__ = ["draw"]

_mp_drawing = mp.solutions.drawing_utils
_mp_hands = mp.solutions.hands

# Colors (BGR).
GREEN = (0, 200, 0)
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)
YELLOW = (0, 215, 255)


def draw(frame, tracker, face, hands_info, pinch_count):
    """Render the Pinch Playground overlay (presence, head, fingers, counter)."""
    color = GREEN if tracker.status == config.STATUS_PRESENT else RED
    cv2.putText(frame, f"Status: {tracker.status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
    cv2.putText(frame, f"This interval: {format_duration(tracker.current_interval_seconds())}",
                (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)

    if face.detected:
        cv2.putText(frame, f"Head: {face.head_direction}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
        if face.too_close:
            cv2.putText(frame, "TOO CLOSE!", (10, 125),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2)

    if tracker.long_sitting_warning():
        cv2.putText(frame, "Time for a break! (45+ min)", (10, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2)

    # Hand skeleton + finger count.
    for hand_landmarks in hands_info.landmarks:
        _mp_drawing.draw_landmarks(frame, hand_landmarks, _mp_hands.HAND_CONNECTIONS)
    if hands_info.hands_detected:
        cv2.putText(frame, f"Fingers: {hands_info.total_fingers}",
                    (config.FRAME_WIDTH - 260, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, CYAN, 3)

    # Pinch practice counter.
    cv2.putText(frame, "Pinch Playground - practice your pinch!",
                (10, config.FRAME_HEIGHT - 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, YELLOW, 1)
    cv2.putText(frame, f"Pinches: {pinch_count}",
                (10, config.FRAME_HEIGHT - 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, CYAN, 3)

    ui.draw_back_hint(frame)
