import streamlit as st
import pandas as pd
import sqlite3
import requests

# custom project scripts
import perfJira
import st_help

# Set the page config
st.set_page_config(
    page_title="Perf Souce",
    page_icon=":bar_chart:",
    # layout="wide" 
)

# Initialize session states if they don't exist
if 'auth' not in st.session_state:
    st.session_state.auth = None
if 'info' not in st.session_state:
    st.session_state.info = None
if 'project' not in st.session_state:
    st.session_state.project = None
if 'board' not in st.session_state:
    st.session_state.board = None
if 'jira_data_bacth' not in st.session_state:
    st.session_state.jira_data_bacth = None
if 'jira_data_bacth2' not in st.session_state:
    st.session_state.jira_data_bacth2 = None
if 'jira_field_mapping' not in st.session_state:
    st.session_state.jira_field_mapping = None

#❗ Sidebar for some debug data❗
debugbar = st.sidebar
with debugbar:
    st.write('session_state:')
    st.write(st.session_state)

st.title("Project Performance Dashboard")

if st.session_state.auth is None:
    st.text_input("Project code", key='input_project', help=st_help.project_help)
    st.text_input("Jira Username", key='input_username', help=st_help.username_help)
    st.text_input("Jira API Key", key='input_api_key', type="password", help=st_help.api_key_help)
    st.text_input("Jira URL", key='input_jira_url', help=st_help.jira_url_help)
    if st.button("Check Connection"):
        if perfJira.confirm_connection(st.session_state.input_jira_url, st.session_state.input_username, st.session_state.input_api_key):
            st.session_state.auth = (st.session_state.input_username, st.session_state.input_api_key)
            st.session_state.info = (st.session_state.input_project, st.session_state.input_jira_url)
            st.success("Connection successful!")
        else:
            st.error("Connection failed. Please check your credentials and URL.")
    
#❗ Mock data❗
#❗ To add mock data for screenshots, presentation. To be removed in final versions❗
mock_projects = [
    {"id": "00001", "key": "ADOM", "name": "The ADOM Project (Mock data)"},
    {"id": "00002", "key": "ADMT", "name": "DMT Project (Mock data)"},
    {"id": "00003", "key": "AAAA", "name": "Project 1 (Mock data)"}
]


# Selecting Project and Board
if st.session_state.auth is not None and st.session_state.board is None:
    # auth for data retrieval. As well verification of data beilg available.
    auth = st.session_state.auth
    project, jira_url = st.session_state.info

    # Fetch all available Projects
    projects = perfJira.fetch_jira_projects(jira_url, auth)
#❗ To add mock data for screenshots, presentation. To be removed in final versions❗
    projects = mock_projects + projects
    project_options = {f"{project['key']}: {project['name']}": project for project in projects}
    st.divider()
    selected_project_option = st.selectbox("Select a Project", [""] + list(project_options.keys()), index=0, help=st_help.selected_project_option_help)

    if selected_project_option:
        selected_project = project_options[selected_project_option]
#❗ Sidebar for some debug data❗        
        with debugbar:
            st.write("---")
            st.write(f'Selected Project: {selected_project}')
        selected_project_id = selected_project['id']
        selected_project_key = selected_project['key']
        selected_project_name = selected_project['name']

        st.session_state.project = (selected_project_id, selected_project_key, selected_project_name)
       
        # Fetch all Boards for the selected project
        boards = perfJira.fetch_jira_boards(jira_url, auth)
        board_ids = [board['id'] for board in boards if board.get('location', {}).get('projectKey') == selected_project_key]
        selected_board_option = "Use whole Project"

        if selected_board_option:
#❗ Sidebar for some debug data❗
            with debugbar:
                st.write("---")
                st.write(f'Selected board: {selected_board_option}')

            if selected_board_option == "Use whole Project":
                selected_board_id = None
                selected_board_name = "Use whole Project"
            
            st.session_state.board = (selected_board_id, selected_board_name)

#❗ Sidebar for some debug data❗
            with debugbar:
                st.write("---")
                st.write(f'Selected board detailed: {selected_board_id}, {selected_board_name}')

if st.session_state.board is not None:

    auth = st.session_state.auth
    project, jira_url = st.session_state.info
    project_id, project_key, project_name = st.session_state.project
    board_id, board_name = st.session_state.board
    # st.write(f"Retrieving data for {project_key}: {project_name}, {board_name}")
    st.write(f"Retrieving data for {project_key}: {project_name}")

    if st.session_state.jira_data_bacth is None:
        jira_data_bacth_bar = st.progress(0, text='Retrieving initial Jira data')
        
        steps = [
            ("Project issue statuses", perfJira.fetch_jira_project_issue_status),
            ("fields", perfJira.fetch_jira_fields),
            ("resolutions", perfJira.fetch_jira_resolutions),
            ("priorities", perfJira.fetch_jira_priorities),
            ("statuses", perfJira.fetch_jira_statuses),
            ("issue types", perfJira.fetch_jira_issue_types)
        ]
        
        for i, (desc, func) in enumerate(steps, start=1):
            func(project, jira_url, project_key, auth)
            jira_data_bacth_bar.progress(int((i / len(steps)) * 100), text=f'Retrieving initial Jira data: {desc}')
        
        jira_data_bacth_bar.progress(100, text='Done!')
        st.session_state.jira_data_bacth = 'Completed'

