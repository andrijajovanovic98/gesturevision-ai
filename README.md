# GestureVision AI – Webcam Gesture Playground

A **privacy-first computer vision** app that turns your laptop webcam into an
interactive playground controlled entirely with your **hands**: count the
fingers you hold up, navigate a menu by pointing and pinching, and play a
gesture-controlled game against an AI. It also includes a presence/head-tracking
mode as a bonus. Everything runs **100% locally** — no webcam frames are ever
stored or sent to any external service.

<!-- Add a screenshot or GIF of the app here once recorded, e.g.:
![GestureVision AI demo](docs/demo.gif)
Tip: record the menu, finger counting, and a Tic-Tac-Toe game. -->
![GestureVision AI demo](docs/demo.png)

---

## What this project demonstrates

| Skill | Where it shows up |
|---|---|
| Real-time **computer vision** | Webcam capture, face & hand detection at interactive frame rates |
| **Hand-gesture interaction** | Pointing + pinch "click" used to drive a menu and a game |
| **Classic AI** | Unbeatable Tic-Tac-Toe opponent via the minimax algorithm |
| **Clean architecture** | Small, single-responsibility modules; CV layer separated from logic |
| **Testing** | Pure game/state logic unit-tested without a webcam |
| **Privacy-by-design** | Fully offline; stores only metadata, never images |

**Example real-world directions:** touchless gesture interfaces (kiosks,
accessibility, sterile environments), gesture-based controls and games, and —
via the bonus mode — privacy-respecting presence analytics or wellbeing
reminders.

---

## Tech stack

| Area | Technology |
|---|---|
| Language | **Python 3.9–3.11** |
| Computer vision | **OpenCV** (webcam capture & drawing) |
| Face / hand detection | **MediaPipe** (Face Detection + Hands, 21 landmarks) |
| Game AI | **Minimax** algorithm (pure Python, no dependencies) |
| Dashboard | **Streamlit** |
| Data analysis | **pandas** |
| Storage | Local **CSV** (metadata only — no images) |
| Testing | **pytest** |

Everything runs **locally** — no cloud services, no network calls.

---

## Features

### Hand-controlled hub (`app.py`)

A single entry point opens a webcam menu you navigate **with your hand** —
point with your index finger and **pinch** (touch thumb + index) to choose a
mode. Press `b` to return to the menu, `q` to quit.

### Gesture features (the main attraction)

- **Live finger counting** — hold up your hand(s) and it shows how many fingers
  you are raising (0–10 with two hands), with a hand skeleton overlay.
- **Pinch-to-click control** — point and pinch to drive the menu and the game,
  no keyboard or mouse needed.
- **Gesture Tic-Tac-Toe** — hover a cell and pinch to place your X. The
  opponent uses the **minimax** algorithm and is **unbeatable on Hard**
  (switch Easy/Hard with `e`/`h`, restart with `r`).

### Presence-tracking mode (bonus)

A secondary mode that shows your status from the webcam:
- **PRESENT** / **AWAY** real-time status with a short grace period.
- Basic **head direction**: looking left / right / center.
- "Too close to screen" warning and a long-sitting break reminder.
- Optionally logs intervals locally to `data/events.csv` (metadata only — no
  images), viewable in the included **Streamlit dashboard** with daily totals
  and CSV export.

---

## Project structure

