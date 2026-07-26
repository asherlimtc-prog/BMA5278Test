
import streamlit as st                                 # brings in the tool for building the live dashboard page
import sqlite3                                          # brings in a tool for reading the stored records
import pandas as pd                                     # brings in a tool for working with tables of data

st.title("Prescription Renewal Oversight Dashboard")    # sets the page title a viewer sees

conn = sqlite3.connect("audit.db")                      # opens the saved record book from disk
df = pd.read_sql_query("SELECT * FROM decisions", conn) # pulls every logged decision into a table
df["timestamp"] = pd.to_datetime(df["timestamp"])       # converts the timestamp text into real dates

status_filter = st.multiselect("Filter by status", df["status"].unique(), default=df["status"].unique())   # lets the viewer pick which outcomes to see

# 1. Date-range filter so a regulator can inspect a specific week.
min_date, max_date = df["timestamp"].min().date(), df["timestamp"].max().date()   # find the earliest and latest dates logged
date_range = st.date_input("Date range", value=(min_date, max_date))   # lets the viewer pick a specific date range
if isinstance(date_range, tuple) and len(date_range) == 2:   # if the viewer picked a start and end date
    start_date, end_date = date_range
else:                                                    # otherwise, treat it as a single day
    start_date = end_date = date_range

filtered = df[                                           # narrow the table down to what the viewer asked for
    df["status"].isin(status_filter)
    & (df["timestamp"].dt.date >= start_date)
    & (df["timestamp"].dt.date <= end_date)
]

st.metric("Total requests logged", len(df))              # shows the all-time total request count
st.metric("Flagged for physician review", len(filtered[filtered["status"] != "processed"]))   # shows how many need human review

# 2. Visible callout when flagged requests exceed a threshold.
FLAG_THRESHOLD = 5                                       # how many flags are needed before we raise an alert
flagged_count = len(filtered[filtered["reason"].str.contains("controlled substance", na=False)])   # count controlled-substance flags
if flagged_count >= FLAG_THRESHOLD:                      # if we've crossed the alert threshold
    st.warning(f"{flagged_count} controlled-substance flags in this range - review recommended")   # show a warning banner

st.bar_chart(filtered["status"].value_counts())          # shows a simple bar chart of outcomes

# 3. Stretch goal: surface the reason text next to each flagged row.
st.subheader("Flagged requests")                         # a section heading for flagged requests
flagged_rows = filtered[filtered["status"] != "processed"][["patient_id", "status", "reason", "timestamp"]]   # pull just the flagged rows
st.dataframe(flagged_rows.sort_values("timestamp", ascending=False))   # display them, most recent first

st.subheader("All requests")                             # a section heading for every request
st.dataframe(filtered.sort_values("timestamp", ascending=False))   # display every request, most recent first
