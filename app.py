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

mock_boards = [
    {"id": "001", "name": "ADOM Scrum Board (Mock data)", "location": {"projectKey": "ADOM"}},
    {"id": "002", "name": "DMT Scrum Board (Mock data)", "location": {"projectKey": "ADOM"}},
    {"id": "003", "name": "ADOM Main Board (Mock data)", "location": {"projectKey": "ADOM"}},
    {"id": "004", "name": "DMT Kanban (Mock data)", "location": {"projectKey": "ADOM"}},
    {"id": "005", "name": "ADOM DMT Board (Mock data)", "location": {"projectKey": "ADOM"}},
    {"id": "123", "name": "DMT ADOM Board (Mock data)", "location": {"projectKey": "ADOM"}}
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
#❗ To add mock data for screenshots, presentation. To be removed in final versions❗
        boards = mock_boards + boards
        board_options = {f"{board['id']}: {board['name']}": board for board in boards if board.get('location', {}).get('projectKey') == selected_project_key}
        board_options = {"Use whole Project": None} | board_options  # Add "Use whole Project" option at the top
        selected_board_option = st.selectbox("Select a Board", [""] + list(board_options.keys()), index=0, help=st_help.selected_board_option_help)

        if selected_board_option:
#❗ Sidebar for some debug data❗
            with debugbar:
                st.write("---")
                st.write(f'Selected board: {selected_board_option}')
            if selected_board_option == "Use whole Project":
                selected_board_id = None
                selected_board_name = "Use whole Project"
            else:
                selected_board = board_options[selected_board_option]
                selected_board_id = selected_board['id']
                selected_board_name = selected_board['name']
            
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
    st.write(f"Retrieving data for {project_key}: {project_name}, {board_name}")

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
    else:
        st.write('Initial data load done')

st.button('OK')



    

