import streamlit as st
import requests
import sys
import os
import re
import uuid # Import uuid for generating unique session IDs
from fastapi import HTTPException

# Add the parent directory to the Python path to allow importing from the 'backend' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import authentication functions
from auth import is_authenticated, get_auth_header
from pages.auth_pages import show_login_page, show_register_page, show_logout_button

# FastAPI endpoint
FASTAPI_URL = "http://localhost:8000/chat"
UPLOAD_URL = "http://localhost:8000/upload_document"
SAVE_MESSAGE_URL = "http://localhost:8000/save_chat_message" # New endpoint for saving messages

def apply_custom_styles():
    st.markdown("""
    <style>
    .reportview-container {
        background: #f0f2f6;
    }
    .sidebar .sidebar-content {
        background: #f0f2f6;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
        border: none;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #ccc;
        padding: 10px;
    }
    .stFileUploader label {
        font-size: 18px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Authentication is now handled by OAuth2 instead of token input

# def file_uploader_section():
#     st.header("Document Upload :page_facing_up:")
#     uploaded_file = st.file_uploader("Upload a document for RAG", type=["pdf", "txt"], key="file_uploader")

#     if uploaded_file is not None:
#         st.session_state["uploaded_file"] = uploaded_file
#         st.info(f"File '{uploaded_file.name}' uploaded. Click 'Process Document' to add it to RAG.")

#     if st.button("Process Document :rocket:", key="process_button"):
#         if "uploaded_file" in st.session_state and st.session_state["uploaded_file"] is not None:
#             file_to_process = st.session_state["uploaded_file"]
#             st.write("Processing document...")
#             files = {"file": (file_to_process.name, file_to_process.getvalue(), file_to_process.type)}
#             headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.get("access_token") else {}
#             try:
#                 response = requests.post(UPLOAD_URL, files=files, headers=headers)
#                 response.raise_for_status()
#                 st.success(response.json()["message"])
#                 st.session_state["uploaded_file"] = None
#             except requests.exceptions.RequestException as e:
#                 st.error(f"Error uploading file: {e}")
#         else:
#             st.warning("Please upload a file first.")

def file_uploader_section():
    with st.sidebar:
        st.header("Document Upload :page_facing_up:")
        uploaded_file = st.file_uploader("Upload a document for RAG", type=["pdf", "txt"], key="file_uploader")

        if uploaded_file is not None:
            st.session_state["uploaded_file"] = uploaded_file
            st.info(f"File '{uploaded_file.name}' uploaded. Click 'Process Document' to add it to RAG.")

        if st.button("Process Document :rocket:", key="process_button"):
            if "uploaded_file" in st.session_state and st.session_state["uploaded_file"] is not None:
                file_to_process = st.session_state["uploaded_file"]
                st.write("Processing document...")
                files = {"file": (file_to_process.name, file_to_process.getvalue(), file_to_process.type)}
                headers = get_auth_header()
                try:
                    response = requests.post(UPLOAD_URL, files=files, headers=headers)
                    response.raise_for_status()
                    st.success("Document processed successfully!")
                    st.session_state["uploaded_file"] = None
                except requests.exceptions.RequestException as e:
                    st.error(f"Error uploading file: {e}")
            else:
                st.warning("Please upload a file first.")



def chat_interface_section():
    st.header("Chat with your documents :speech_balloon:")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Initialize chat_session_id if not present
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())

    for i, message in enumerate(st.session_state.messages):
        with st.container(key=f"chat_message_container_{i}"):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        headers = {"Authorization": f"Bearer {st.session_state.access_token}"} if st.session_state.get("access_token") else {}
        user_id = st.session_state.user_id # Assuming user_id is stored in session_state after login

        try:
            # Send user query to the chat endpoint
            response = requests.post(
                FASTAPI_URL,
                json={
                    "user_id": user_id,
                    "chat_session_id": st.session_state.chat_session_id,
                    "content": prompt
                },
                headers=headers
            )
            response.raise_for_status()
            chatbot_response_data = response.json()
            chatbot_response = chatbot_response_data["response"]
            returned_chat_session_id = chatbot_response_data["chat_session_id"]

            # Save user message and LLM response to the database in a single entry
            chatbot_response_str = "".join(chatbot_response) if isinstance(chatbot_response, list) else chatbot_response
            requests.post(
                SAVE_MESSAGE_URL,
                json={
                    "chat_session_id": returned_chat_session_id,
                    "user_id": user_id,
                    "user_query": prompt,
                    "llm_resp": chatbot_response_str
                },
                headers=headers
            )

        except requests.exceptions.RequestException as e:
            chatbot_response = f"Error: Could not connect to the chatbot backend. Is it running? ({e})"

        with st.chat_message("assistant"):
            st.markdown(chatbot_response)
        st.session_state.messages.append({"role": "assistant", "content": chatbot_response})

        # Remove the separate LLM response saving block
        # try:
        #     # Save LLM response to the database
        #     requests.post(
        #         SAVE_MESSAGE_URL,
        #         json={
        #             "chat_session_id": returned_chat_session_id,
        #             "user_id": user_id,
        #             "llm_resp": chatbot_response
        #         },
        #         headers=headers
        #     )
        # except requests.exceptions.RequestException as e:
        #     st.error(f"Error saving LLM response: {e}")

def main():
    st.set_page_config(page_title="Chatbot UI", layout="centered")
    apply_custom_styles()
    st.title("FAQ & Web Search Chatbot UI :")
    
    # Initialize session state for page navigation
    if "show_page" not in st.session_state:
        st.session_state.show_page = "login"
    
    # Initialize chat_session_id if not present
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = str(uuid.uuid4())

    # Handle page navigation
    if st.session_state.show_page == "login":
        show_login_page()
        if st.button("Register instead"):
            st.session_state.show_page = "register"
            st.rerun()
    elif st.session_state.show_page == "register":
        show_register_page()
        if st.button("Login instead"):
            st.session_state.show_page = "login"
            st.rerun()
    elif st.session_state.show_page == "chat" and is_authenticated():
        show_chat_interface()
    else:
        st.session_state.show_page = "login"
        st.rerun()

def show_chat_interface():
    # Show logout button in sidebar
    with st.sidebar:
        show_logout_button()
        st.markdown("---")
    
    # Show file uploader in sidebar
    file_uploader_section()
    st.markdown("---")
    chat_interface_section()

if __name__ == "__main__":
    main()
