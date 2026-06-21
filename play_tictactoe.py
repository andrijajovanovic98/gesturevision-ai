"""Play Tic-Tac-Toe against an AI using only hand gestures.

    python play_tictactoe.py

How to play:
  - Move your hand: your index fingertip is the cursor (a dot on screen).
  - Hover over a cell, then PINCH (touch thumb + index together) to place X.
  - The AI responds with O.
  - Keys:  'r' = restart,  'e'/'h' = easy/hard AI,  'q' = quit.

Privacy note: the webcam is used only to read hand landmarks in memory.
No image or video is ever saved.
"""

import cv2
import mediapipe as mp

import importlib

from gesturevision import config
from gesturevision.gestures import GestureRecognizer

# Tic-Tac-Toe logic lives in games/2_tictactoe/ (folder starts with a digit).
_logic = importlib.import_module("games.2_tictactoe.logic")
TicTacToe = _logic.TicTacToe
HUMAN, AI, EMPTY = _logic.HUMAN, _logic.AI, _logic.EMPTY

WINDOW_NAME = "Gesture Tic-Tac-Toe"

# Drawing helpers (BGR colors).
WHITE = (255, 255, 255)
GREY = (90, 90, 90)
GREEN = (0, 200, 0)
RED = (60, 60, 255)
BLUE = (255, 180, 0)
YELLOW = (0, 215, 255)
CYAN = (255, 255, 0)

_mp_drawing = mp.solutions.drawing_utils
_mp_hands = mp.solutions.hands

# Board geometry: a square grid centred in the frame.
BOARD_SIZE = 360                     # pixels
MARGIN_TOP = 80
CELL = BOARD_SIZE // 3


def _board_origin():
    """Top-left (x, y) pixel of the board, horizontally centred."""
    x0 = (config.FRAME_WIDTH - BOARD_SIZE) // 2
    y0 = MARGIN_TOP
    return x0, y0


def _cell_from_point(px: int, py: int):
    """Map a pixel position to a board cell index (0-8) or None."""
    x0, y0 = _board_origin()
    if not (x0 <= px < x0 + BOARD_SIZE and y0 <= py < y0 + BOARD_SIZE):
        return None
    col = (px - x0) // CELL
    row = (py - y0) // CELL
    return int(row * 3 + col)


def _draw_board(frame, game: TicTacToe, hover, difficulty, status_msg):
    """Render the grid, marks, cursor and HUD onto the frame."""
    x0, y0 = _board_origin()

    # Highlight the hovered (empty) cell.
    if hover is not None and game.is_empty(hover) and not game.is_over():
        r, c = divmod(hover, 3)
        cv2.rectangle(
            frame,
            (x0 + c * CELL, y0 + r * CELL),
            (x0 + (c + 1) * CELL, y0 + (r + 1) * CELL),
            (50, 50, 50), -1,
        )

    # Highlight the winning line, if any.
    win = game.winning_line()
    if win:
        for idx in win:
            r, c = divmod(idx, 3)
            cv2.rectangle(
                frame,
                (x0 + c * CELL, y0 + r * CELL),
                (x0 + (c + 1) * CELL, y0 + (r + 1) * CELL),
                (0, 80, 0), -1,
            )

    # Grid lines.
    for i in range(1, 3):
        cv2.line(frame, (x0 + i * CELL, y0), (x0 + i * CELL, y0 + BOARD_SIZE), WHITE, 2)
        cv2.line(frame, (x0, y0 + i * CELL), (x0 + BOARD_SIZE, y0 + i * CELL), WHITE, 2)
    cv2.rectangle(frame, (x0, y0), (x0 + BOARD_SIZE, y0 + BOARD_SIZE), WHITE, 2)

    # Marks.
    for idx, mark in enumerate(game.board):
        if mark == EMPTY:
            continue
        r, c = divmod(idx, 3)
        cx = x0 + c * CELL + CELL // 2
        cy = y0 + r * CELL + CELL // 2
        if mark == HUMAN:
            d = CELL // 4
            cv2.line(frame, (cx - d, cy - d), (cx + d, cy + d), GREEN, 4)
            cv2.line(frame, (cx - d, cy + d), (cx + d, cy - d), GREEN, 4)
        else:
            cv2.circle(frame, (cx, cy), CELL // 4, RED, 4)

    # HUD: title + difficulty + status.
    cv2.putText(frame, "Gesture Tic-Tac-Toe", (x0, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, WHITE, 2)
    cv2.putText(frame, f"AI: {difficulty.upper()}  (e/h to switch)",
                (x0, y0 + BOARD_SIZE + 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, YELLOW, 1)
    cv2.putText(frame, "Pinch to place  |  r=restart  q=quit",
                (x0, y0 + BOARD_SIZE + 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREY, 1)
    if status_msg:
        cv2.putText(frame, status_msg, (x0, y0 + BOARD_SIZE + 105),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, BLUE, 2)


def main() -> None:
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    if not cap.isOpened():
        raise RuntimeError(
            "Could not open the webcam. Check CAMERA_INDEX in config.py "
            "and that no other app is using the camera."
        )

    game = TicTacToe()
    difficulty = "hard"
    # Pinch must be released before it can trigger another placement.
    pinch_armed = True

    print("Gesture Tic-Tac-Toe running. Pinch to place, 'q' to quit.")

    # WINDOW_GUI_NORMAL lets the window's X (close) button work.
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_GUI_NORMAL)

    try:
        with GestureRecognizer() as recognizer:
            while True:
                ok, frame = cap.read()
                if not ok:
                    print("Failed to read a frame from the webcam.")
                    break

                frame = cv2.flip(frame, 1)  # mirror for natural control
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                gesture = recognizer.detect(frame_rgb)

                hover = None
                if gesture.hand_detected and gesture.index_pos:
                    px = int(gesture.index_pos[0] * config.FRAME_WIDTH)
                    py = int(gesture.index_pos[1] * config.FRAME_HEIGHT)
                    hover = _cell_from_point(px, py)

                    # Draw the cursor dot.
                    dot_color = CYAN if gesture.is_pinching else WHITE
                    cv2.circle(frame, (px, py), 10, dot_color, -1)

                    # Handle a pinch "click" (debounced).
                    if gesture.is_pinching and pinch_armed:
                        pinch_armed = False
                        if (not game.is_over() and hover is not None
                                and game.current_player == HUMAN
                                and game.is_empty(hover)):
                            game.make_move(hover, HUMAN)
                            if not game.is_over():
                                game.current_player = AI
                                game.ai_move(difficulty)
                                game.current_player = HUMAN
                    elif not gesture.is_pinching:
                        pinch_armed = True  # re-arm once released

                _draw_board(frame, game, hover, difficulty, game.result_text())
                cv2.imshow(WINDOW_NAME, frame)

                key = cv2.waitKey(1) & 0xFF

                # Stop if the window was closed with the X button. (waitKey must
                # run first so the window event is processed.)
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
                if key == ord("q"):
                    break
                elif key == ord("r"):
                    game.reset()
                    pinch_armed = True
                elif key == ord("e"):
                    difficulty = "easy"
                elif key == ord("h"):
                    difficulty = "hard"
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Thanks for playing!")


if __name__ == "__main__":
    main()
