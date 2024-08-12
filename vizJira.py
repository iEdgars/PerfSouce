import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime, timedelta
from typing import Literal
import warnings

cacheTime = 600 # time to keep cache in seconds

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

@st.cache_data(ttl=cacheTime)
def plot_lead_cycle_bar_chart(
        df,
        issue_type: Literal['Epic','Story'],
        metric_type: Literal['Lead','Cycle']
        ):
    metric_low = metric_type.lower()

    # Filter data to include only items resolved within the past 12 months
    today = datetime.today()
    twelve_months_ago = today - timedelta(days=365)
    if metric_type == 'Lead':
        df_filtered = df[df['resolved'] >= twelve_months_ago].copy()
    elif metric_type == 'Cycle':
        df_filtered = df[(df['resolved'] >= twelve_months_ago) & (df['cycle_time'].notna())].copy()

    # Calculate monthly lead time based on resolved date
    df_filtered['resolved_month'] = df_filtered['resolved'].dt.to_period('M')
    monthly_time = df_filtered.groupby('resolved_month')[f'{metric_low}_time'].mean().reset_index()
    monthly_time['resolved_month'] = monthly_time['resolved_month'].dt.to_timestamp()

    #Apply the get_color function
    monthly_time['color'] = monthly_time[f'{metric_low}_time'].apply(lambda x: get_color(x, issue_type, metric_type)[0])
    
    # Create Altair chart with explicit color scale
    color_scale = alt.Scale(
        domain=['Green', 'Amber', 'Red'],
        range=['green', '#FFA500', 'red']  # Green, Amber (Orange), Red
    )

    base = alt.Chart(monthly_time).encode(
        x=alt.X('resolved_month:T', title='Month', axis=alt.Axis(labelAngle=-45, format='%b, %y')),  # Format month and year
        y=alt.Y(f'{metric_low}_time:Q', title='Days'),
        color=alt.Color('color:N', scale=color_scale, legend=alt.Legend(title=f'{metric_type} Time Categories', orient='bottom'))
    )

    bars = base.mark_bar(size=20).encode(
        tooltip=['resolved_month:T', f'{metric_low}_time:Q']
    )

    trend = base.transform_regression('resolved_month', f'{metric_low}_time').mark_line(strokeDash=[5,5]).encode(
        color=alt.value('gray')
    )

    chart = (bars + trend).properties(
        title=f'{issue_type} {metric_type} Time, days'
    )

    st.altair_chart(chart, use_container_width=True)

@st.cache_data(ttl=cacheTime)
def display_kpi_cards(
        df,
        issue_type: Literal['Epic','Story'],
        metric_type: Literal['Lead','Cycle']
        ):
    metric_low = metric_type.lower()

    # Filter data to include only items resolved within the past 12 months
    today = datetime.today()
    twelve_months_ago = today - timedelta(days=365)
    if metric_type == 'Lead':
        df_filtered = df[df['resolved'] >= twelve_months_ago].copy()
    elif metric_type == 'Cycle':
        df_filtered = df[(df['resolved'] >= twelve_months_ago) & (df['cycle_time'].notna())].copy()

    # Calculate statistics
    average_time = df_filtered[f'{metric_low}_time'].mean()
    deviation_time = df_filtered[f'{metric_low}_time'].std()
    median_time = df_filtered[f'{metric_low}_time'].median()
    max_time = df_filtered[f'{metric_low}_time'].max()

    # Calculate trend (slope of the regression line)
    df_filtered['resolved_month'] = df_filtered['resolved'].dt.to_period('M')
    monthly_time = df_filtered.groupby('resolved_month')[f'{metric_low}_time'].mean().reset_index()
    monthly_time['resolved_month'] = monthly_time['resolved_month'].dt.to_timestamp()

    x = np.arange(len(monthly_time))
    y = monthly_time[f'{metric_low}_time'].values
    y = y.astype(float)
    slope, intercept = np.polyfit(x, y, 1)
    trend_per_month = slope

    average_color = get_color(average_time, issue_type, metric_type)[1]

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

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div class='card'><h3>Average</h3><h2 style='color:{average_color};'>{average_time:.1f}</h2><h5 style='color:{average_color};'> days</h5></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h3>Deviation</h3><h2>{deviation_time:.1f}</h2><h5> days</h5></div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='card'><h3>Median</h3><h2>{median_time:.1f}</h2><h5> days</h5></div>", unsafe_allow_html=True)
    col1.markdown(f"<div class='card'><h3>Maximum</h3><h2>{max_time:.1f}</h2><h5> days</h5></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='card'><h3>Trend</h3><h2>{trend_per_month:.1f}</h2><h5> days per month</h5></div>", unsafe_allow_html=True)

