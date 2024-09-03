import streamlit as st
import pandas as pd
# import altair as alt
# from datetime import datetime, timedelta
# import sqlite3

# custom project scripts
import vizDataJira
import vizJira
import st_help

# Set the page config
st.set_page_config(
    page_title="Time to Market",
    page_icon=":bar_chart:",
    layout="wide"
)

## Throughput / Productivity

# Fetch the DataFrame
issues_df = vizDataJira.extract_released_data()
# Plot and display the charts
# chart_type = st.selectbox("Select Chart Type", ['story_points', 'num_stories', 'num_epics'], index=0)
chart = vizJira.plot_release_metrics(issues_df, 'story_points')
st.altair_chart(chart)

st.divider()

chart = vizJira.plot_release_metrics(issues_df, 'num_stories')
st.altair_chart(chart)

st.divider()

chart = vizJira.plot_release_metrics(issues_df, 'num_epics')
st.altair_chart(chart)

st.divider()

