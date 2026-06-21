"""Tests for the presence state machine.

These run without a webcam by feeding the tracker synthetic observations and
controlling time via the injectable `now` argument.
"""

from datetime import datetime, timedelta

from gesturevision import config
from gesturevision.tracker import PresenceTracker
from gesturevision import logger as fv_logger


def _make_tracker(tmp_path, monkeypatch):
    """Tracker that logs to a temp CSV instead of the real data file."""
    log_path = tmp_path / "events.csv"
    monkeypatch.setattr(config, "LOG_FILE", log_path)
    monkeypatch.setattr(fv_logger.config, "LOG_FILE", log_path)
    return PresenceTracker(away_threshold=3.0), log_path


def test_starts_away(tmp_path, monkeypatch):
    tracker, _ = _make_tracker(tmp_path, monkeypatch)
    assert tracker.status == config.STATUS_AWAY


def test_face_makes_present(tmp_path, monkeypatch):
    tracker, _ = _make_tracker(tmp_path, monkeypatch)
    t0 = datetime(2026, 6, 21, 9, 0, 0)
    status = tracker.update(face_detected=True, now=t0)
    assert status == config.STATUS_PRESENT


def test_grace_period_before_away(tmp_path, monkeypatch):
    tracker, _ = _make_tracker(tmp_path, monkeypatch)
    t0 = datetime(2026, 6, 21, 9, 0, 0)
    tracker.update(face_detected=True, now=t0)

    # Face gone for 2s -> still PRESENT (under the 3s threshold).
    tracker.update(face_detected=False, now=t0 + timedelta(seconds=2))
    assert tracker.status == config.STATUS_PRESENT

    # Face gone for 4s total -> now AWAY.
    tracker.update(face_detected=False, now=t0 + timedelta(seconds=4))
    assert tracker.status == config.STATUS_AWAY


def test_interval_is_logged_on_switch(tmp_path, monkeypatch):
    tracker, log_path = _make_tracker(tmp_path, monkeypatch)
    t0 = datetime(2026, 6, 21, 9, 0, 0)
    tracker.update(face_detected=True, now=t0)             # AWAY -> PRESENT (logs AWAY)
    tracker.update(face_detected=False, now=t0 + timedelta(seconds=5))  # PRESENT -> AWAY (logs PRESENT)

    rows = fv_logger.read_events(log_path)
    statuses = [r["status"] for r in rows]
    assert config.STATUS_AWAY in statuses
    assert config.STATUS_PRESENT in statuses


def test_long_sitting_warning(tmp_path, monkeypatch):
    tracker, _ = _make_tracker(tmp_path, monkeypatch)
    t0 = datetime(2026, 6, 21, 9, 0, 0)
    tracker.update(face_detected=True, now=t0)
    later = t0 + timedelta(minutes=config.LONG_SITTING_WARNING_MINUTES + 1)
    assert tracker.long_sitting_warning(now=later) is True
