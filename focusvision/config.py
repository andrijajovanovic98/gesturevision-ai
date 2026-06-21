"""Central configuration for GestureVision AI.

Keeping all the tunable numbers in one place makes the project easy to read
and lets beginners experiment without digging through the logic files.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------
# Project root = the folder that contains the `focusvision` package.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LOG_FILE = DATA_DIR / "events.csv"

# Make sure the data folder always exists.
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Webcam ----------------------------------------------------------------
CAMERA_INDEX = 0          # 0 = default built-in webcam
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# --- Detection logic -------------------------------------------------------
# How many seconds without a face before we switch PRESENT -> AWAY.
AWAY_THRESHOLD_SECONDS = 3.0

# MediaPipe face detection confidence (0.0 - 1.0).
MIN_DETECTION_CONFIDENCE = 0.6

# --- Posture / proximity (nice-to-have) ------------------------------------
# If the detected face box is wider than this fraction of the frame width,
# the user is probably sitting too close to the screen.
TOO_CLOSE_FACE_RATIO = 0.45

# Horizontal offset of the nose relative to the face box center that counts
# as "looking left/right" instead of "center". Expressed as a fraction of the
# face box width.
HEAD_DIRECTION_THRESHOLD = 0.12

# --- Finger counting (fun extra) -------------------------------------------
# Show how many fingers you are holding up in the tracker overlay.
ENABLE_FINGER_COUNTING = True
MAX_HANDS = 2  # count up to two hands (0-10 fingers)

# --- Wellbeing -------------------------------------------------------------
# Warn the user after this many minutes of continuous sitting (present time).
LONG_SITTING_WARNING_MINUTES = 45

# Statuses used across the app.
STATUS_PRESENT = "PRESENT"
STATUS_AWAY = "AWAY"
