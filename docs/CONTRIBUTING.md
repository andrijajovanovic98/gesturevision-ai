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

- **`games/`** — one folder per game/mode. Each game is self-contained:
  - `games/1_pinch_playground/` — pinch practice mode
  - `games/2_tictactoe/` — `logic.py` (pure rules + minimax) and `__init__.py`
    (drawing). A clean example to copy.
- **`gesturevision/`** — shared building blocks used by every game:
  - `gestures.py` — pointing + pinch detection (your input device)
  - `ui.py` — the on-screen menu and its buttons
  - `detector.py`, `hands.py`, `tracker.py`, `stats.py`, `logger.py`, `config.py`
- **`app.py`** — the hub: one webcam loop that switches between *states* and
  calls into each game's folder.
- **`tests/`** — unit tests for the logic that doesn't need a webcam.

The golden rule: **keep game logic separate from webcam/drawing code**, exactly
like `games/2_tictactoe/logic.py` (pure rules) vs. its `__init__.py` (drawing).
This makes the logic easy to unit-test.

> Note: the game folders start with a number (`1_`, `2_`, ...) so they sort
> nicely. Because a module name can't start with a digit, the hub loads them
> with `importlib.import_module("games.2_tictactoe")` rather than a plain
> `import`. Just copy the pattern.

---

## Adding a new game to the menu — step by step

Let's say you want to add **"Rock Paper Scissors"** as game number 3.

### 1. Create your game folder

Make `games/3_rock_paper_scissors/` with two files:

- `logic.py` — the pure rules, **no OpenCV** (so it can be unit-tested):
  ```python
  class RockPaperScissors:
      def play(self, player_move: str) -> str:
          """Return 'win', 'lose' or 'draw' for the player's move."""
          ...
  ```
- `__init__.py` — exposes what the hub needs and does the drawing. Copy the
  shape of `games/2_tictactoe/__init__.py`:
  ```python
  from .logic import RockPaperScissors

  def draw(frame, game, ...):
      ...  # use cv2 + gesturevision.ui helpers
  ```

### 2. Add a unit test

Create `tests/test_rps.py` and test the rules without a webcam, like
`tests/test_tictactoe.py` does (it imports the logic via `importlib`). Required
for game logic.

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

1. Load your game near the other `importlib.import_module(...)` lines:
   ```python
   rps = importlib.import_module("games.3_rock_paper_scissors")
   ```
2. Add a state constant: `RPS = "rps"`.
3. In the menu handling, switch to `RPS` when the button is pinched (and, with
   the matching number key).
4. Add an `elif state == RPS:` block in the main loop that reads the gesture,
   updates your game, and calls `rps.draw(...)`.

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
