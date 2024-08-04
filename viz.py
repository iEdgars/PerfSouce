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

for mt in ['Lead','Cycle']:
    for it in ['Epic', 'Story']:
        st.write(st_help.ttm_text(it, mt))

        if it == 'Epic':
            selection = True
        else:
            selection = False

        df = vizDataJira.ttm_create_resolve_dates(epic_selection=selection)
        df2 = vizDataJira.ttm_first_inProgress_dates(epic_selection=selection)
        trans_df = vizDataJira.ttm_transform_and_join_dataframes(df, df2)

        col1, col2 = st.columns([3,4])
        with col1:
            vizJira.plot_lead_cycle_bar_chart(trans_df, it, mt)

        with col2:
            vizJira.display_kpi_cards(trans_df, it, mt)

        st.divider()
