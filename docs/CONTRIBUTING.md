# Contributing to GestureVision AI

Thanks for your interest in contributing! This project is meant to be a
friendly playground for computer vision and hand gestures, so new gesture-based
games and modes are very welcome.

This guide focuses on the most common contribution: **adding a new game or mode
to the menu.** General fixes, docs and refactors are welcome too — just open a
pull request.

---

## Getting set up

```bash
# 1. Fork the repo on GitHub, then clone your fork
git clone https://github.com/<your-username>/gesturevision-ai.git
cd gesturevision-ai

# 2. Create a branch for your change
git checkout -b my-new-game

# 3. Set everything up and run it (creates the venv + installs deps)
python start.py
```

Run the tests before and after your change:

```bash
pytest
```

---

## How the app is structured

- **`gesturevision/`** — the core package (one job per file):
  - `gestures.py` — pointing + pinch detection (your input device)
  - `tictactoe.py` — an example of pure game logic with no webcam code
  - `ui.py` — the on-screen menu and its buttons
  - `detector.py`, `hands.py`, `tracker.py`, `stats.py`, `logger.py`, `config.py`
- **`app.py`** — the hub: one webcam loop that switches between *states*
  (menu, Pinch Playground, Tic-Tac-Toe).
- **`tests/`** — unit tests for the logic that doesn't need a webcam.

The golden rule: **keep game/logic code separate from the webcam/drawing
code**, exactly like `tictactoe.py` (pure rules) vs. its drawing in `app.py`.
This makes the logic easy to unit-test.

---

## Adding a new game to the menu — step by step

Let's say you want to add a game called **"Rock Paper Scissors"**.

### 1. Write the game logic (no webcam!)

Create `gesturevision/rps.py` with a small, testable class — just the rules,
no OpenCV. Follow the style of `gesturevision/tictactoe.py`.

```python
class RockPaperScissors:
    def play(self, player_move: str) -> str:
        """Return 'win', 'lose' or 'draw' for the player's move."""
        ...
```

### 2. Add a unit test

Create `tests/test_rps.py` and test the rules without a webcam, like
`tests/test_tictactoe.py` does. This is required for game logic.

### 3. Add a menu button

In `gesturevision/ui.py`, add your mode to the `items` list in
`build_menu_buttons()`:

```python
items = [
    ("1. Pinch Playground", "focus"),
    ("2. Tic-Tac-Toe (hand)", "tictactoe"),
    ("3. Rock Paper Scissors", "rps"),   # <-- your new mode
    ("4. Quit", "quit"),
]
```

### 4. Wire it into the hub (`app.py`)

1. Add a state constant near the top:
   ```python
   MENU, FOCUS, TICTACTOE, RPS = "menu", "focus", "tictactoe", "rps"
   ```
2. In the menu handling, switch to your state when the button is pinched (and,
   optionally, with its number key).
3. Add an `elif state == RPS:` block inside the main loop that reads the
   gesture, updates your game, and draws it.

Use the existing `TICTACTOE` block as a template — it shows how to read the
pinch, debounce it with `pinch_armed`, and draw an overlay.

### 5. Test it

```bash
pytest            # logic tests pass
python app.py     # try your game from the menu
```

---

## Pull request checklist

- [ ] `pytest` passes
- [ ] Game/logic code is separate from drawing code (and has a unit test)
- [ ] You can reach and play your mode from the menu (pinch **and** number key)
- [ ] You can return to the menu with `b` and close the window with `q` / `X`
- [ ] Code stays beginner-friendly and commented, matching the existing style

Then push your branch and open a pull request:

```bash
git push origin my-new-game
```

Describe what your game does and how to play it. That's it — thank you for
making GestureVision AI better!
