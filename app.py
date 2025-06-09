# app.py (FINAL VERSION with MATPLOTLIB Visualizations)

import streamlit as st
import requests
import os
import pandas as pd
import matplotlib.pyplot as plt  # Import Matplotlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration & State Initialization ---
st.set_page_config(page_title="GitLab Profiler", page_icon="🤖", layout="wide")

GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_API_TOKEN")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_data" not in st.session_state:
    st.session_state.user_data = None

# --- API Helper Functions (No changes here) ---

def fetch_gitlab_user(username: str):
    """Fetches a single user's complete profile from GitLab."""
    headers = {"Authorization": f"Bearer {GITLAB_TOKEN}"}
    api_url = f"{GITLAB_URL}/api/v4/users?username={username}"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        users = response.json()
        return users[0] if users else None
    except requests.exceptions.RequestException as e:
        st.error(f"API Request Failed: {e}")
        return None

def fetch_user_projects(user_id: int):
    """Fetches projects for a given user ID."""
    headers = {"Authorization": f"Bearer {GITLAB_TOKEN}"}
    api_url = f"{GITLAB_URL}/api/v4/users/{user_id}/projects?statistics=true&per_page=100"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return []

def get_project_languages(project_id: int):
    """Fetches language statistics for a single project."""
    headers = {"Authorization": f"Bearer {GITLAB_TOKEN}"}
    api_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/languages"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return {}

# --- UI Rendering Functions ---

def display_full_profile(user):
    """Renders the 'A to Z' user profile details."""
    st.subheader(f"Full Profile: {user.get('name')}")
    col1, col2 = st.columns([1, 3])
    with col1:
        if user.get('avatar_url'):
            st.image(user['avatar_url'], width=150)
    with col2:
        st.markdown(f"**Username:** `{user.get('username')}`")
        st.markdown(f"**ID:** `{user.get('id')}`")
        st.markdown(f"**State:** `{user.get('state')}`")
        st.markdown(f"**Joined:** {user.get('created_at', 'N/A').split('T')[0]}")
        st.markdown(f"**Profile:** [View on GitLab]({user.get('web_url')})")
    with st.expander("See all available profile details"):
        st.json(user)

def display_project_visuals(projects):
    """Renders the advanced project visualizations using MATPLOTLIB."""
    st.subheader("Project Visualizations")

    if not projects:
        st.warning("No projects found that are visible to you.")
        return

    df = pd.DataFrame(projects)

    st.markdown("#### Project Popularity & Activity")
    df_stats = df[['name', 'star_count', 'forks_count']]
    if 'statistics' in df.columns:
        df_stats['commit_count'] = df['statistics'].apply(lambda x: x.get('commit_count', 0) if isinstance(x, dict) else 0)
    st.bar_chart(df_stats.set_index('name'))

    st.markdown("#### Language Breakdown per Project (Matplotlib)")
    st.info("Fetching language data for each project... this may take a moment.")

    cols = st.columns(3)
    col_idx = 0
    for project in projects[:9]:  # Limit to first 9 projects
        with cols[col_idx]:
            with st.spinner(f"Getting languages for {project['name']}..."):
                languages = get_project_languages(project['id'])
                if languages:
                    # --- MATPLOTLIB PIE CHART CREATION ---
                    lang_df = pd.DataFrame(list(languages.items()), columns=['Language', 'Percentage'])
                    
                    # Create a figure and axes object
                    fig, ax = plt.subplots(figsize=(6, 6))
                    
                    # Plot the pie chart on the axes
                    ax.pie(lang_df['Percentage'], labels=lang_df['Language'], autopct='%1.1f%%', startangle=90)
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                    ax.set_title(project['name'], fontsize=14)
                    
                    # Display the figure in Streamlit
                    st.pyplot(fig)
                    
                    # IMPORTANT: Close the figure to free up memory
                    plt.close(fig)
                    # --- END OF MATPLOTLIB SECTION ---
                else:
                    st.write(f"**{project['name']}**")
                    st.caption("No language data available.")
        col_idx = (col_idx + 1) % 3

# --- Main App Logic (No changes here) ---

st.title("🤖 GitLab Advanced Profiler")

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

if not st.session_state.messages:
    add_message("assistant", "Hi there! Enter a GitLab username to begin profiling.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter a username..."):
    add_message("user", prompt)
    st.session_state.user_data = None
    with st.spinner(f"Searching for '{prompt}'..."):
        user_data = fetch_gitlab_user(prompt)
        if user_data:
            st.session_state.user_data = user_data
            add_message("assistant", f"Found user **{user_data['name']}** (`{user_data['username']}`). What would you like to see?")
        else:
            add_message("assistant", f"Sorry, I couldn't find a user with the username '{prompt}'.")
    st.rerun()

if st.session_state.user_data:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("👤 View Full Profile"):
            display_full_profile(st.session_state.user_data)
    with col2:
        if st.button("📊 View Project Visuals"):
            projects = fetch_user_projects(st.session_state.user_data['id'])
            display_project_visuals(projects)