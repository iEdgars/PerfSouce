import requests
import sqlite3
import json
import streamlit as st

def confirm_connection(jira_url, username, api_key):
    try:
        # Construct the API endpoint for fetching projects
        api_endpoint = f"{jira_url}/rest/api/2/project"
        
        # Make a GET request to the Jira API
        response = requests.get(api_endpoint, auth=(username, api_key))
        
        # Check if the response status code indicates success
        if len(response.text) > 2:
            return True
        else:
            # st.error(f"Connection failed")
            return False
    except Exception as e:
        st.error(f"Connection failed: {e}")
        return False
    
# Function to get all projects from Jira and store in SQLite
def fetch_jira_projects(the_project, jira_url, auth):
    # Fetch projects from Jira
    response = requests.get(f"{jira_url}/rest/api/latest/project", auth=auth)
    projects = response.json()

    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jira_projects (
            the_project TEXT,
            project_url TEXT,
            id TEXT,
            key TEXT,
            name TEXT,
            projectTypeKey TEXT,
            simplified BOOLEAN,
            style TEXT,
            isPrivate BOOLEAN
        )
    ''')

    # Insert data into table
    for project in projects:
        cursor.execute('''
            INSERT INTO jira_projects (the_project, project_url, id, key, name, projectTypeKey, simplified, style, isPrivate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (the_project, project['self'], project['id'], project['key'], project['name'], project['projectTypeKey'], project['simplified'], project['style'], project['isPrivate']))

    # Commit and close connection
    conn.commit()
    conn.close()


# Function to get all statuses for issue types from Jira and store in SQLite
def fetch_jira_issue_status(the_project, jira_url, project_code, auth):
    # Jira API URL
    url = f"{jira_url}/rest/api/latest/project/{project_code}/statuses"
    
    # Make the request to Jira API
    response = requests.get(url, auth=auth)
    data = response.json()
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues_and_statuses (
        the_project TEXT,
        jira_project TEXT,
        issue_type_id TEXT,
        issue_type TEXT,
        status_name TEXT,
        status_id TEXT,
        untranslated_name TEXT,
        category_id INTEGER,
        category_key TEXT,
        category_name TEXT,
        category_color TEXT
    )
    ''')
    
    # Insert data into table
    for issue_type in data:
        issue_type_id = issue_type['id']
        issue_type_name = issue_type['name']
        for status in issue_type['statuses']:
            status_name = status['name']
            status_id = status['id']
            untranslated_name = status['untranslatedName']
            category_id = status['statusCategory']['id']
            category_key = status['statusCategory']['key']
            category_name = status['statusCategory']['name']
            category_color = status['statusCategory']['colorName']
            
            cursor.execute('''
            INSERT INTO issues_and_statuses (
                the_project, jira_project, issue_type_id, issue_type, status_name, status_id, untranslated_name, category_id, category_key, category_name, category_color
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (the_project, project_code, issue_type_id, issue_type_name, status_name, status_id, untranslated_name, category_id, category_key, category_name, category_color))
    
    # Commit and close connection
    conn.commit()
    conn.close()

# Function to get all fields from Jira and store in SQLite
def fetch_jira_fields(the_project, jira_url, project_code, auth):
    # Jira API URL
    url = f"{jira_url}/rest/api/latest/field"
    
    # Make the request to Jira API
    response = requests.get(url, auth=auth)
    data = response.json()
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fields (
        the_project TEXT,
        jira_project TEXT,
        id TEXT,
        custom_id INTEGER,
        key TEXT,
        name TEXT,
        untranslatedName TEXT,
        is_custom TEXT,
        is_orderable TEXT,
        is_navigable TEXT,
        is_searchable TEXT
    )
    ''')
    
    # Insert data into table
    for issue_type in data:
        issue_type_id = issue_type['id']
        issue_type_name = issue_type['name']
        for status in issue_type['statuses']:
            status_name = status['name']
            status_id = status['id']
            untranslated_name = status['untranslatedName']
            category_id = status['statusCategory']['id']
            category_key = status['statusCategory']['key']
            category_name = status['statusCategory']['name']
            category_color = status['statusCategory']['colorName']
            
            cursor.execute('''
            INSERT INTO issues_and_statuses (
                the_project, jira_project, issue_type_id, issue_type, status_name, status_id, untranslated_name, category_id, category_key, category_name, category_color
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (the_project, project_code, issue_type_id, issue_type_name, status_name, status_id, untranslated_name, category_id, category_key, category_name, category_color))
    
    # Commit and close connection
    conn.commit()
    conn.close()
    
    
    
    
    pass