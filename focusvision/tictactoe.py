"""Tic-Tac-Toe game logic with a minimax AI opponent.

This module is completely independent of the webcam / OpenCV layer so it can
be unit-tested on its own. The board is a flat list of 9 cells:

    0 | 1 | 2
    ---------
    3 | 4 | 5
    ---------
    6 | 7 | 8

Each cell is "X", "O" or "" (empty). By convention the human plays "X" and
the AI plays "O".
"""

import math
import random
from typing import List, Optional

EMPTY = ""
HUMAN = "X"
AI = "O"

# All winning line index triplets (rows, columns, diagonals).
_WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
    (0, 4, 8), (2, 4, 6),              # diagonals
]


class TicTacToe:
    """Holds the board state and the rules; knows nothing about the UI."""

    def __init__(self):
        self.board: List[str] = [EMPTY] * 9
        self.current_player: str = HUMAN  # human starts

    # --- Board queries -----------------------------------------------------

    def available_moves(self) -> List[int]:
        """Indices of all empty cells."""
        return [i for i, cell in enumerate(self.board) if cell == EMPTY]

    def is_empty(self, index: int) -> bool:
        return 0 <= index < 9 and self.board[index] == EMPTY

    def winner(self) -> Optional[str]:
        """Return 'X' or 'O' if someone has won, else None."""
        for a, b, c in _WIN_LINES:
            if self.board[a] != EMPTY and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]
        return None

    def winning_line(self) -> Optional[tuple]:
        """Return the triplet of indices forming the win, for highlighting."""
        for line in _WIN_LINES:
            a, b, c = line
            if self.board[a] != EMPTY and self.board[a] == self.board[b] == self.board[c]:
                return line
        return None

    def is_full(self) -> bool:
        return EMPTY not in self.board

    def is_over(self) -> bool:
        return self.winner() is not None or self.is_full()

    def result_text(self) -> str:
        """Human-readable outcome once the game is over."""
        w = self.winner()
        if w == HUMAN:
            return "You win!"
        if w == AI:
            return "AI wins!"
        if self.is_full():
            return "It's a draw!"
        return ""

    # --- Moves -------------------------------------------------------------

    def make_move(self, index: int, player: str) -> bool:
        """Place `player` at `index`. Returns True if the move was legal."""
        if not self.is_empty(index):
            return False
        self.board[index] = player
        return True

    def reset(self) -> None:
        self.board = [EMPTY] * 9
        self.current_player = HUMAN

    # --- AI ----------------------------------------------------------------

    def ai_move(self, difficulty: str = "hard") -> Optional[int]:
        """Choose and play the AI's move. Returns the chosen index.

        difficulty="easy"  -> random legal move
        difficulty="hard"  -> optimal minimax move (unbeatable)
        """
        moves = self.available_moves()
        if not moves:
            return None

        if difficulty == "easy":
            choice = random.choice(moves)
        else:
            choice = self._best_move()

        self.make_move(choice, AI)
        return choice

    def _best_move(self) -> int:
        """Pick the move with the highest minimax score for the AI."""
        best_score = -math.inf
        best_index = self.available_moves()[0]

        for index in self.available_moves():
            self.board[index] = AI
            score = self._minimax(depth=0, is_maximizing=False)
            self.board[index] = EMPTY
            if score > best_score:
                best_score = score
                best_index = index
        return best_index

    def _minimax(self, depth: int, is_maximizing: bool) -> int:
        """Classic minimax. Prefers faster wins / slower losses via depth.

        Scoring (from the AI's point of view):
            AI win  -> +10 (minus depth, so quicker wins are better)
            Human win -> -10 (plus depth, so delayed losses are "better")
            Draw    ->  0
        """
        winner = self.winner()
        if winner == AI:
            return 10 - depth
        if winner == HUMAN:
            return depth - 10
        if self.is_full():
            return 0

        if is_maximizing:  # AI's turn -> maximise
            best = -math.inf
            for index in self.available_moves():
                self.board[index] = AI
                best = max(best, self._minimax(depth + 1, False))
                self.board[index] = EMPTY
            return best
        else:              # human's turn -> minimise
            best = math.inf
            for index in self.available_moves():
                self.board[index] = HUMAN
                best = min(best, self._minimax(depth + 1, True))
                self.board[index] = EMPTY
            return best
