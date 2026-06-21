"""Aggregate logged events into daily statistics.

Used by both the Streamlit dashboard and the CSV export helper. Built on
pandas so it stays short and readable.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd

from . import config
from .logger import CSV_HEADER


def load_dataframe(path: Path = None) -> pd.DataFrame:
    """Load the event log as a typed DataFrame (empty frame if no data)."""
    path = Path(path) if path is not None else config.LOG_FILE
    if not Path(path).exists():
        return pd.DataFrame(columns=CSV_HEADER)

    df = pd.read_csv(path)
    if df.empty:
        return df

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce").fillna(0)
    df["day"] = df["start_time"].dt.date
    return df


def daily_summary(df: pd.DataFrame, day: Optional[date] = None) -> dict:
    """Return focus/away totals and break count for a single day."""
    day = day or date.today()
    summary = {
        "date": day,
        "focus_seconds": 0.0,
        "away_seconds": 0.0,
        "breaks": 0,
    }
    if df.empty:
        return summary

    today = df[df["day"] == day]
    if today.empty:
        return summary

    present = today[today["status"] == config.STATUS_PRESENT]
    away = today[today["status"] == config.STATUS_AWAY]

    summary["focus_seconds"] = float(present["duration_seconds"].sum())
    summary["away_seconds"] = float(away["duration_seconds"].sum())
    # Each AWAY interval counts as one break.
    summary["breaks"] = int(len(away))
    return summary


def format_duration(seconds: float) -> str:
    """Human-friendly H:MM:SS string."""
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}"


def export_daily_csv(out_path: Path, day: Optional[date] = None,
                     log_path: Path = None) -> Path:
    """Write a one-row daily summary CSV and return the path."""
    df = load_dataframe(log_path if log_path is not None else config.LOG_FILE)
    summary = daily_summary(df, day)
    out = pd.DataFrame([summary])
    out.to_csv(out_path, index=False)
    return out_path
