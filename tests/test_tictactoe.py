"""Tests for the Tic-Tac-Toe logic and the minimax AI.

These run without a webcam. The key guarantees we check:
  - win/draw detection works,
  - the hard (minimax) AI never loses,
  - the AI takes an immediate win and blocks an immediate loss.
"""

import random

from gesturevision.tictactoe import TicTacToe, HUMAN, AI, EMPTY


def test_detects_row_win():
    game = TicTacToe()
    game.board = [HUMAN, HUMAN, HUMAN,
                  EMPTY, EMPTY, EMPTY,
                  EMPTY, EMPTY, EMPTY]
    assert game.winner() == HUMAN
    assert game.is_over() is True


def test_detects_diagonal_win():
    game = TicTacToe()
    game.board = [AI, EMPTY, EMPTY,
                  EMPTY, AI, EMPTY,
                  EMPTY, EMPTY, AI]
    assert game.winner() == AI
    assert game.winning_line() == (0, 4, 8)


def test_draw_is_detected():
    game = TicTacToe()
    game.board = [HUMAN, AI, HUMAN,
                  HUMAN, AI, AI,
                  AI, HUMAN, HUMAN]
    assert game.winner() is None
    assert game.is_full() is True
    assert game.result_text() == "It's a draw!"


def test_cannot_overwrite_cell():
    game = TicTacToe()
    assert game.make_move(0, HUMAN) is True
    assert game.make_move(0, AI) is False  # already taken
    assert game.board[0] == HUMAN


def test_ai_takes_immediate_win():
    game = TicTacToe()
    # AI ("O") can win by playing index 2.
    game.board = [AI, AI, EMPTY,
                  HUMAN, HUMAN, EMPTY,
                  EMPTY, EMPTY, EMPTY]
    move = game.ai_move("hard")
    assert move == 2
    assert game.winner() == AI


def test_ai_blocks_immediate_loss():
    game = TicTacToe()
    # Human threatens to win at index 2; AI must block there.
    game.board = [HUMAN, HUMAN, EMPTY,
                  EMPTY, AI, EMPTY,
                  EMPTY, EMPTY, EMPTY]
    move = game.ai_move("hard")
    assert move == 2


def test_minimax_ai_never_loses():
    """Play many games of a random human vs the hard AI; AI must never lose."""
    random.seed(42)
    for _ in range(50):
        game = TicTacToe()
        # Human moves first each game (as in the real app).
        while not game.is_over():
            human_moves = game.available_moves()
            game.make_move(random.choice(human_moves), HUMAN)
            if game.is_over():
                break
            game.ai_move("hard")
        assert game.winner() != HUMAN  # AI either wins or draws, never loses
