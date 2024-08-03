import streamlit as st
import pandas as pd
# import altair as alt
# from datetime import datetime, timedelta
import sqlite3

# custom project scripts
import vizDataJira
import vizJira

# Set the page config
st.set_page_config(
    page_title="Time to Market",
    page_icon=":bar_chart:",
    layout="wide"
)

st.title('Time to Market')

st.write('''
         Total time from Epic’s creation to its delivery to end users. Defines how long it takes to the team to deliver tangible value. 
         Time in days from the Epic's creation to "Closed" status, last 12 months avg. 
''')

df = vizDataJira.ttm_create_resolve_dates(epic_selection=True)
df2 = vizDataJira.ttm_first_inProgress_dates(epic_selection=True)
trans_df = vizDataJira.ttm_transform_and_join_dataframes(df, df2)

col1, col2 = st.columns(2)
with col1:
    vizJira.plot_lead_time_bar_chart(trans_df, 'Epic', 'Lead')

with col2:
    vizJira.display_kpi_cards(trans_df, 'Epic', 'Lead')

st.divider()