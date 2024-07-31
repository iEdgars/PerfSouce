import pandas as pd
import sqlite3
import streamlit as st

cacheTime = 900 # time to keep cache in seconds

# Get Lead time data
# @st.cache_data(ttl=cacheTime)
def get_issues_dataframe(epic_selection=False):
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

# Calculate Lead time data
# @st.cache_data(ttl=cacheTime)
def transform_issues_dataframe(df):
    # Pivot the DataFrame to get 'created' and 'resolutiondate' in columns
    df_pivot = df.pivot(index=['the_project', 'jira_project', 'issue_id', 'key', 'issue_type_name'], 
                        columns='field', values='field_value').reset_index()
    
    # Rename columns for clarity
    df_pivot.columns.name = None
    df_pivot.rename(columns={'created': 'created', 'resolutiondate': 'resolved'}, inplace=True)
    
    # Extract the date part from the datetime string
    df_pivot['created'] = df_pivot['created'].str[:10]
    df_pivot['resolved'] = df_pivot['resolved'].str[:10]
    
    # Convert date columns to datetime
    df_pivot['created'] = pd.to_datetime(df_pivot['created'], errors='coerce')
    df_pivot['resolved'] = pd.to_datetime(df_pivot['resolved'], errors='coerce')
    
    # Filter out rows where 'resolved' is NaT (Not a Time)
    df_pivot = df_pivot.dropna(subset=['resolved'])
    
    # Calculate lead_time
    df_pivot['lead_time'] = (df_pivot['resolved'] - df_pivot['created']).dt.days
    
    return df_pivot