# Function to build the monthly "Time In Status" bar chart
@st.cache_data(ttl=cacheTime, show_spinner=False)
def build_time_in_status_chart(df, toggle_status_category, issue_types, status_category_filter):
    # Filter the DataFrame by issue type
    if issue_types:
        df = df[df['issue_type_name'].isin(issue_types)]

    # Filter the DataFrame by status category
    if status_category_filter and status_category_filter != "All categories":
        df = df[df['category_name'] == status_category_filter]

    # Calculate the start date for the past 12 full months
    today = pd.Timestamp.now(tz='UTC')
    start_date = (today.replace(day=1) - pd.DateOffset(months=12)).replace(day=1)

    # Filter the DataFrame to include records between start_date and today
    filtered_df = df[(df['change_date_time'] >= start_date) & (df['change_date_time'] <= today)]

    # Include the latest record before the start date if the change was not to "Done"
    before_start_date_df = df[df['change_date_time'] < start_date]
    latest_before_start_date = before_start_date_df.groupby('issue_id').last().reset_index()
    latest_before_start_date = latest_before_start_date[latest_before_start_date['category_name'] != 'Done']

    # Combine the filtered DataFrame with the latest records before the start date
    combined_df = pd.concat([filtered_df, latest_before_start_date]).drop_duplicates().reset_index(drop=True)

    # Create a DataFrame to store the results
    results = []

    # Iterate through each issue
    for issue_id, issue_df in combined_df.groupby('issue_id'):
        issue_df = issue_df.sort_values(by='change_date_time').reset_index(drop=True)
        for i in range(len(issue_df)):
            start_date = issue_df.loc[i, 'change_date_time']
            if i + 1 < len(issue_df):
                end_date = issue_df.loc[i + 1, 'change_date_time']
            else:
                end_date = pd.Timestamp.now(tz='UTC')
            
            status = issue_df.loc[i, 'value_to']

            # Calculate time in status for each month
            while start_date < end_date:
                month_start = start_date.replace(day=1)
                month_end = (month_start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
                if end_date < month_end:
                    month_end = end_date

                hours_in_status = (month_end - start_date).total_seconds() / 3600.0
                results.append({
                    'issue_id': issue_id,
                    'status': status,
                    'issue_type_name': issue_df.loc[i, 'issue_type_name'],
                    'month': month_start,
                    'hours_in_status': hours_in_status
                })

                start_date = month_end + pd.DateOffset(days=1)

    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

    # Create a DataFrame with unique value_to and category_name pairs
    unique_status_category = df[['value_to', 'category_name']].drop_duplicates().rename(columns={'value_to': 'status'})

    # Join results_df with unique_status_category to get the correct category_name
    results_df = results_df.merge(unique_status_category, on='status', how='left')

    # Rename category_name to category
    results_df = results_df.rename(columns={'category_name': 'category'})

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        # Ensure the month column is in the correct format
        results_df['month'] = pd.to_datetime(results_df['month'], errors='coerce').dt.to_period('M').dt.to_timestamp()

    # Filter to include only the past 12 months
    last_12_months = pd.date_range(end=datetime.now(), periods=12, freq='M').to_period('M').to_timestamp()
    results_df = results_df[results_df['month'].isin(last_12_months)]

    # Filter out items in the "Done" status group
    results_df = results_df[(results_df['category'] != 'Done') & (results_df['category'].notna())]

    # Aggregate the data by issue, status, and month to calculate the total hours in status
    if toggle_status_category:
        results_df = results_df.groupby(['issue_id', 'category', 'month', 'issue_type_name'])['hours_in_status'].sum().reset_index()
        # Convert hours to days with decimals
        results_df['days_in_status'] = results_df['hours_in_status'] / 24.0
        # Aggregate the data by month and category to calculate the average time in status
        monthly_df = results_df.groupby(['month', 'category'])['days_in_status'].mean().reset_index()
        color_field = 'category'
    else:
        results_df = results_df.groupby(['issue_id', 'status', 'month', 'issue_type_name'])['hours_in_status'].sum().reset_index()
        # Convert hours to days with decimals
        results_df['days_in_status'] = results_df['hours_in_status'] / 24.0
        # Aggregate the data by month and status to calculate the average time in status
        monthly_df = results_df.groupby(['month', 'status'])['days_in_status'].mean().reset_index()
        color_field = 'status'

    # Create the bar chart with wider bars
    chart = alt.Chart(monthly_df).mark_bar(size=30).encode(
        x=alt.X('month:T', title='Month', axis=alt.Axis(format='%b, %y')),
        y=alt.Y('mean(days_in_status):Q', title='Average Days'),
        color=f'{color_field}:N',
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip(f'{color_field}:N', title='Status' if not toggle_status_category else 'Category'),
            alt.Tooltip('mean(days_in_status):Q', title='Average Days')
        ]
    ).properties(
        title='Average Time in Status By Month',
        width=800,
        height=400
    )

    # Calculate the average time in status for each issue type
    avg_time_in_status = results_df.groupby(['issue_type_name', color_field])['days_in_status'].mean().unstack().fillna(0)

    return chart, avg_time_in_status

