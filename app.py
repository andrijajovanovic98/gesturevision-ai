"""GestureVision AI - unified app with a hand-controlled menu.

    python app.py

Starts the webcam and shows a menu. Point and PINCH (touch thumb + index), or
press the number keys, to choose:

    1. Pinch Playground - practice pinching (counter) + finger/presence info
    2. Tic-Tac-Toe      - play against a minimax AI using hand gestures
    3. Quit

Inside any mode, press 'b' to go back to the menu, or 'q' to quit.

Everything runs locally; the webcam is only read in memory, never saved.
"""

import importlib

import cv2

from gesturevision import config, ui
from gesturevision.detector import FaceDetector
from gesturevision.hands import HandCounter
from gesturevision.gestures import GestureRecognizer
from gesturevision.tracker import PresenceTracker

# Games live in their own numbered folders under games/. Because those folder
# names start with a digit, we load them with importlib instead of a plain
# `import games.2_tictactoe`. Adding a new game = add a folder + one line here.
pinch_playground = importlib.import_module("games.1_pinch_playground")
tictactoe = importlib.import_module("games.2_tictactoe")

# Convenient aliases for the Tic-Tac-Toe logic exposed by its package.
TicTacToe = tictactoe.TicTacToe
HUMAN = tictactoe.HUMAN

# Screen states.
MENU, FOCUS, TICTACTOE = "menu", "focus", "tictactoe"

WINDOW_NAME = "GestureVision AI"


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
    pinch_count = 0     # practice counter for the Pinch Playground

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
                            pinch_count = 0
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

            # ---------------- PINCH PLAYGROUND ----------------
            elif state == FOCUS:
                face = face_detector.detect(frame_rgb)
                hands_info = hand_counter.detect(frame_rgb)
                tracker.update(face_detected=face.detected,
                               head_direction=face.head_direction,
                               too_close=face.too_close)

                # Practice pinching: each completed pinch bumps the counter.
                g = gestures.detect(frame_rgb)
                if g.hand_detected and g.index_pos:
                    px = int(g.index_pos[0] * config.FRAME_WIDTH)
                    py = int(g.index_pos[1] * config.FRAME_HEIGHT)
                    ui.draw_cursor(frame, px, py, g.is_pinching)
                if g.is_pinching and pinch_armed:
                    pinch_armed = False
                    pinch_count += 1
                if not g.is_pinching:
                    pinch_armed = True

                pinch_playground.draw(frame, tracker, face, hands_info, pinch_count)

            # ---------------- TIC-TAC-TOE ----------------
            elif state == TICTACTOE:
                g = gestures.detect(frame_rgb)
                hover = None
                if g.hand_detected and g.index_pos:
                    px = int(g.index_pos[0] * config.FRAME_WIDTH)
                    py = int(g.index_pos[1] * config.FRAME_HEIGHT)
                    hover = tictactoe.cell_from_point(px, py)
                    ui.draw_cursor(frame, px, py, g.is_pinching)

                    if g.is_pinching and pinch_armed:
                        pinch_armed = False
                        if (not game.is_over() and hover is not None
                                and game.is_empty(hover)):
                            game.make_move(hover, HUMAN)
                            if not game.is_over():
                                game.ai_move(difficulty)
                tictactoe.draw(frame, game, hover, difficulty)

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
            elif state == MENU:
                # Number keys select menu items, just like pinching them.
                if key == ord("1"):
                    tracker.start_session()
                    pinch_count = 0
                    state = FOCUS
                elif key == ord("2"):
                    game.reset()
                    state = TICTACTOE
                elif key == ord("3"):
                    break
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
