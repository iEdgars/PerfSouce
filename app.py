import streamlit as st
import pandas as pd
import sqlite3
import perfJira
import requests

# Set the page config
st.set_page_config(
    page_title="Perf Souce",
    page_icon=":bar_chart:",
    # layout="wide" 
)

st.title("Project Performance Dashboard")

# Streamlit UI for user inputs
project = st.text_input("Project code")
username = st.text_input("Jira Username")
api_key = st.text_input("Jira API Key", type="password")
jira_url = st.text_input("Jira URL")


if st.button("Check Connection"):
    if perfJira.confirm_connection(jira_url, username, api_key):
        st.success("Connection successful!")
    else:
        st.error("Connection failed. Please check your credentials and URL.")

#auth for methods
auth = (username, api_key)

# Mock data
mock_projects = [
    {"id": "00001", "key": "ADOM", "name": "The ADOM Project"},
    {"id": "00002", "key": "ADMT", "name": "DMT Project"},
    {"id": "00003", "key": "AAAA", "name": "Project 1"}
]

projects = requests.get(f"{jira_url}/rest/api/latest/project", auth=auth).json()
projects = mock_projects + projects
project_options = {f"{project['key']}: {project['name']}": project for project in projects}
selected_project_option = st.selectbox("Select a Project", [""] + list(project_options.keys()), index=0)

if selected_project_option:
    selected_project = project_options[selected_project_option]
    selected_project_id = selected_project['id']
    selected_project_key = selected_project['key']
    selected_project_name = selected_project['name']
    
    


