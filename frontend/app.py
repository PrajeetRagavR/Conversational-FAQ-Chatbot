import streamlit as st
import requests
import sys
import os
import re
from fastapi import HTTPException

# Add the parent directory to the Python path to allow importing from the 'backend' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.utils import verify_token
# FastAPI endpoint
FASTAPI_URL = "http://localhost:8000/chat"
UPLOAD_URL = "http://localhost:8000/upload_document"

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

def token_input_section():
    st.header("Token Configuration :key:")
    token = st.text_input("Enter your Token", type="password", key="bearer_token_input")
    
    if token:
        # Local validation: must be ABC + 3 digits
        if re.fullmatch(r"ABC\d{3}", token):
            st.session_state["bearer_token"] = token
            st.success("Token Authorized!")
        else:
            st.session_state["bearer_token"] = None
            st.warning("Invalid token format. Must be ABC followed by 3 digits (e.g., ABC123).")
    else:
        st.session_state["bearer_token"] = None
        st.warning("Please enter bearer token to continue to the chatbot")

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
#             headers = {"Authorization": st.session_state.bearer_token} if st.session_state.get("bearer_token") else {}
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
    with st.sidebar:  # 👈 move everything inside sidebar
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
                headers = {"Authorization": st.session_state.bearer_token} if st.session_state.get("bearer_token") else {}
                try:
                    response = requests.post(UPLOAD_URL, files=files, headers=headers)
                    response.raise_for_status()
                    st.success(response.json()["message"])
                    st.session_state["uploaded_file"] = None
                except requests.exceptions.RequestException as e:
                    st.error(f"Error uploading file: {e}")
            else:
                st.warning("Please upload a file first.")


def chat_interface_section():
    st.header("Chat with your documents :speech_balloon:")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for i, message in enumerate(st.session_state.messages):
        with st.container(key=f"chat_message_container_{i}"):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if prompt := st.chat_input("What is up?"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        headers = {"Authorization": st.session_state.bearer_token} if st.session_state.get("bearer_token") else {}
        try:
            response = requests.post(
                FASTAPI_URL,
                json={
                    "user_id": "streamlit_user",
                    "thread_id": "streamlit_thread",
                    "content": prompt
                },
                headers=headers
            )
            response.raise_for_status()
            chatbot_response = response.json()["response"]
        except requests.exceptions.RequestException as e:
            chatbot_response = f"Error: Could not connect to the chatbot backend. Is it running? ({e})"

        with st.chat_message("assistant"):
            st.markdown(chatbot_response)
        st.session_state.messages.append({"role": "assistant", "content": chatbot_response})

def main():
    st.set_page_config(page_title="Chatbot UI", layout="centered")
    st.title("FAQ Chatbot UI :")
    apply_custom_styles()
    token_input_section()
    st.markdown("---")

    if st.session_state.get("bearer_token"):
        file_uploader_section()
        st.markdown("---")
        chat_interface_section()
    else:
        st.warning("example : 'ABC123'")

if __name__ == "__main__":
    main()
