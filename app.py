import streamlit as st
import pandas as pd
import sqlite3
from perfJira import confirm_connection

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
    if confirm_connection(jira_url, username, api_key):
        st.success("Connection successful!")
    else:
        st.error("Connection failed. Please check your credentials and URL.")

# if st.button("Fetch Data"):
#     data = fetch_jira_issues(username, api_key, jira_url)
#     if data is not None:
#         write_df_to_db(data)
#         st.success("Data fetched and saved successfully!")

# if st.button("Load Data"):
#     data = read_from_sqlite()
#     st.dataframe(data)