import streamlit as st
import pandas as pd
# import altair as alt
# from datetime import datetime, timedelta
import sqlite3

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

st.title('Time to Market')

t2m = ['Epic', 'Lead']
st.write(st_help.ttm_text(t2m[0], t2m[1]))

df = vizDataJira.ttm_create_resolve_dates(epic_selection=True)
df2 = vizDataJira.ttm_first_inProgress_dates(epic_selection=True)
trans_df = vizDataJira.ttm_transform_and_join_dataframes(df, df2)

col1, col2 = st.columns(2)
with col1:
    vizJira.plot_lead_cycle_bar_chart(trans_df, t2m[0], t2m[1])

with col2:
    vizJira.display_kpi_cards(trans_df, t2m[0], t2m[1])

st.divider()

t2m = ['Story', 'Lead']
st.write(st_help.ttm_text(t2m[0], t2m[1]))

df = vizDataJira.ttm_create_resolve_dates(epic_selection=False)
df2 = vizDataJira.ttm_first_inProgress_dates(epic_selection=False)
trans_df = vizDataJira.ttm_transform_and_join_dataframes(df, df2)

col1, col2 = st.columns(2)
with col1:
    vizJira.plot_lead_cycle_bar_chart(trans_df, t2m[0], t2m[1])

with col2:
    vizJira.display_kpi_cards(trans_df, t2m[0], t2m[1])

st.divider()


t2m = ['Story', 'Cycle']
st.write(st_help.ttm_text(t2m[0], t2m[1]))

df = vizDataJira.ttm_create_resolve_dates(epic_selection=False)
df2 = vizDataJira.ttm_first_inProgress_dates(epic_selection=False)
trans_df = vizDataJira.ttm_transform_and_join_dataframes(df, df2)

col1, col2 = st.columns(2)
with col1:
    vizJira.plot_lead_cycle_bar_chart(trans_df, t2m[0], t2m[1])

with col2:
    vizJira.display_kpi_cards(trans_df, t2m[0], t2m[1])

st.divider()