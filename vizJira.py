import pandas as pd
import sqlite3
import streamlit as st

cacheTime = 900 # time to keep cache in seconds

# Function to get Lead time data
# @st.cache_data(ttl=cacheTime)
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
# @st.cache_data(ttl=cacheTime)
def ttm_first_inProgress_dates(epic_selection=True):
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
# @st.cache_data(ttl=cacheTime)
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
    
    return merged_df