```
gesturevision-ai/
├── focusvision/            # Core package (modular, well commented)
│   ├── __init__.py
│   ├── config.py           # All tunable settings in one place
│   ├── detector.py         # MediaPipe face detection wrapper (metadata only)
│   ├── hands.py            # MediaPipe Hands wrapper + finger counting
│   ├── gestures.py         # Pointing + pinch gesture recognition
│   ├── tictactoe.py        # Tic-Tac-Toe rules + minimax AI (no webcam)
│   ├── ui.py               # On-screen menu & pinch-clickable buttons
│   ├── tracker.py          # PRESENT/AWAY state machine + timing
│   ├── logger.py           # Local CSV logging (privacy-first)
│   └── stats.py            # Daily aggregation & CSV export (pandas)
├── tests/
│   ├── test_tracker.py     # Unit tests for the presence logic
│   └── test_tictactoe.py   # Unit tests for the game + minimax AI
├── data/                   # Local log lives here (git-ignored)
├── start.py                # One-click launcher (sets up venv, deps, runs app)
├── app.py                  # Unified hand-controlled hub (menu + modes)
├── run_tracker.py          # Presence-tracking mode only (standalone)
├── play_tictactoe.py       # Tic-Tac-Toe only (standalone)
├── dashboard.py            # Streamlit dashboard (read-only)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Installation & quick start

Requires **Python 3.9–3.11** (MediaPipe support is best in this range).
Works on **Windows, Linux and macOS**.

### One-click start (recommended)

```bash
git clone <your-repo-url>
cd gesturevision-ai
python start.py
```

`start.py` does everything for you: it creates the virtual environment if it's
missing, installs the dependencies the first time (and only re-installs them if
`requirements.txt` changes), then launches the app. No manual venv activation
needed — the same command works on every OS.

### Manual setup (optional)

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

---

## Usage

Run the unified hub (created automatically by `start.py`):

```bash
python app.py
```

In the menu, point with your index finger and **pinch** to select. Inside any
mode, press `b` to go back to the menu and `q` to quit.

You can also run each part standalone:

```bash
python run_tracker.py      # presence-tracking mode only
python play_tictactoe.py   # gesture Tic-Tac-Toe only
```

**View the dashboard** (in a second terminal):

```bash
streamlit run dashboard.py
```

The tracker writes intervals to `data/events.csv`; the dashboard reads from it.
You can run both at the same time and refresh the dashboard to see updates.

**Run the tests:**

```bash
pip install pytest
pytest
```

---

## How the detection logic works

1. **Capture** – OpenCV reads frames from the webcam in memory (BGR), which we
   convert to RGB for MediaPipe.
2. **Detect** – `MediaPipe Face Detection` (short-range model) returns whether
   a face is present, its bounding box, and key facial points. We immediately
   discard the pixels and keep only metadata.
3. **Decide presence** – A small **state machine** (`tracker.py`) converts the
   raw "face / no face" signal into stable **PRESENT** / **AWAY** intervals.
   A **grace period** (default 3s) prevents flicker when you blink or briefly
   turn away.
4. **Extra signals**
   - *Too close*: if the face box width exceeds ~45% of the frame width.
   - *Head direction*: compare the nose key-point position to the face box
     center → `left`, `right`, or `center`.
5. **Log** – Each completed interval is appended to `data/events.csv` as
   `start_time, end_time, status, duration_seconds`.
6. **Analyse** – `stats.py` aggregates the CSV with pandas into daily focus
   time, away time and break count for the dashboard and exports.

### Finger counting

`hands.py` uses `MediaPipe Hands`, which returns **21 landmarks per hand**
(knuckles and fingertips). To count raised fingers we use simple geometry:

- **Four fingers** (index, middle, ring, pinky): a finger is "up" if its
  fingertip is higher (smaller `y`) than the joint below it.
- **Thumb**: compared horizontally (`x`) instead, because it points sideways;
  the direction depends on whether MediaPipe labels the hand Left or Right.

The counts from each detected hand are summed (0–10 with two hands) and shown
in the overlay. As with everything else, only landmark coordinates are used —
never the image.

### Gesture control & the Tic-Tac-Toe AI

`gestures.py` turns hand landmarks into two simple controls:

- **Pointing** — the index fingertip is used as an on-screen cursor.
- **Pinch (click)** — when the thumb tip and index tip come close together
  (normalised distance below a threshold), it counts as a click. A small
  "re-arm" rule requires releasing the pinch before the next click registers,
  so one pinch never fires twice.

`tictactoe.py` holds the pure game rules plus a **minimax** AI. Minimax
explores every possible continuation of the game, scoring a win for the AI as
positive and a loss as negative, and assumes the human plays optimally too.
It then picks the move with the best guaranteed outcome — which makes the
**Hard** opponent unbeatable (you can only draw). The **Easy** mode just plays
a random legal move. This logic is fully unit-tested in `tests/test_tictactoe.py`
(including a check that the AI never loses across many simulated games).

---

## Privacy

This is the core design principle:

- All processing happens **on your device**.
- Only **metadata** is stored (timestamp, status, duration).
- **No** images or video are ever saved.
- **No** network calls — the app works fully offline.

The `data/` folder is git-ignored so your personal logs never get committed.

---

## Future improvements

- Hand-gesture recognition (thumbs up, peace, fist) built on the existing
  finger-counting landmarks — and gesture-based controls (e.g. show 5 fingers
  to pause tracking)
- Real posture estimation with **MediaPipe Pose** (shoulder/neck angle)
- Drowsiness / eye-aspect-ratio detection for fatigue alerts
- Optional **SQLite** backend for richer querying
- Weekly/monthly presence trends and summary charts
- Native desktop notifications for break reminders
- System-tray / background mode (no visible window)
- Multi-user profiles and team wellbeing dashboards (privacy-preserving)
- Dockerfile for reproducible setup

---

## License

MIT — free to use, learn from, and build on.
