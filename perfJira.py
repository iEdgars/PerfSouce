import requests
import sqlite3
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