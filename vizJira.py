import pandas as pd
import sqlite3
import streamlit as st

cacheTime = 900 # time to keep cache in seconds

@st.cache_data(ttl=cacheTime)
def get_issues_dataframe(epic_selection=True):
    # Connect to SQLite database
    conn = sqlite3.connect('jira_projects.db')
    
    # Define the query
    query = '''
    SELECT *
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