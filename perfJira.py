import requests
import sqlite3
import json
import streamlit as st
import hashlib

cacheTime = 900 # time to keep cache in seconds

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
    
# Function to get all Projects from Jira provide for selection
@st.cache_data(ttl=cacheTime)
def fetch_jira_projects(jira_url, auth):
    data = requests.get(f"{jira_url}/rest/api/latest/project", auth=auth).json()
    return data

# Function to get all boards from Jira Agile and store in SQLite
@st.cache_data(ttl=cacheTime)
def fetch_jira_boards(jira_url, auth):
    start_at = 0
    max_results = 50
    boards = []
    while True:
        response = requests.get(f"{jira_url}/rest/agile/latest/board", auth=auth, params={'startAt': start_at, 'maxResults': max_results}).json()
        boards.extend(response['values'])
        if response['isLast']:
            break
        start_at += max_results

    return boards

# Function to get all statuses for issue types from Jira and store in SQLite
def fetch_jira_project_issue_status(the_project, jira_url, project_code, auth):
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
    CREATE TABLE IF NOT EXISTS project_issues_and_statuses (
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
            INSERT INTO project_issues_and_statuses (
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

        # Use .get() to safely access keys
        untranslated_name = field.get('untranslatedName', None)
        custom_id = field.get('schema', {}).get('customId', None)
        field_type = field.get('schema', {}).get('type', None)

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
        
        # Handle scope using .get() method
        scope = status.get('scope', {})
        scope_type = scope.get('type', None)
        project_id = scope.get('project', {}).get('id', None)
        
        cursor.execute('''
        INSERT INTO statuses (
            the_project, jira_project, id, name, description, untranslated_name, status_category_id, status_category_key, status_category_name, status_category_color, scope_type, project_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (the_project, project_code, status_id, status_name, status_description, untranslated_name, status_category_id, status_category_key, status_category_name, status_category_color, scope_type, project_id))
    
    # Commit and close connection
    conn.commit()
    conn.close()

# Function to get all issue types from Jira and store in SQLite
def fetch_jira_issue_types(the_project, jira_url, project_code, auth):
    # Jira API URL
    url = f"{jira_url}/rest/api/latest/issuetype"
    
    # Make the request to Jira API
    response = requests.get(url, auth=auth)
    data = response.json()
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issue_types (
        the_project TEXT,
        jira_project TEXT,
        id INTEGER,
        description TEXT,
        name TEXT,
        untranslated_name TEXT,
        subtask BOOLEAN,
        hierarchy_level INTEGER,
        scope_type TEXT,
        project_id INTEGER
    )
    ''')
    
    # Insert data into table
    for issue_type in data:
        issue_type_id = issue_type['id']
        description = issue_type['description']
        name = issue_type['name']
        untranslated_name = issue_type['untranslatedName']
        subtask = issue_type['subtask']
        hierarchy_level = issue_type['hierarchyLevel']

        # Handle scope using .get() method
        scope = issue_type.get('scope', {})
        scope_type = scope.get('type', None)
        project_id = scope.get('project', {}).get('id', None)
        
        cursor.execute('''
        INSERT INTO issue_types (
            the_project, jira_project, id, description, name, untranslated_name, subtask, hierarchy_level, scope_type, project_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (the_project, project_code, issue_type_id, description, name, untranslated_name, subtask, hierarchy_level, scope_type, project_id))
    
    # Commit and close connection
    conn.commit()
    conn.close()

# Function to get and store sprint info from Jira Agile
def fetch_jira_sprints(the_project, jira_url, project_code, board_id, auth):
    start_at = 0
    max_results = 50
    is_last = False
    
    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sprints (
        the_project TEXT,
        jira_project TEXT,
        board_id INTEGER,
        id INTEGER,
        state TEXT,
        name TEXT,
        start_date TEXT,
        end_date TEXT,
        complete_date TEXT,
        origin_board_id INTEGER,
        goal TEXT
    )
    ''')
    
    while not is_last:
        # Jira API URL
        url = f"{jira_url}/rest/agile/latest/board/{board_id}/sprint?startAt={start_at}&maxResults={max_results}"
        
        # Make the request to Jira API
        response = requests.get(url, auth=auth)
        if response.status_code == 400:
            conn.close()
            return  # Stop function execution

        data = response.json()
        
        # Insert data into table
        for sprint in data['values']:
            sprint_id = sprint['id']
            state = sprint['state']
            name = sprint['name']
            start_date = sprint.get('startDate', '')
            end_date = sprint.get('endDate', '')
            complete_date = sprint.get('completeDate', '')
            origin_board_id = sprint['originBoardId']
            goal = sprint.get('goal', '')
            
            cursor.execute('''
            INSERT INTO sprints (
                the_project, jira_project, board_id, id, state, name, start_date, end_date, complete_date, origin_board_id, goal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (the_project, project_code, board_id, sprint_id, state, name, start_date, end_date, complete_date, origin_board_id, goal))
        
        # Update pagination variables
        start_at += max_results
        is_last = data['isLast']
    
    # Commit and close connection
    conn.commit()
    conn.close()

def issue_field_handling(field, value, sprint_field):
    if field in ['assignee', 'reporter', 'creator']:
        display_name = value.get('displayName', '') if value else ''
        field_value = hashlib.blake2b(display_name.encode()).hexdigest() if display_name else 'None'
    
    if field == 'comment':
        field_value = 'True' if value['total'] > 0 else 'False'
        field = 'Commented'

    if field == 'description':
        field_value = 'Obfuscated'

    if field == 'summary':
        field_value = 'Obfuscated'
    
    if field == 'parent':
        field_value = value.get('key', '') if value else ''

    if field == sprint_field:
        if isinstance(value, list):
            field_value = ';'.join(str(item['id']) for item in value)
        else:
            field_value = str(value)

    return field, field_value

def issue_changelog_field_handling(field, item, sprint_field):
    if field in ['assignee', 'reporter', 'creator']:
    # potentially hash in future for some unique count per person metric or smth
        from_string = item.get('fromString', '')
        to_string = item.get('toString', '')
        value_from = hashlib.blake2b(from_string.encode()).hexdigest() if from_string else 'None'
        value_to = hashlib.blake2b(to_string.encode()).hexdigest() if to_string else 'None'

    if field == 'comment':
        value_from = 'Obfuscated'
        value_to = 'Obfuscated'

    if field == 'description':
        value_from = f"Obfuscated, len:{len(item.get('fromString', ''))}" if item.get('fromString') else 'Obfuscated, len:0'
        value_to = f"Obfuscated, len:{len(item.get('toString', ''))}" if item.get('toString') else 'Obfuscated, len:0'

    if field == 'summary':
        value_from = f"Obfuscated, len:{len(item.get('fromString', ''))}" if item.get('fromString') else 'Obfuscated, len:0'
        value_to = f"Obfuscated, len:{len(item.get('toString', ''))}" if item.get('toString') else 'Obfuscated, len:0'

    if field == 'parent':
        value_from = item.get('fromString', '')
        value_to = item.get('toString', '')
    
    if field == sprint_field:
        value_from = item.get('from', '')
        value_to = item.get('to', '')

    return value_from, value_to

# Function to get and store issues and changelog from Jira
def fetch_jira_issues(the_project, jira_url, project_code, auth, sprint_field, board_id=None):
    spec_fields = ['assignee', 'reporter', 'creator', 'comment', 'description', 'summary', 'parent', sprint_field]
    skip_fields = ['attachment']

    start_at = 0
    max_results = 100

    # Connect to SQLite database (or create it)
    conn = sqlite3.connect('jira_projects.db')
    cursor = conn.cursor()
    
    # Create tables if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        the_project TEXT,
        jira_project TEXT,
        issue_id TEXT,
        key TEXT,
        field TEXT,
        field_value TEXT,
        issue_type_name TEXT,
        issue_status TEXT,
        issue_status_cat_key TEXT,
        issue_status_cat_name TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issue_changelog (
        the_project TEXT,
        jira_project TEXT,
        issue_id TEXT,
        key TEXT,
        change_date_time TEXT,
        field TEXT,
        field_type TEXT,
        field_id TEXT,
        value_from TEXT,
        value_to TEXT,
        issue_type_name TEXT,
        issue_status TEXT,
        issue_status_cat_key TEXT,
        issue_status_cat_name TEXT
    )
    ''')

    while True:
        if board_id:
            url = f'{jira_url}/rest/agile/latest/board/{board_id}/issue?expand=changelog&maxResults={max_results}&startAt={start_at}'
        elif project_code:
            jql_query = f'project = {project_code}'
            url = f'{jira_url}/rest/api/latest/search?jql={jql_query}&expand=changelog&maxResults={max_results}&startAt={start_at}'
        else:
            raise ValueError("Either board_id or project_code must be provided")

        response = requests.get(url, auth=auth)
        response.raise_for_status()
        
        issues = response.json()['issues']
        
        for issue in issues:
            issue_id = issue['id']
            key = issue['key']
            issue_type_name = issue['fields']['issuetype']['name']
            issue_status = issue['fields']['status']['name']
            issue_status_cat_key = issue['fields']['status']['statusCategory']['key']
            issue_status_cat_name = issue['fields']['status']['statusCategory']['name']
            
            # Store latest fields
            for field, value in issue['fields'].items():
                if field in skip_fields:
                    continue
                elif field in spec_fields:
                   field, field_value = issue_field_handling(field, value, sprint_field)
                else:
                    field_value = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
                
                cursor.execute('''
                INSERT INTO issues (
                    the_project, jira_project, issue_id, key, field, field_value, issue_type_name, issue_status, issue_status_cat_key, issue_status_cat_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (the_project, project_code, issue_id, key, field, field_value, issue_type_name, issue_status, issue_status_cat_key, issue_status_cat_name))
            
            # Store changelog
            for history in issue['changelog']['histories']:
                change_date_time = history['created']
                for item in history['items']:
                    field = item['field']
                    field_type = item['fieldtype']
                    field_id = item.get('fieldId', '')
                    if field_id in skip_fields:
                        continue
                    elif field_id in spec_fields:
                        value_from, value_to = issue_changelog_field_handling(field_id, item, sprint_field)
                    else:
                        value_from = item.get('fromString', '')
                        value_to = item.get('toString', '')
                    
                    cursor.execute('''
                    INSERT INTO issue_changelog (
                        the_project, jira_project, issue_id, key, change_date_time, field, field_type, field_id, value_from, value_to, issue_type_name,issue_status, issue_status_cat_key, issue_status_cat_name
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (the_project, project_code, issue_id, key, change_date_time, field, field_type, field_id, value_from, value_to, issue_type_name, issue_status, issue_status_cat_key, issue_status_cat_name))
        
        if len(issues) < max_results:
            break
        
        start_at += max_results
    
    # Commit and close connection
    conn.commit()
    conn.close()