if st.session_state.jira_data_bacth == 'Completed' and st.session_state.jira_field_mapping != 'Completed':

    auth = st.session_state.auth
    project, jira_url = st.session_state.info
    project_id, project_key, project_name = st.session_state.project
    board_id, board_name = st.session_state.board

    st.write('''
At this step please match attributes required for metrics calculation to appropriate fields in Jira. 
Either a default field or a custom field can be selected. If an attribute is left blank – commonly used field will be taken as a match for the attribute.\n 
Fields mapping impacts all metric calculations by Jira data in a project (e.g. velocity metrics, quality metrics, Burn Up, etc.).
''')

    # Function to fetch data from SQLite
    def fetch_jira_fields_from_db():
        conn = sqlite3.connect('jira_projects.db')
        query = "SELECT name, key FROM fields"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    # Function to save selections to SQLite
    def save_selections_to_db(selections):
        conn = sqlite3.connect('jira_projects.db')
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS field_selections (
            metric_attribute TEXT PRIMARY KEY,
            field_name TEXT,
            field_id TEXT,
            masked INTEGER
        )
        ''')
        
        # Insert or update data into table
        for attribute, selection in selections.items():
            cursor.execute('''
            INSERT INTO field_selections (metric_attribute, field_name, field_id, masked)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(metric_attribute) DO UPDATE SET
            field_name=excluded.field_name,
            field_id=excluded.field_id,
            masked=excluded.masked
            ''', (attribute, selection['field_name'], selection['field_id'], selection['masked']))
        
        # Commit and close connection
        conn.commit()
        conn.close()

    # Fetch the data
    fields_df = fetch_jira_fields_from_db()

    # Create a dictionary for name to key and key to name mapping
    name_to_key = dict(zip(fields_df['name'], fields_df['key']))
    key_to_name = dict(zip(fields_df['key'], fields_df['name']))

    # Metric attributes
    metric_attributes = [
        "Estimation in Story Points", 
        "Estimation in Original Hours", 
        "Sprint", 
        "Epic", 
        "Affected release", 
        "Fixed release", 
        "Severity", 
        "Priority"
    ]

    # Initialize session state for each attribute if not already done
    for attribute in metric_attributes:
        if f"{attribute}_name" not in st.session_state:
            st.session_state[f"{attribute}_name"] = "Please select value"
        if f"{attribute}_id" not in st.session_state:
            st.session_state[f"{attribute}_id"] = "Please select value"
        if f"{attribute}_masked" not in st.session_state:
            st.session_state[f"{attribute}_masked"] = False

    # Callback functions to update session state
    def update_name(attribute):
        field_id = st.session_state[f"{attribute}_id"]
        if field_id in key_to_name:
            st.session_state[f"{attribute}_name"] = key_to_name[field_id]

    def update_id(attribute):
        field_name = st.session_state[f"{attribute}_name"]
        if field_name in name_to_key:
            st.session_state[f"{attribute}_id"] = name_to_key[field_name]

    # Create the form
    with st.container():
        selections = {}
        for attribute in metric_attributes:
            col1, col2, col3, col4 = st.columns([2, 3, 3, 1])
            
            with col1:
                st.markdown(f"**{attribute}**")
            
            with col2:
                st.selectbox(
                    f"Issue Field Name for {attribute}", 
                    ["Please select value"] + list(fields_df['name']), 
                    key=f"{attribute}_name",
                    on_change=update_id,
                    args=(attribute,)
                )
            
            with col3:
                st.selectbox(
                    f"Issue Field ID for {attribute}", 
                    ["Please select value"] + list(fields_df['key']), 
                    key=f"{attribute}_id",
                    on_change=update_name,
                    args=(attribute,)
                )
            
            with col4:
                st.checkbox("Masked", key=f"{attribute}_masked")
            
            selections[attribute] = {
                'field_name': st.session_state[f"{attribute}_name"],
                'field_id': st.session_state[f"{attribute}_id"],
                'masked': int(st.session_state[f"{attribute}_masked"])
            }
            
            st.divider()

        # Save selections to SQLite
        save_selections_to_db(selections)

        if st.button("Confirm"):
            st.session_state.jira_field_mapping = 'Completed'

if st.session_state.jira_field_mapping == 'Completed':
    auth = st.session_state.auth
    project, jira_url = st.session_state.info
    project_id, project_key, project_name = st.session_state.project
    board_id, board_name = st.session_state.board
    
    if st.session_state.jira_data_bacth2 is None:
        
        jira_data_bacth_bar = st.progress(0, text='Retrieving Sprint and Issue Jira data')

        for en, id in enumerate(board_ids, start=1):
            perfJira.fetch_jira_sprints(project, jira_url, project_key, id, auth)
            jira_data_bacth_bar.progress(int((en / len(board_ids)) * 50), text=f'Retrieving Sprint data for board {id}')

        jira_data_bacth_bar.progress(80, text='Retrieving Issue history')
        perfJira.fetch_jira_issues(project, jira_url, project_key, auth, board_id)
        
        jira_data_bacth_bar.progress(100, text='Done!')
        st.session_state.jira_data_bacth2 = 'Completed'

st.button('OK')