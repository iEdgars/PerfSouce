import pandas as pd
import sqlite3
import streamlit as st
import gc
from datetime import datetime


cacheTime = 900 # time to keep cache in seconds

# Function to get Lead time data
@st.cache_data(ttl=cacheTime)
def ttm_create_resolve_dates(epic_selection=False):
    # Connect to SQLite database
    conn = sqlite3.connect('jira_projects.db')
    
    # Define the query
    query = '''
    SELECT the_project, jira_project, issue_id, key, field, field_value, issue_type_name
    FROM issues
    WHERE field IN('resolutiondate', 'created')
        AND issue_status_cat_name = 'Done'
        AND issue_status <> 'Rejected'
        AND field_value <> 'None'
    '''
    
    # Modify query based on epic_selection
    if epic_selection:
        query += " AND issue_type_name = 'Epic'"
    else:
        query += " AND issue_type_name <> 'Epic'"
    
    # Execute the query and load into a DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Close the connection
    conn.close()
    
    return df

# Function to get fist InProgress for Cycle time data
@st.cache_data(ttl=cacheTime)
def ttm_first_inProgress_dates(epic_selection=False):
    # Connect to SQLite database
    conn = sqlite3.connect('jira_projects.db')
    
    # Define the query
    query = '''
    SELECT ic.the_project, ic.jira_project, ic.issue_id, ic."key", MIN(ic.change_date_time) AS first_in_progress
    FROM issue_changelog ic
    JOIN project_issues_and_statuses pis ON ic.value_to = pis.untranslated_name
    WHERE ic.issue_status_cat_name = 'Done'
        AND ic.issue_status <> 'Rejected'
        AND ic.field = 'status'
        AND pis.category_name = 'In Progress'
    '''
    
    # Modify query based on epic_selection
    if epic_selection:
        query += " AND ic.issue_type_name = 'Epic'"
    else:
        query += " AND ic.issue_type_name <> 'Epic'"
    
    query += " GROUP BY ic.the_project, ic.jira_project, ic.issue_id, ic.\"key\""
    
    # Execute the query and load into a DataFrame
    df = pd.read_sql_query(query, conn)
    
    # Close the connection
    conn.close()
    
    return df

# Combined function to transform and join dataframes
@st.cache_data(ttl=cacheTime)
def ttm_transform_and_join_dataframes(df_issues, df_first_in_progress):
    # Pivot the DataFrame to get 'created' and 'resolutiondate' in columns
    df_pivot = df_issues.pivot(index=['the_project', 'jira_project', 'issue_id', 'key', 'issue_type_name'], 
                               columns='field', values='field_value').reset_index()
    
    # Rename columns for clarity
    df_pivot.columns.name = None
    df_pivot.rename(columns={'created': 'created', 'resolutiondate': 'resolved'}, inplace=True)
    
    # Extract the date part from the datetime string
    df_pivot['created'] = df_pivot['created'].str[:10]
    df_pivot['resolved'] = df_pivot['resolved'].str[:10]
    df_first_in_progress['first_in_progress'] = df_first_in_progress['first_in_progress'].str[:10]
    
    # Convert date columns to datetime
    df_pivot['created'] = pd.to_datetime(df_pivot['created'], errors='coerce')
    df_pivot['resolved'] = pd.to_datetime(df_pivot['resolved'], errors='coerce')
    df_first_in_progress['first_in_progress'] = pd.to_datetime(df_first_in_progress['first_in_progress'], errors='coerce')
    
    # Filter out rows where 'resolved' is NaT (Not a Time)
    df_pivot = df_pivot.dropna(subset=['resolved'])
    
    # Calculate lead_time
    df_pivot['lead_time'] = (df_pivot['resolved'] - df_pivot['created']).dt.days
    
    # Merge the dataframes on common columns
    merged_df = pd.merge(df_pivot, df_first_in_progress, on=['the_project', 'jira_project', 'issue_id', 'key'], how='left')
    
    # Calculate cycle_time
    merged_df['cycle_time'] = (merged_df['resolved'] - merged_df['first_in_progress']).dt.days
    
    # Convert cycle_time to integer, handling NaN values
    merged_df['cycle_time'] = merged_df['cycle_time'].fillna(-1).astype(int).replace(-1, pd.NA)
    
    # Cleaning up
    # Clear unnecessary DataFrames
    del df_pivot
    del df_first_in_progress
    # Run garbage collector to free up memory
    gc.collect()

    return merged_df

