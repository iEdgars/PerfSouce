import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from typing import Literal

# Define thresholds
def get_color(the_time, issue_type, metric_type):
    RAG_scale = {
        'Epic_Lead': {
            'toGreen': 45,
            'toAmber': 90
        },
        'Story_Lead': {
            'toGreen': 30,
            'toAmber': 45
        },
        'Epic_Cycle': {
            'toGreen': 28,
            'toAmber': 42
        },
        'Story_Cycle': {
            'toGreen': 5,
            'toAmber': 14
        }
    }
    if the_time <= RAG_scale[f'{issue_type}_{metric_type}']['toGreen']:
        return ['Green','green']
    elif the_time <= RAG_scale[f'{issue_type}_{metric_type}']['toAmber']:
        return ['Amber','#FFA500']  # Amber
    else:
        return ['Red','red']

def plot_lead_time_bar_chart(
        df,
        issue_type: Literal['Epic','Story'],
        metric_type: Literal['Lead','Cycle']
        ):
    # Filter data to include only items resolved within the past 12 months
    today = datetime.today()
    twelve_months_ago = today - timedelta(days=365)
    df_filtered = df[df['resolved'] >= twelve_months_ago].copy()

    # Calculate monthly lead time based on resolved date
    df_filtered['resolved_month'] = df_filtered['resolved'].dt.to_period('M')
    monthly_lead_time = df_filtered.groupby('resolved_month')['lead_time'].mean().reset_index()
    monthly_lead_time['resolved_month'] = monthly_lead_time['resolved_month'].dt.to_timestamp()

    #Apply the get_color function
    monthly_lead_time['color'] = monthly_lead_time['lead_time'].apply(lambda x: get_color(x, issue_type, metric_type)[0])

    # Create Altair chart with explicit color scale
    color_scale = alt.Scale(
        domain=['Green', 'Amber', 'Red'],
        range=['green', '#FFA500', 'red']  # Green, Amber (Orange), Red
    )

    base = alt.Chart(monthly_lead_time).encode(
        x=alt.X('resolved_month:T', title='Month', axis=alt.Axis(labelAngle=-45, format='%b, %y')),  # Format month and year
        y=alt.Y('lead_time:Q', title='Days'),
        color=alt.Color('color:N', scale=color_scale, legend=alt.Legend(title="Lead Time Categories", orient='bottom'))
    )

    bars = base.mark_bar(size=20).encode(
        tooltip=['resolved_month:T', 'lead_time:Q']
    )

    trend = base.transform_regression('resolved_month', 'lead_time').mark_line(strokeDash=[5,5]).encode(
        color=alt.value('gray')
    )

    chart = (bars + trend).properties(
        title=f'{issue_type} Lead Time, days'
    )

    st.altair_chart(chart, use_container_width=True)

def display_kpi_cards(
        df,
        issue_type: Literal['Epic','Story'],
        metric_type: Literal['Lead','Cycle']
        ):
    # Filter data to include only items resolved within the past 12 months
    today = datetime.today()
    twelve_months_ago = today - timedelta(days=365)
    df_filtered = df[df['resolved'] >= twelve_months_ago].copy()

    # Calculate statistics
    average_lead_time = df_filtered['lead_time'].mean()
    deviation_lead_time = df_filtered['lead_time'].std()
    median_lead_time = df_filtered['lead_time'].median()
    max_lead_time = df_filtered['lead_time'].max()

    # Calculate trend (slope of the regression line)
    df_filtered['resolved_month'] = df_filtered['resolved'].dt.to_period('M')
    monthly_lead_time = df_filtered.groupby('resolved_month')['lead_time'].mean().reset_index()
    monthly_lead_time['resolved_month'] = monthly_lead_time['resolved_month'].dt.to_timestamp()

    x = np.arange(len(monthly_lead_time))
    y = monthly_lead_time['lead_time'].values
    slope, intercept = np.polyfit(x, y, 1)
    trend_per_month = slope

    average_color = get_color(average_lead_time, issue_type, metric_type)[1]

    # CSS for KPI cards
    card_css = """
    <style>
    .card {
        border: 1px solid #ccc;
        border-radius: 5px;
        padding: 10px;
        margin: 5px;
        text-align: center;
    }
    .card h3 {
        margin: 0;
        font-size: 1.2em;
    }
    .card h2 {
        margin: 0;
        font-size: 2em;
    }
    </style>
    """

    # Display KPI cards
    st.markdown(card_css, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f"<div class='card'><h3 style='color:{average_color};'>Average</h3><h2 style='color:{average_color};'>{average_lead_time:.1f}</h2><h5 style='color:{average_color};'> days</h5></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h3>Deviation</h3><h2>{deviation_lead_time:.1f}</h2><h5> days</h5></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><h3>Median</h3><h2>{median_lead_time:.1f}</h2><h5> days</h5></div>", unsafe_allow_html=True)
    col4.markdown(f"<div class='card'><h3>Maximum</h3><h2>{max_lead_time:.1f}</h2><h5> days</h5></div>", unsafe_allow_html=True)
    col1.markdown(f"<div class='card'><h3>Trend</h3><h2>{trend_per_month:.1f}</h2><h5> days per month</h5></div>", unsafe_allow_html=True)
