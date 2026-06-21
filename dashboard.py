"""Streamlit dashboard for GestureVision AI.

Run with:

    streamlit run dashboard.py

Shows today's focus/away time, number of breaks, and a timeline of events,
all read from the local CSV log. No webcam access here - this is read-only.
"""

from datetime import date

import pandas as pd
import streamlit as st

from gesturevision import config
from gesturevision.stats import (
    load_dataframe,
    daily_summary,
    format_duration,
    export_daily_csv,
)

st.set_page_config(page_title="GestureVision AI", page_icon="🎯", layout="wide")

st.title("GestureVision AI – Focus Dashboard")
st.caption("Privacy-first webcam presence & focus tracking. All data stays on your machine.")

# --- Load data -------------------------------------------------------------
df = load_dataframe()

if df.empty:
    st.info(
        "No data yet. Start tracking by running `python run_tracker.py`, "
        "then refresh this page."
    )
    st.stop()

# --- Day selector ----------------------------------------------------------
available_days = sorted(df["day"].unique(), reverse=True)
selected_day = st.selectbox(
    "Select day",
    options=available_days,
    index=0,
    format_func=lambda d: d.strftime("%Y-%m-%d"),
)

summary = daily_summary(df, selected_day)

# --- Live-ish status (last logged event) -----------------------------------
last_event = df.sort_values("end_time").iloc[-1]
current_status = last_event["status"]
status_color = "🟢" if current_status == config.STATUS_PRESENT else "🔴"
st.subheader(f"Last known status: {status_color} {current_status}")

# --- Metrics ---------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Focus time", format_duration(summary["focus_seconds"]))
c2.metric("Away time", format_duration(summary["away_seconds"]))
c3.metric("Breaks", summary["breaks"])

# --- Focus vs away chart ---------------------------------------------------
st.subheader("Focus vs Away")
chart_df = pd.DataFrame(
    {
        "minutes": [
            summary["focus_seconds"] / 60.0,
            summary["away_seconds"] / 60.0,
        ]
    },
    index=["Focus", "Away"],
)
st.bar_chart(chart_df)

# --- Timeline table --------------------------------------------------------
st.subheader("Event timeline")
day_df = df[df["day"] == selected_day].copy()
day_df = day_df.sort_values("start_time")
day_df["duration"] = day_df["duration_seconds"].apply(format_duration)
st.dataframe(
    day_df[["start_time", "end_time", "status", "duration"]],
    width="stretch",
    hide_index=True,
)

# --- CSV export ------------------------------------------------------------
st.subheader("Export")
export_name = f"gesturevision_{selected_day}.csv"
if st.button("Prepare daily summary CSV"):
    out_path = config.DATA_DIR / export_name
    export_daily_csv(out_path, selected_day)
    with open(out_path, "rb") as f:
        st.download_button(
            "Download CSV",
            data=f.read(),
            file_name=export_name,
            mime="text/csv",
        )
