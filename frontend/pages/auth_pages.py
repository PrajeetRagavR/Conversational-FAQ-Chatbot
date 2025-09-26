import streamlit as st
from auth import register_user, login_user, logout

def show_login_page():
    """Display the login page."""
    st.header("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not username or not password:
                st.error("Please fill in all fields")
                return
                
            status_code, response = login_user(username, password)
            
            if status_code == 200:
                st.session_state.access_token = response["access_token"]
                st.session_state.username = username
                st.success("Login successful!")
                st.session_state.show_page = "chat"
                st.rerun()
            else:
                st.error(f"Login failed: {response.get('detail', 'Unknown error')}")
    
    st.markdown("---")
    st.markdown("Don't have an account? [Register](#register)")

def show_register_page():
    """Display the registration page."""
    st.header("Register")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if not username or not email or not password or not confirm_password:
                st.error("Please fill in all fields")
                return
                
            if password != confirm_password:
                st.error("Passwords do not match")
                return
                
            status_code, response = register_user(username, email, password)
            
            if status_code == 200:
                st.success("Registration successful! Please login.")
                st.session_state.show_page = "login"
                st.rerun()
            else:
                st.error(f"Registration failed: {response.get('detail', 'Unknown error')}")
    
    st.markdown("---")
    st.markdown("Already have an account? [Login](#login)")

def show_logout_button():
    """Display the logout button."""
    if st.button("Logout"):
        logout()
        st.success("Logged out successfully!")
        st.rerun()