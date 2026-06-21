"""Shared UI helpers: an on-screen menu and pinch-clickable buttons.

Used by app.py to let the user pick a mode with their hand (point + pinch),
on top of the live webcam feed. Pure drawing + hit-testing; no camera or
MediaPipe code lives here.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2

from . import config

WHITE = (255, 255, 255)
GREY = (120, 120, 120)
DARK = (40, 40, 40)
HIGHLIGHT = (0, 170, 0)
CYAN = (255, 255, 0)
YELLOW = (0, 215, 255)


@dataclass
class Button:
    """A rectangular, pinch-clickable menu button."""

    label: str
    action: str            # identifier returned when clicked
    x: int
    y: int
    w: int
    h: int

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def center(self) -> Tuple[int, int]:
        return self.x + self.w // 2, self.y + self.h // 2


def build_menu_buttons() -> List[Button]:
    """Vertically stacked, centred menu buttons for the available modes."""
    btn_w, btn_h = 380, 60
    gap = 24
    x = (config.FRAME_WIDTH - btn_w) // 2
    first_y = 140

    items = [
        ("1. Focus Tracker", "focus"),
        ("2. Tic-Tac-Toe (hand)", "tictactoe"),
        ("3. Quit", "quit"),
    ]
    buttons = []
    for i, (label, action) in enumerate(items):
        y = first_y + i * (btn_h + gap)
        buttons.append(Button(label, action, x, y, btn_w, btn_h))
    return buttons


def draw_menu(frame, buttons: List[Button], hover: Optional[Button],
              pinching: bool) -> None:
    """Render the menu title and buttons over the (live) frame."""
    # Dim the camera feed a little so the menu pops.
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (config.FRAME_WIDTH, config.FRAME_HEIGHT),
                  (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    cv2.putText(frame, "GestureVision AI", (config.FRAME_WIDTH // 2 - 185, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, WHITE, 3)
    cv2.putText(frame, "Point and pinch to choose", (config.FRAME_WIDTH // 2 - 165, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, YELLOW, 1)

    for btn in buttons:
        is_hover = hover is btn
        fill = HIGHLIGHT if is_hover else DARK
        cv2.rectangle(frame, (btn.x, btn.y), (btn.x + btn.w, btn.y + btn.h),
                      fill, -1)
        cv2.rectangle(frame, (btn.x, btn.y), (btn.x + btn.w, btn.y + btn.h),
                      WHITE, 2)
        cv2.putText(frame, btn.label, (btn.x + 20, btn.y + 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2)


def draw_cursor(frame, px: int, py: int, pinching: bool) -> None:
    """Draw the fingertip cursor dot (cyan while pinching)."""
    cv2.circle(frame, (px, py), 10, CYAN if pinching else WHITE, -1)


def draw_back_hint(frame) -> None:
    """Small hint shown inside a mode for returning to the menu."""
    cv2.putText(frame, "'b' = menu   'q' = quit",
                (10, config.FRAME_HEIGHT - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREY, 1)
