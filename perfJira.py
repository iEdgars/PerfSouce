import pandas as pd
from jira import JIRA
import sqlite3

def fetch_jira_issues(server_url, email, api_token, project_key):
    # Connect to JIRA instance
    jira = JIRA(server=server_url, basic_auth=(email, api_token))
    
    # Fetch all issues from the specified project
    issues = jira.search_issues(f'project={project_key}', maxResults=False)
    
    # Collect issue keys and summaries
    issue_data = {
        'Key': [issue.key for issue in issues],
        'Summary': [issue.fields.summary for issue in issues]
    }
    
    # Convert to DataFrame
    df = pd.DataFrame(issue_data)
    
    return df

# Example usage
# server_url = 'https://your-jira-instance.atlassian.net'
# email = 'your-email'
# api_token = 'your-api-token'
# project_key = 'YOUR_PROJECT_KEY'
# df = get_jira_issues_as_dataframe(server_url, email, api_token, project_key)
# print(df)

def write_df_to_db(df, db_name, table_name):
    # Connect to SQLite database (it will create the database if it doesn't exist)
    conn = sqlite3.connect(db_name)
    
    # Write the DataFrame to the specified table
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    # Close the connection
    conn.close()

# Example usage
# df = get_jira_issues_as_dataframe(server_url, email, api_token, project_key)
# write_dataframe_to_sqlite(df, 'jira_issues.db', 'issues')