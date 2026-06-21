"""GestureVision AI - unified app with a hand-controlled menu.

    python app.py

Starts the webcam and shows a menu. Point with your index finger and PINCH
(touch thumb + index) to choose:

    1. Focus Tracker  - PRESENT/AWAY status, head direction, finger counting
    2. Tic-Tac-Toe    - play against a minimax AI using hand gestures
    3. Quit

Inside any mode, press 'b' to go back to the menu, or 'q' to quit.

Everything runs locally; the webcam is only read in memory, never saved.
"""

import cv2
import mediapipe as mp

from focusvision import config, ui
from focusvision.detector import FaceDetector
from focusvision.hands import HandCounter
from focusvision.gestures import GestureRecognizer
from focusvision.tracker import PresenceTracker
from focusvision.stats import format_duration
from focusvision.tictactoe import TicTacToe, HUMAN, AI, EMPTY

# Drawing helpers / colors.
_mp_drawing = mp.solutions.drawing_utils
_mp_hands = mp.solutions.hands
GREEN = (0, 200, 0)
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
WHITE = (255, 255, 255)
CYAN = (255, 255, 0)
YELLOW = (0, 215, 255)
BLUE = (255, 180, 0)
GREY = (90, 90, 90)

# Screen states.
MENU, FOCUS, TICTACTOE = "menu", "focus", "tictactoe"

WINDOW_NAME = "GestureVision AI"

# Tic-Tac-Toe board geometry.
BOARD_SIZE = 360
MARGIN_TOP = 80
CELL = BOARD_SIZE // 3


# --------------------------------------------------------------------------
# Focus Tracker drawing
# --------------------------------------------------------------------------
def draw_focus(frame, tracker, face, hands_info):
    """Render the focus tracker overlay (presence, head, fingers)."""
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

    ui.draw_back_hint(frame)


# --------------------------------------------------------------------------
# Tic-Tac-Toe drawing & geometry
# --------------------------------------------------------------------------
def _board_origin():
    return (config.FRAME_WIDTH - BOARD_SIZE) // 2, MARGIN_TOP


