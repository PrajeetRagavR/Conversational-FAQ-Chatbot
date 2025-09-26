import streamlit as st
import requests
import json

# FastAPI authentication endpoints
AUTH_BASE_URL = "http://localhost:8000/auth"
REGISTER_URL = f"{AUTH_BASE_URL}/register"
LOGIN_URL = f"{AUTH_BASE_URL}/token"

def register_user(username, email, password):
    """Register a new user and return the response."""
    try:
        response = requests.post(
            REGISTER_URL,
            json={"username": username, "email": email, "password": password}
        )
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return 500, {"detail": f"Connection error: {str(e)}"}

def login_user(username, password):
    """Login a user and return the access token."""
    try:
        # OAuth2 expects form data, not JSON
        response = requests.post(
            LOGIN_URL,
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            response_data = response.json()
            st.session_state.access_token = response_data["access_token"]
            st.session_state.user_id = response_data["user_id"] # Store user_id
            return response.status_code, response_data
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        return 500, {"detail": f"Connection error: {str(e)}"}

def is_authenticated():
    """Check if the user is authenticated."""
    return "access_token" in st.session_state

def get_auth_header():
    """Get the authorization header for API requests."""
    if is_authenticated():
        return {"Authorization": f"Bearer {st.session_state.access_token}"}
    return {}

def logout():
    """Log out the user by clearing the session state."""
    for key in ["access_token", "username", "user_id"]:
        if key in st.session_state:
            del st.session_state[key]