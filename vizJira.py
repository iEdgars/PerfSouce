import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

def plot_lead_time_bar_chart(df):
    # Filter data to include only items resolved within the past 12 months
    today = datetime.today()
    twelve_months_ago = today - timedelta(days=365)
    df_filtered = df[df['resolved'] >= twelve_months_ago].copy()

    # Calculate monthly lead time based on resolved date
    df_filtered['resolved_month'] = df_filtered['resolved'].dt.to_period('M')
    monthly_lead_time = df_filtered.groupby('resolved_month')['lead_time'].mean().reset_index()
    monthly_lead_time['resolved_month'] = monthly_lead_time['resolved_month'].dt.to_timestamp()

    # Define thresholds
    def get_color(lead_time):
        if lead_time < 45:
            return 'Green'
        elif lead_time < 90:
            return 'Amber'
        else:
            return 'Red'

    monthly_lead_time['color'] = monthly_lead_time['lead_time'].apply(get_color)

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
        title='Epic Lead Time by Months, days'
    )

    st.altair_chart(chart, use_container_width=True)