def _cell_from_point(px, py):
    x0, y0 = _board_origin()
    if not (x0 <= px < x0 + BOARD_SIZE and y0 <= py < y0 + BOARD_SIZE):
        return None
    return int(((py - y0) // CELL) * 3 + (px - x0) // CELL)


def draw_tictactoe(frame, game, hover, difficulty):
    x0, y0 = _board_origin()

    if hover is not None and game.is_empty(hover) and not game.is_over():
        r, c = divmod(hover, 3)
        cv2.rectangle(frame, (x0 + c * CELL, y0 + r * CELL),
                      (x0 + (c + 1) * CELL, y0 + (r + 1) * CELL), (50, 50, 50), -1)

    win = game.winning_line()
    if win:
        for idx in win:
            r, c = divmod(idx, 3)
            cv2.rectangle(frame, (x0 + c * CELL, y0 + r * CELL),
                          (x0 + (c + 1) * CELL, y0 + (r + 1) * CELL), (0, 80, 0), -1)

    for i in range(1, 3):
        cv2.line(frame, (x0 + i * CELL, y0), (x0 + i * CELL, y0 + BOARD_SIZE), WHITE, 2)
        cv2.line(frame, (x0, y0 + i * CELL), (x0 + BOARD_SIZE, y0 + i * CELL), WHITE, 2)
    cv2.rectangle(frame, (x0, y0), (x0 + BOARD_SIZE, y0 + BOARD_SIZE), WHITE, 2)

    for idx, mark in enumerate(game.board):
        if mark == EMPTY:
            continue
        r, c = divmod(idx, 3)
        cx, cy = x0 + c * CELL + CELL // 2, y0 + r * CELL + CELL // 2
        if mark == HUMAN:
            d = CELL // 4
            cv2.line(frame, (cx - d, cy - d), (cx + d, cy + d), GREEN, 4)
            cv2.line(frame, (cx - d, cy + d), (cx + d, cy - d), GREEN, 4)
        else:
            cv2.circle(frame, (cx, cy), CELL // 4, RED, 4)

    cv2.putText(frame, "Tic-Tac-Toe", (x0, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, WHITE, 2)
    cv2.putText(frame, f"AI: {difficulty.upper()}  (e/h)  r=restart",
                (x0, y0 + BOARD_SIZE + 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, YELLOW, 1)
    if game.result_text():
        cv2.putText(frame, game.result_text(), (x0, y0 + BOARD_SIZE + 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, BLUE, 2)
    ui.draw_back_hint(frame)


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------
def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(
            "Could not open the webcam. Check CAMERA_INDEX in config.py "
            "and that no other app is using the camera."
        )

    # Detectors (created once, reused across modes).
    face_detector = FaceDetector()
    hand_counter = HandCounter(max_hands=config.MAX_HANDS)
    gestures = GestureRecognizer()

    tracker = PresenceTracker()
    game = TicTacToe()
    buttons = ui.build_menu_buttons()

    state = MENU
    difficulty = "hard"
    pinch_armed = True  # debounce: require release between pinch clicks

    print("GestureVision AI running. Point + pinch in the menu to choose.")

    # WINDOW_GUI_NORMAL makes the window's X (close) button report correctly
    # via WND_PROP_VISIBLE, so the app can be closed without the keyboard.
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_GUI_NORMAL)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Failed to read a frame from the webcam.")
                break
            frame = cv2.flip(frame, 1)  # mirror
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ---------------- MENU ----------------
            if state == MENU:
                g = gestures.detect(frame_rgb)
                hover_btn = None
                if g.hand_detected and g.index_pos:
                    px = int(g.index_pos[0] * config.FRAME_WIDTH)
                    py = int(g.index_pos[1] * config.FRAME_HEIGHT)
                    for btn in buttons:
                        if btn.contains(px, py):
                            hover_btn = btn
                            break
                    ui.draw_menu(frame, buttons, hover_btn, g.is_pinching)
                    ui.draw_cursor(frame, px, py, g.is_pinching)

                    if g.is_pinching and pinch_armed and hover_btn:
                        pinch_armed = False
                        if hover_btn.action == "quit":
                            break
                        elif hover_btn.action == "focus":
                            tracker.start_session()
                            state = FOCUS
                        elif hover_btn.action == "tictactoe":
                            game.reset()
                            state = TICTACTOE
                else:
                    ui.draw_menu(frame, buttons, None, False)

                # Re-arm whenever no pinch is active (hand released OR no hand),
                # so the next pinch always registers.
                if not g.is_pinching:
                    pinch_armed = True

            # ---------------- FOCUS TRACKER ----------------
            elif state == FOCUS:
                face = face_detector.detect(frame_rgb)
                hands_info = hand_counter.detect(frame_rgb)
                tracker.update(face_detected=face.detected,
                               head_direction=face.head_direction,
                               too_close=face.too_close)
                draw_focus(frame, tracker, face, hands_info)

            # ---------------- TIC-TAC-TOE ----------------
            elif state == TICTACTOE:
                g = gestures.detect(frame_rgb)
                hover = None
                if g.hand_detected and g.index_pos:
                    px = int(g.index_pos[0] * config.FRAME_WIDTH)
                    py = int(g.index_pos[1] * config.FRAME_HEIGHT)
                    hover = _cell_from_point(px, py)
                    ui.draw_cursor(frame, px, py, g.is_pinching)

                    if g.is_pinching and pinch_armed:
                        pinch_armed = False
                        if (not game.is_over() and hover is not None
                                and game.is_empty(hover)):
                            game.make_move(hover, HUMAN)
                            if not game.is_over():
                                game.ai_move(difficulty)
                draw_tictactoe(frame, game, hover, difficulty)

                # Re-arm whenever no pinch is active (hand released OR no hand).
                if not g.is_pinching:
                    pinch_armed = True

            cv2.imshow(WINDOW_NAME, frame)

            # ---------------- Keyboard ----------------
            key = cv2.waitKey(1) & 0xFF

            # Stop if the window was closed with the X button. (waitKey must run
            # first so the window event is processed.)
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break

            if key == ord("q"):
                break
            elif key == ord("b"):
                if state == FOCUS:
                    tracker.flush()  # save the open interval before leaving
                state = MENU
                pinch_armed = True
            elif state == TICTACTOE:
                if key == ord("r"):
                    game.reset()
                    pinch_armed = True
                elif key == ord("e"):
                    difficulty = "easy"
                elif key == ord("h"):
                    difficulty = "hard"
    finally:
        if state == FOCUS:
            tracker.flush()
        face_detector.close()
        hand_counter.close()
        gestures.close()
        cap.release()
        cv2.destroyAllWindows()
        print("Goodbye!")


if __name__ == "__main__":
    main()
