import streamlit as st

# custom project scripts
import vizDataJira
import vizJira
import st_help

# Set the page config
st.set_page_config(
    page_title="Throughput / Productivity",
    page_icon="📶",
    layout="wide"
)

## Throughput / Productivity
st.title('Throughput / Productivity')

# Fetch the DataFrame
issues_df = vizDataJira.extract_released_data()

# Plot and display the charts
for chart_type in ['story_points', 'num_stories', 'num_epics']:
    chart, metrics_df, y_axis_column = vizJira.plot_release_metrics(issues_df, chart_type)

    col1, space, col2, space2 = st.columns([4,0.3,2.5, 0.3])


    col1.altair_chart(chart, use_container_width=True)
    # Display KPI cards
    with col2:
        unit = 'SP' if chart_type == 'story_points' else 'Stories' if chart_type == 'num_stories' else 'Epics'
        vizJira.display_release_kpi_cards(metrics_df, y_axis_column, unit)

    st.divider()
