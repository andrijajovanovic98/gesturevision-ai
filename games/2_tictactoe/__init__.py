"""Tic-Tac-Toe game: rules + minimax AI (logic.py) and webcam drawing.

The hub (app.py) imports this package and uses:
  - TicTacToe, HUMAN, AI, EMPTY   (game logic, from logic.py)
  - cell_from_point(px, py)       (map a pixel to a board cell)
  - draw(frame, game, hover, difficulty)
"""

import cv2

from gesturevision import config, ui
from .logic import TicTacToe, HUMAN, AI, EMPTY

# Re-export so the hub can do `from games... import TicTacToe`.
__all__ = ["TicTacToe", "HUMAN", "AI", "EMPTY", "cell_from_point", "draw"]

# Colors (BGR).
WHITE = (255, 255, 255)
GREEN = (0, 200, 0)
RED = (0, 0, 255)
YELLOW = (0, 215, 255)
BLUE = (255, 180, 0)

# Board geometry.
BOARD_SIZE = 360
MARGIN_TOP = 80
CELL = BOARD_SIZE // 3


def _board_origin():
    return (config.FRAME_WIDTH - BOARD_SIZE) // 2, MARGIN_TOP


def cell_from_point(px, py):
    """Map a pixel position to a board cell index (0-8) or None."""
    x0, y0 = _board_origin()
    if not (x0 <= px < x0 + BOARD_SIZE and y0 <= py < y0 + BOARD_SIZE):
        return None
    return int(((py - y0) // CELL) * 3 + (px - x0) // CELL)


def draw(frame, game, hover, difficulty):
    """Render the board, marks, hover highlight and status onto the frame."""
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