@st.cache_data(ttl=cacheTime, show_spinner=False)
def build_time_in_status_chart__avg_time_in_status_adj(df, toggle_status_category, issue_types, status_category_filter):
## This funtion should should have adjustment, not to depend on filters, however, comparing to  build_time_in_status_chart(), when nothing is filtered, values are slightly off.
    # Calculate the start date for the past 12 full months
    today = pd.Timestamp.now(tz='UTC')
    start_date = (today.replace(day=1) - pd.DateOffset(months=12)).replace(day=1)

    # Filter the DataFrame to include records between start_date and today
    filtered_df = df[(df['change_date_time'] >= start_date) & (df['change_date_time'] <= today)]

    # Include the latest record before the start date if the change was not to "Done"
    before_start_date_df = df[df['change_date_time'] < start_date]
    latest_before_start_date = before_start_date_df.groupby('issue_id').last().reset_index()
    latest_before_start_date = latest_before_start_date[latest_before_start_date['category_name'] != 'Done']

    # Combine the filtered DataFrame with the latest records before the start date
    combined_df = pd.concat([filtered_df, latest_before_start_date]).drop_duplicates().reset_index(drop=True)

    # Create a DataFrame to store the results
    results = []

    # Iterate through each issue
    for issue_id, issue_df in combined_df.groupby('issue_id'):
        issue_df = issue_df.sort_values(by='change_date_time').reset_index(drop=True)
        for i in range(len(issue_df)):
            start_date = issue_df.loc[i, 'change_date_time']
            if i + 1 < len(issue_df):
                end_date = issue_df.loc[i + 1, 'change_date_time']
            else:
                end_date = pd.Timestamp.now(tz='UTC')
            
            status = issue_df.loc[i, 'value_to']

            # Calculate time in status for each month
            while start_date < end_date:
                month_start = start_date.replace(day=1)
                month_end = (month_start + pd.DateOffset(months=1)) - pd.DateOffset(days=1)
                if end_date < month_end:
                    month_end = end_date

                hours_in_status = (month_end - start_date).total_seconds() / 3600.0
                results.append({
                    'issue_id': issue_id,
                    'status': status,
                    'issue_type_name': issue_df.loc[i, 'issue_type_name'],
                    'month': month_start,
                    'hours_in_status': hours_in_status
                })

                start_date = month_end + pd.DateOffset(days=1)

    # Create a DataFrame from the results
    results_df = pd.DataFrame(results)

    # Create a DataFrame with unique value_to and category_name pairs
    unique_status_category = df[['value_to', 'category_name']].drop_duplicates().rename(columns={'value_to': 'status'})

    # Join results_df with unique_status_category to get the correct category_name
    results_df = results_df.merge(unique_status_category, on='status', how='left')

    # Rename category_name to category
    results_df = results_df.rename(columns={'category_name': 'category'})

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        # Ensure the month column is in the correct format
        results_df['month'] = pd.to_datetime(results_df['month'], errors='coerce').dt.to_period('M').dt.to_timestamp()

    # Filter to include only the past 12 months
    last_12_months = pd.date_range(end=datetime.now(), periods=12, freq='M').to_period('M').to_timestamp()
    results_df = results_df[results_df['month'].isin(last_12_months)]

    # Filter out items in the "Done" status group
    results_df = results_df[(results_df['category'] != 'Done') & (results_df['category'].notna())]

    # DF for calculation of average time in status for each issue type
    results_df_unfilter = results_df.copy()
    # Calculate the average time in status for each issue type (before applying filters)
    results_df_unfilter['days_in_status'] = results_df_unfilter['hours_in_status'] / 24.0
    if toggle_status_category:
        avg_time_in_status = results_df_unfilter.groupby(['issue_type_name', 'category'])['days_in_status'].mean().unstack().fillna(0)
    else:
        avg_time_in_status = results_df_unfilter.groupby(['issue_type_name', 'status'])['days_in_status'].mean().unstack().fillna(0)

    # Apply filters for chart
    if issue_types:
        results_df = results_df[results_df['issue_type_name'].isin(issue_types)]
    if status_category_filter and status_category_filter != "All categories":
        results_df = results_df[results_df['category'] == status_category_filter]

    # Aggregate the data by issue, status, and month to calculate the total hours in status
    if toggle_status_category:
        results_df = results_df.groupby(['issue_id', 'category', 'month', 'issue_type_name'])['hours_in_status'].sum().reset_index()
        # Convert hours to days with decimals
        results_df['days_in_status'] = results_df['hours_in_status'] / 24.0
        # Aggregate the data by month and category to calculate the average time in status
        monthly_df = results_df.groupby(['month', 'category'])['days_in_status'].mean().reset_index()
        color_field = 'category'
    else:
        results_df = results_df.groupby(['issue_id', 'status', 'month', 'issue_type_name'])['hours_in_status'].sum().reset_index()
        # Convert hours to days with decimals
        results_df['days_in_status'] = results_df['hours_in_status'] / 24.0
        # Aggregate the data by month and status to calculate the average time in status
        monthly_df = results_df.groupby(['month', 'status'])['days_in_status'].mean().reset_index()
        color_field = 'status'

    # Create the bar chart with wider bars
    chart = alt.Chart(monthly_df).mark_bar(size=30).encode(
        x=alt.X('month:T', title='Month', axis=alt.Axis(format='%b, %y')),
        y=alt.Y('mean(days_in_status):Q', title='Average Days'),
        color=f'{color_field}:N',
        tooltip=[
            alt.Tooltip('month:T', title='Month'),
            alt.Tooltip(f'{color_field}:N', title='Status' if not toggle_status_category else 'Category'),
            alt.Tooltip('mean(days_in_status):Q', title='Average Days')
        ]
    ).properties(
        title='Average Time in Status By Month',
        width=800,
        height=400
    )

    return chart, avg_time_in_status