# Funtion to get latest status
@st.cache_data(ttl=cacheTime)
def ttm_calculate_time_in_status():

    # Connect to SQLite database
    conn = sqlite3.connect('jira_projects.db')

    # Load data into DataFrames
    issues = '''
    SELECT the_project, jira_project, issue_id, "key", field, field_value, issue_type_name, issue_status
    FROM issues
    WHERE field = 'created'
    '''

    changelog = '''
    SELECT the_project, jira_project, issue_id, "key", change_date_time, field, value_from, value_to, issue_type_name
    FROM issue_changelog ic
    WHERE field = 'status'
    '''

    status_category = '''
    SELECT the_project, jira_project, status_name, untranslated_name, category_name
    FROM project_issues_and_statuses
    GROUP BY the_project, jira_project, status_name, untranslated_name, category_name
    '''

    issues_df = pd.read_sql_query(issues, conn)
    changelog_df = pd.read_sql_query(changelog, conn)
    statusCat_df = pd.read_sql_query(status_category, conn)

    # Close the connection
    conn.close()

    # Sort values to ensure correct time difference calculation
    changelog_df = changelog_df.sort_values(by=['issue_id', 'change_date_time'])

    # Get the first status change for each issue key
    first_status_changes = changelog_df.groupby('issue_id').first().reset_index()
    # Move value_from to value_to
    first_status_changes['value_to'] = first_status_changes['value_from']
    # Replace value_from with 'Created'
    first_status_changes['value_from'] = 'Created'

    # Replace change_date_time with field_value from issues_df
    issues_df = issues_df.rename(columns={'field_value': 'created_date'})
    first_status_changes = pd.merge(first_status_changes, issues_df[['issue_id', 'created_date']], on='issue_id', how='left')
    first_status_changes['change_date_time'] = first_status_changes['created_date']
    first_status_changes = first_status_changes.drop(columns=['created_date']) # Drop the temporary 'created_date' column

    # Get the last status change for each issue key
    last_status_changes = changelog_df.groupby('issue_id').last().reset_index()
    # Set value_from and value_to to the latest status
    last_status_changes['value_from'] = last_status_changes['value_to']
    # Set change_date_time to the current date and time
    last_status_changes['change_date_time'] = pd.Timestamp.now(tz='UTC')

    # Append the modified first_status_changes and last_status_changes to changelog_df
    combined_df = pd.concat([first_status_changes, changelog_df, last_status_changes])

    # Convert change_date_time to datetime format
    combined_df['change_date_time'] = pd.to_datetime(combined_df['change_date_time'], errors='coerce', utc=True)

    # Sort the combined DataFrame by issue_id and change_date_time
    combined_df = combined_df.sort_values(by=['issue_id', 'change_date_time']).reset_index(drop=True)

    # Calculate time in status
    combined_df['time_in_status'] = combined_df.groupby('issue_id')['change_date_time'].diff().dt.total_seconds() / 86400.0

    # Fill the first row of each group with 0
    combined_df['time_in_status'] = combined_df['time_in_status'].fillna(0)

    # Join statusCat_df to combined_df on value_to = untranslated_name
    combined_df = pd.merge(combined_df, statusCat_df[['untranslated_name', 'category_name']], 
                        left_on='value_to', right_on='untranslated_name', how='left')
    # Drop the temporary 'untranslated_name' column
    combined_df = combined_df.drop(columns=['untranslated_name'])

    # Clear unnecessary DataFrames
    del issues_df
    del changelog_df
    del first_status_changes
    del last_status_changes
    del statusCat_df

    # Run garbage collector to free up memory
    gc.collect()

    return combined_df

# Funtion to extract and pre-manipulate data for spillover
@st.cache_data(ttl=cacheTime, show_spinner=False)
def extract_spillover_data(board):
    conn = sqlite3.connect('jira_projects.db')

    sprints_query = '''
    SELECT *
    FROM sprints
    WHERE state = 'closed'
    ORDER BY board_id, id
    '''
    issues_query = '''
    SELECT *
    FROM issues
    WHERE issue_status_cat_name = 'Done'
    AND issue_status <> 'Rejected'
    AND issue_type_name <> 'Epic'
    AND field = 'customfield_10010'
    '''
    changelog_query = '''
    SELECT *
    FROM issue_changelog
    WHERE issue_status_cat_name = 'Done'
    AND issue_status <> 'Rejected'
    AND issue_type_name <> 'Epic'
    AND field LIKE 'Sprint'
    '''

    sprints_df = pd.read_sql_query(sprints_query, conn)
    issues_df = pd.read_sql_query(issues_query, conn)
    changelog_df = pd.read_sql_query(changelog_query, conn)

    conn.close()

    # Convert id to string
    sprints_df['id'] = sprints_df['id'].astype(str)
    # Ensure value_to in changelog_df is of type string
    changelog_df['value_to'] = changelog_df['value_to'].astype(str)

    # Convert to datetime
    sprints_df['end_date'] = pd.to_datetime(sprints_df['end_date'], errors='coerce')
    sprints_df['start_date'] = pd.to_datetime(sprints_df['start_date'], errors='coerce')

    sprints_df = sprints_df[sprints_df['board_id'] == board]

    # Sort by end_date and select the last 12 sprints
    latest_sprints_df = sprints_df.sort_values(by='end_date', ascending=False).head(12)
    
    # Limiting issues_df to only items that has no Sprint change
    issues_df = issues_df[~issues_df['issue_id'].isin(changelog_df['issue_id'])]
    # Limiting issues_df to only items in latest 12 sprints
    issues_df = issues_df[issues_df['field_value'].astype(str).isin(latest_sprints_df['id'])]

    return sprints_df, issues_df, changelog_df, latest_sprints_df

