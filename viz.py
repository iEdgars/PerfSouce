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

## Time to Market
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


## Time in Status By Month
st.title('Time in Status By Month')

# Get the data
tisc = vizDataJira.ttm_calculate_time_in_status()

col1, col2, col3, col4, col5 = st.columns(5)
# Toggle for status vs status category
toggle_status_category = col1.toggle("Show Status Category", value=False)

# Multiselect for issue types
issue_types = col4.multiselect("Select Issue Types", options=tisc['issue_type_name'].unique())

# Filter for status category
status_categories = tisc['category_name'].dropna().unique()
status_categories = [cat for cat in status_categories if cat != 'Done']
status_categories.insert(0, "All categories")
status_category_filter = col5.selectbox("Select Status Category", options=status_categories, index=0)

# Build and display the chart
with st.spinner('Recalculating chart...'):
    col1, col2 = st.columns([4,3])
    # Build and display the chart
    chart, avg_time_in_status = vizJira.build_time_in_status_chart(tisc, toggle_status_category, issue_types, status_category_filter)
    # chart = vizJira.build_time_in_status_chart(tisc, toggle_status_category, issue_types, status_category_filter)[0]
    col1.altair_chart(chart, use_container_width=True)

    # Display the average time in status table for "Story" and "Epic"
    st.subheader('Average Time in Status by Issue Type')
    filtered_avg_time_in_status = avg_time_in_status.loc[["Story", "Epic"]].round(1)
    filtered_avg_time_in_status.index.name = "Issue Type"
    st.dataframe(filtered_avg_time_in_status)

st.divider()

## Story Spillover
st.title('Story Spillover')
col1, col2, col3 = st.columns([5,3,2], vertical_alignment="bottom")
with st.spinner('Calculating Story Spillover...'):
    sprint_percentages, average_sprints = vizDataJira.calculate_spillover(257)
    bar_chart, pie_chart = vizJira.plot_spillover_chart(sprint_percentages)
    col1.altair_chart(bar_chart)
    col2.altair_chart(pie_chart)
    with col3:
        vizJira.display_average_sprints_spillover_kpi(average_sprints)