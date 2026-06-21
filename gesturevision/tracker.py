"""Presence state machine for GestureVision AI.

The tracker turns a stream of "face / no face" observations into clean
PRESENT and AWAY intervals, applying a small grace period so a momentary
detection drop (blinking, turning your head) does not flip the status.

It also logs each completed interval and exposes the current live status.
"""

from datetime import datetime
from typing import Optional

from . import config
from .logger import log_event


class PresenceTracker:
    """State machine: observations in, logged PRESENT/AWAY intervals out."""

    def __init__(self, away_threshold: float = config.AWAY_THRESHOLD_SECONDS):
        self.away_threshold = away_threshold

        # Current confirmed status and when this interval started.
        self.status: str = config.STATUS_AWAY
        self._interval_start: datetime = datetime.now()

        # Timestamp of the last frame where a face WAS seen.
        self._last_seen: Optional[datetime] = None

        # Latest extra info for the dashboard / overlay.
        self.head_direction = "unknown"
        self.too_close = False

    def update(self, face_detected: bool, now: Optional[datetime] = None,
               head_direction: str = "unknown", too_close: bool = False) -> str:
        """Feed one observation; returns the confirmed current status.

        `now` is injectable so the logic can be unit-tested deterministically.
        """
        now = now or datetime.now()
        self.head_direction = head_direction
        self.too_close = too_close

        if face_detected:
            self._last_seen = now
            if self.status != config.STATUS_PRESENT:
                self._switch_to(config.STATUS_PRESENT, now)
        else:
            # No face right now. Only switch to AWAY once the grace period
            # since the last sighting has fully elapsed.
            elapsed = (now - self._last_seen).total_seconds() if self._last_seen else self.away_threshold + 1
            if self.status == config.STATUS_PRESENT and elapsed >= self.away_threshold:
                self._switch_to(config.STATUS_AWAY, now)

        return self.status

    def _switch_to(self, new_status: str, now: datetime) -> None:
        """Close the current interval, log it, and open a new one."""
        log_event(self._interval_start, now, self.status)
        self.status = new_status
        self._interval_start = now

    def current_interval_seconds(self, now: Optional[datetime] = None) -> float:
        """Seconds elapsed in the current (not-yet-logged) interval."""
        now = now or datetime.now()
        return (now - self._interval_start).total_seconds()

    def long_sitting_warning(self, now: Optional[datetime] = None) -> bool:
        """True if the user has been PRESENT longer than the configured limit."""
        if self.status != config.STATUS_PRESENT:
            return False
        minutes = self.current_interval_seconds(now) / 60.0
        return minutes >= config.LONG_SITTING_WARNING_MINUTES

    def flush(self, now: Optional[datetime] = None) -> None:
        """Log the in-progress interval (call on shutdown)."""
        now = now or datetime.now()
        log_event(self._interval_start, now, self.status)
        self._interval_start = now

    def start_session(self, now: Optional[datetime] = None) -> None:
        """Begin a fresh tracking session (call when entering Focus mode).

        Resets the status to AWAY and starts the interval clock now, so time
        spent in the menu or another mode is not counted or logged.
        """
        now = now or datetime.now()
        self.status = config.STATUS_AWAY
        self._interval_start = now
        self._last_seen = None
