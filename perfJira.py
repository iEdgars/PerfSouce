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
        untranslated_name TEXT,
        is_custom INTEGER,
        is_orderable INTEGER,
        is_navigable INTEGER,
        is_searchable INTEGER,
        type TEXT
    )
    ''')
    
    # Insert data into table
    for field in data:
        id = field['id']
        key = field['key']
        name = field['name']
        is_custom = field['custom']
        is_orderable = field['orderable']
        is_navigable = field['navigable']
        is_searchable = field['searchable']
        if is_custom == True:
            untranslated_name = field['untranslatedName']
            custom_id = field['schema']['customId']
        else:
            untranslated_name = ''
            custom_id = 0
        try:
            field_type = field['schema']['type']
        except KeyError:
            field_type = ''

        cursor.execute('''
        INSERT INTO fields (
            the_project, jira_project, id, custom_id, key, name, untranslated_name, is_custom, is_orderable, is_navigable, is_searchable, type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (the_project, project_code, id, custom_id, key, name, untranslated_name, is_custom, is_orderable, is_navigable, is_searchable, field_type))

    
    # Commit and close connection
    conn.commit()
    conn.close()

# Function to get all resolutions from Jira and store in SQLite
def fetch_jira_resolutions(the_project, jira_url, project_code, auth):
    # Jira API URL
    url = f"{jira_url}/rest/api/latest/resolution"
    
    # Make the request to Jira API
    response = requests.get(url, auth=auth)
    data = response.json()
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS resolutions (
        the_project TEXT,
        jira_project TEXT,
        id INTEGER,
        name TEXT,
        description TEXT
    )
    ''')
    
    # Insert data into table
    for resolution in data:
        resolution_id = resolution['id']
        resolution_name = resolution['name']
        resolution_description = resolution['description']
        
        cursor.execute('''
        INSERT INTO resolutions (
            the_project, jira_project, id, name, description
        ) VALUES (?, ?, ?, ?, ?)
        ''', (the_project, project_code, resolution_id, resolution_name, resolution_description))
    
    # Commit and close connection
    conn.commit()
    conn.close()

# Function to get all priorities from Jira and store in SQLite
def fetch_jira_priorities(the_project, jira_url, project_code, auth):
    # Jira API URL
    url = f"{jira_url}/rest/api/latest/priority"
    
    # Make the request to Jira API
    response = requests.get(url, auth=auth)
    data = response.json()
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS priorities (
        the_project TEXT,
        jira_project TEXT,
        id INTEGER,
        name TEXT,
        description TEXT,
        status_color TEXT
    )
    ''')
    
    # Insert data into table
    for priority in data:
        priority_id = priority['id']
        priority_name = priority['name']
        priority_description = priority['description']
        status_color = priority['statusColor']
        
        cursor.execute('''
        INSERT INTO priorities (
            the_project, jira_project, id, name, description, status_color
        ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (the_project, project_code, priority_id, priority_name, priority_description, status_color))
    
    # Commit and close connection
    conn.commit()
    conn.close()

# Function to get all statuses from Jira and store in SQLite
def fetch_jira_statuses(the_project, jira_url, project_code, auth):
    # Jira API URL
    url = f"{jira_url}/rest/api/latest/status"
    
    # Make the request to Jira API
    response = requests.get(url, auth=auth)
    data = response.json()
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS statuses (
        the_project TEXT,
        jira_project TEXT,
        id INTEGER,
        name TEXT,
        description TEXT,
        untranslated_name TEXT,
        status_category_id INTEGER,
        status_category_key TEXT,
        status_category_name TEXT,
        status_category_color TEXT,
        scope_type TEXT,
        project_id INTEGER
    )
    ''')
    
    # Insert data into table
    for status in data:
        status_id = status['id']
        status_name = status['name']
        status_description = status['description']
        untranslated_name = status['untranslatedName']
        status_category_id = status['statusCategory']['id']
        status_category_key = status['statusCategory']['key']
        status_category_name = status['statusCategory']['name']
        status_category_color = status['statusCategory']['colorName']
        
        # Handle scope if it exists
        if 'scope' in status:
            scope_type = status['scope']['type']
            project_id = status['scope']['project']['id']
        else:
            scope_type = ''
            project_id = 0
        
        cursor.execute('''
        INSERT INTO statuses (
            the_project, jira_project, id, name, description, untranslated_name, status_category_id, status_category_key, status_category_name, status_category_color, scope_type, project_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (the_project, project_code, status_id, status_name, status_description, untranslated_name, status_category_id, status_category_key, status_category_name, status_category_color, scope_type, project_id))
    
    # Commit and close connection
    conn.commit()
    conn.close()