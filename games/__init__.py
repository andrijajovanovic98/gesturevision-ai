"""Game/mode plugins for GestureVision AI.

Each game lives in its own numbered sub-package (e.g. `1_pinch_playground`,
`2_tictactoe`) holding that game's logic and drawing. The hub (`app.py`)
imports each game and wires it into the menu.

To add a new game, create the next numbered folder (e.g. `3_my_game`) with an
`__init__.py` that exposes the functions the hub needs, then wire it up in
`app.py`. See docs/CONTRIBUTING.md for the full walkthrough.
"""
