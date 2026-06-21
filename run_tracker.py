"""Live webcam tracker for GestureVision AI.

Run this to start tracking:

    python run_tracker.py

It opens the webcam, shows a small status overlay, and logs PRESENT/AWAY
intervals to data/events.csv. Press 'q' to quit (the open interval is saved).

Privacy: frames are processed in memory only. Nothing is recorded or sent
anywhere.
"""

import cv2
import mediapipe as mp

from focusvision import config
from focusvision.detector import FaceDetector
from focusvision.hands import HandCounter
from focusvision.tracker import PresenceTracker
from focusvision.stats import format_duration

# MediaPipe drawing helpers for the hand skeleton overlay.
_mp_drawing = mp.solutions.drawing_utils
_mp_hands = mp.solutions.hands


WINDOW_NAME = "GestureVision AI"

# Colors (BGR) for the on-screen overlay.
GREEN = (0, 200, 0)
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)


def _draw_hands(frame, hands_info) -> None:
    """Draw the hand skeleton and the finger count on the frame."""
    for hand_landmarks in hands_info.landmarks:
        _mp_drawing.draw_landmarks(
            frame, hand_landmarks, _mp_hands.HAND_CONNECTIONS
        )

    if hands_info.hands_detected:
        # Big, friendly finger count in the top-right corner.
        text = f"Fingers: {hands_info.total_fingers}"
        cv2.putText(frame, text, (config.FRAME_WIDTH - 260, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, CYAN, 3)
        if len(hands_info.per_hand) > 1:
            detail = " + ".join(str(n) for n in hands_info.per_hand)
            cv2.putText(frame, f"({detail})", (config.FRAME_WIDTH - 260, 85),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, CYAN, 1)


def _draw_overlay(frame, tracker: PresenceTracker, face) -> None:
    """Draw status text on the frame (no image is ever saved)."""
    is_present = tracker.status == config.STATUS_PRESENT
    color = GREEN if is_present else RED

    cv2.putText(frame, f"Status: {tracker.status}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    interval = format_duration(tracker.current_interval_seconds())
    cv2.putText(frame, f"This interval: {interval}", (10, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)

    if face.detected:
        cv2.putText(frame, f"Head: {face.head_direction}", (10, 95),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, WHITE, 1)
        if face.too_close:
            cv2.putText(frame, "TOO CLOSE!", (10, 125),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2)

    if tracker.long_sitting_warning():
        cv2.putText(frame, "Time for a break! (45+ min)", (10, 160),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, ORANGE, 2)

    cv2.putText(frame, "Press 'q' to quit", (10, config.FRAME_HEIGHT - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1)


def main() -> None:
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        raise RuntimeError(
            "Could not open the webcam. Check CAMERA_INDEX in config.py "
            "and that no other app is using the camera."
        )

    tracker = PresenceTracker()
    print("GestureVision AI is running. Press 'q' in the video window to stop.")

    # Optional finger counter (None if disabled in config).
    hand_counter = (
        HandCounter(max_hands=config.MAX_HANDS)
        if config.ENABLE_FINGER_COUNTING else None
    )

    # WINDOW_GUI_NORMAL lets the window's X (close) button work.
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_GUI_NORMAL)

    try:
        with FaceDetector() as detector:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Failed to read a frame from the webcam.")
                    break

                # Mirror the frame so it feels like a mirror (nicer for hands).
                frame = cv2.flip(frame, 1)

                # MediaPipe expects RGB; OpenCV gives BGR.
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face = detector.detect(frame_rgb)

                tracker.update(
                    face_detected=face.detected,
                    head_direction=face.head_direction,
                    too_close=face.too_close,
                )

                _draw_overlay(frame, tracker, face)

                if hand_counter is not None:
                    hands_info = hand_counter.detect(frame_rgb)
                    _draw_hands(frame, hands_info)

                cv2.imshow(WINDOW_NAME, frame)

                # Stop on 'q' or when the window is closed with the X button.
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
    finally:
        tracker.flush()  # save the in-progress interval
        if hand_counter is not None:
            hand_counter.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Stopped. Events saved to:", config.LOG_FILE)


if __name__ == "__main__":
    main()