# Function to determine if value_to was equal to id during the period for calculate_spillover funtion
# @st.cache_data(ttl=cacheTime, show_spinner=False) #! Do not cache as it add's 2 minutes to this funtion.
def determine_value_to__for_calculate_spillover(row, df):
    issue_id = row['issue_id']
    start_date = row['start_date']
    end_date = row['end_date']
    id_value = row['id']
    
    # Filter for the same issue_id and changes before the start_date
    filtered_df_before_start = df[(df['issue_id'] == issue_id) & (df['change_date_time'] < start_date)]
    
    # Get the last value_to before the start_date
    if not filtered_df_before_start.empty:
        last_value_to = filtered_df_before_start.iloc[-1]['value_to']
    else:
        last_value_to = None
    
    # Check if the last value_to is equal to the id_value
    if last_value_to == id_value:
        return True
    
    # Additionally, check if any value_to is assigned within the start_date and end_date
    filtered_df_within_period = df[(df['issue_id'] == issue_id) & (start_date <= df['change_date_time']) & (df['change_date_time'] <= end_date)]
    
    if not filtered_df_within_period.empty:
        for _, period_row in filtered_df_within_period.iterrows():
            if period_row['value_to'] == id_value:
                return True
    
    return False

@st.cache_data(ttl=cacheTime, show_spinner=False)
def calculate_spillover(board):
    sprints_df, issues_df, changelog_df, latest_sprints_df = extract_spillover_data(board)
    
    # Merge changelog with sprints to get sprint start and end dates
    changelog_df = changelog_df.merge(sprints_df[['id', 'start_date', 'end_date']], left_on='value_to', right_on='id', how='left')
    # Filter out records where the issue was unassigned before sprint start
    changelog_df = changelog_df[~((changelog_df['change_date_time'] < changelog_df['start_date']) & (changelog_df['value_to'].isna()))]
    # Track the periods during which an issue was assigned to a sprint
    changelog_df['assigned_during_sprint'] = (changelog_df['change_date_time'] >= changelog_df['start_date']) & (changelog_df['change_date_time'] <= changelog_df['end_date'])

    # Ensure change_date_time, start_date, and end_date are datetime
    changelog_df['change_date_time'] = pd.to_datetime(changelog_df['change_date_time'], utc=True, errors='coerce')
    changelog_df['start_date'] = pd.to_datetime(changelog_df['start_date'], utc=True, errors='coerce')
    changelog_df['end_date'] = pd.to_datetime(changelog_df['end_date'], utc=True, errors='coerce')
    # Sort by issue_id and change_date_time
    changelog_df.sort_values(by=['issue_id', 'change_date_time'], inplace=True)

    # Apply the function to each row
    changelog_df['is_value_to_equal_id'] = changelog_df.apply(lambda row: determine_value_to__for_calculate_spillover(row, changelog_df), axis=1)

    # Calculate number of unique sprints each issue was in based on is_value_to_equal_id being True
    changelog_df['num_sprints'] = changelog_df[changelog_df['is_value_to_equal_id']].groupby('issue_id')['value_to'].transform('nunique').astype(int)
    # Categorize issues based on number of sprints
    changelog_df['sprint_category'] = pd.cut(changelog_df['num_sprints'], bins=[0, 1, 2, float('inf')], labels=['1 Sprint', '2 Sprints', '3+ Sprints'])
    # Sort the DataFrame by 'change_date_time'
    changelog_df.sort_values(by=['issue_id', 'change_date_time'], inplace=True)

    # Filter rows where is_value_to_equal_id is True and value_to is not null
    changelog_df = changelog_df[(changelog_df['is_value_to_equal_id']) & (changelog_df['value_to'].notna())]
    # Sort by issue_id and change_date_time in descending order
    changelog_df = changelog_df.sort_values(by=['issue_id', 'change_date_time'], ascending=[True, False])
    # Drop duplicates to keep the latest change_date_time for each issue_id
    changelog_df = changelog_df.drop_duplicates(subset=['issue_id'], keep='first')

    # Calculate the counts of issues closed in each sprint category per sprint
    sprint_counts = changelog_df.groupby(['id', 'sprint_category'], observed=False).size().unstack(fill_value=0)
    # Calculate the percentage of issues closed in each sprint category per sprint
    sprint_percentages = sprint_counts.div(sprint_counts.sum(axis=1), axis=0) * 100
    
    # Limiting to latest 12 Sprints
    sprint_percentages = sprint_percentages.reset_index().merge(latest_sprints_df[['id', 'name']], left_on='id', right_on='id', how='inner')
    changelog_df = changelog_df[changelog_df['id'].astype(str).isin(latest_sprints_df['id'])]
    
    # Add average calculation at the end of calculate_spillover function
    average_sprints = changelog_df['num_sprints'].mean()

    # Clear unnecessary DataFrames
    del changelog_df
    del sprints_df
    del issues_df
    del sprint_counts

    # Run garbage collector to free up memory
    gc.collect()

    return sprint_percentages, average_sprints

