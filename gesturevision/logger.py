"""Local CSV logging for GestureVision AI.

Privacy note: we ONLY store metadata - timestamp, status and duration.
No images, no video, nothing that leaves the machine.

CSV columns:
    start_time, end_time, status, duration_seconds
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from . import config

CSV_HEADER = ["start_time", "end_time", "status", "duration_seconds"]
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def _ensure_file(path: Path) -> None:
    """Create the CSV with a header row if it does not exist yet."""
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_HEADER)


def log_event(start: datetime, end: datetime, status: str,
              path: Path = None) -> None:
    """Append one completed PRESENT/AWAY interval to the log."""
    # Resolve the path at call time so config.LOG_FILE can be overridden
    # (e.g. in tests) after this module is imported.
    path = Path(path) if path is not None else config.LOG_FILE
    _ensure_file(path)
    duration = round((end - start).total_seconds(), 2)
    with path.open("a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            start.strftime(TIME_FORMAT),
            end.strftime(TIME_FORMAT),
            status,
            duration,
        ])


def read_events(path: Path = None) -> List[Dict]:
    """Read all logged events as a list of dicts. Empty list if no file."""
    path = Path(path) if path is not None else config.LOG_FILE
    if not Path(path).exists():
        return []
    with Path(path).open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
