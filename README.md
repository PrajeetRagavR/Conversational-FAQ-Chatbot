# Langchain Chatbot

This project implements a chatbot using Langchain, FastAPI for the backend, and Streamlit for the frontend. It includes Retrieval-Augmented Generation (RAG) capabilities and user authentication.

## Table of Contents
- [Project Structure](#project-structure)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Installation](#installation)
- [Running the Application](#running-the-application)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [RAG Functionality](#rag-functionality)
- [Authentication](#authentication)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Project Structure

```
.env
.gitignore
README.md
backend/
│   auth.py
│   chatbot.py
│   database.py
│   llm.py
│   main.py
│   rag/
│   │   Document.pdf
│   │   rag.py
│   routes/
│   │   auth.py
│   │   auth_routes.py
│   schema.py
│   tools.py
frontend/
│   app.py
│   auth.py
│   pages/
│       auth_pages.py
lc_chatbot/
│   langchain_chatbot.py
│   lc_main.py
│   utils.py
requirements.txt
```

## Setup

### Prerequisites

Make sure you have the following installed:

*   Python 3.9+
*   pip (Python package installer)

### Environment Variables

Create a `.env` file in the root directory of the project with the following variables:

*   `GOOGLE_API_KEY`: Your Google API key for language models.
*   `TAVILY_API_KEY`: Your Tavily API key for search.
*   `SECRET_KEY`: A strong secret key for JWT authentication. You can generate one using `openssl rand -hex 32`.

### Installation

1.  Navigate to the project root directory:

    ```bash
    cd langchain-academy/chatbot
    ```

2.  Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

### Backend

1.  Navigate to the `backend` directory:

    ```bash
    cd backend
    ```

2.  Run the FastAPI application using Uvicorn:

    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

    The backend will be accessible at `http://localhost:8000`.

### Frontend

1.  Navigate to the `frontend` directory:

    ```bash
    cd frontend
    ```

2.  Run the Streamlit application:

    ```bash
    streamlit run app.py
    ```

    The frontend will be accessible at `http://localhost:8501`.
## RAG Functionality

This project utilizes Retrieval-Augmented Generation (RAG) to enhance the chatbot's responses. The RAG pipeline involves the following steps:

1.  **Document Loading**: Supports loading PDF and text documents using `PyPDFLoader` and `TextLoader`.
2.  **Document Splitting**: Documents are split into smaller, manageable chunks using `RecursiveCharacterTextSplitter` to facilitate efficient retrieval.
3.  **Vector Store Creation**: The split documents are embedded using `HuggingFaceEmbeddings` (specifically, "all-MiniLM-L6-v2") and stored in a `Chroma` vector database. This allows for semantic search and retrieval of relevant document chunks.
4.  **Retriever**: A retriever is created from the vector store to fetch the most relevant document chunks based on a user's query, which are then used to augment the language model's response.

The `backend/rag/rag.py` module handles these operations, allowing for the processing of documents and the creation of a persistent vector store.
## Authentication

User authentication is implemented using FastAPI and JWT (JSON Web Tokens). The process involves:

1.  **User Registration**: New users can register by providing a username, email, and password. The password is hashed using `bcrypt` before being stored in the database. Unique usernames and emails are enforced.
2.  **User Login**: Existing users can log in with their username and password. Upon successful authentication, a JWT access token is generated and returned.
3.  **JWT Access Tokens**: Access tokens are short-lived and are used to authenticate subsequent requests to protected endpoints. The `SECRET_KEY` for signing these tokens is loaded from the environment variables.
4.  **Current User Retrieval**: Protected routes use `OAuth2PasswordBearer` to extract and validate the JWT token from the request header, allowing the application to identify the currently authenticated user.

Key files involved in authentication:

*   `backend/auth.py`: Handles password hashing, JWT token creation and validation, and user retrieval functions.
*   `backend/routes/auth_routes.py`: Defines API endpoints for user registration (`/register`) and login (`/token`).
## Usage

Once both the backend and frontend applications are running:

1.  **Access the Frontend**: Open your web browser and navigate to `http://localhost:8501` to access the Streamlit chatbot interface.
2.  **Register/Login**: If you are a new user, register for an account. Otherwise, log in with your existing credentials.
3.  **Interact with the Chatbot**: After logging in, you can start interacting with the chatbot. Type your queries into the input field and press Enter or click the send button.
4.  **RAG Functionality**: The chatbot will use its RAG capabilities to provide informed responses, potentially retrieving information from the loaded documents.
## API Endpoints

The backend FastAPI application exposes the following API endpoints:

### Authentication Endpoints (`/auth`)

*   **`POST /auth/register`**
    *   **Description**: Registers a new user.
    *   **Request Body**: `UserCreate` schema (username, email, password).
    *   **Response**: `UserResponse` schema (user ID, username, email, creation timestamp).

*   **`POST /auth/token`**
    *   **Description**: Authenticates a user and returns a JWT access token.
    *   **Request Body**: `OAuth2PasswordRequestForm` (username, password).
    *   **Response**: `Token` schema (access token, token type, user ID).

*   **`POST /auth/logout`**
    *   **Description**: Provides a logout message. (Note: JWT tokens are stateless, client-side token discard is required for true logout).
    *   **Response**: JSON message indicating successful logout.

### Chat Endpoints

*   **`POST /chat`**
    *   **Description**: Sends a message to the chatbot and receives a response. Utilizes RAG if a retriever is set.
    *   **Request Body**: `Message` schema (user_id, chat_session_id, content).
    *   **Response**: JSON object with the chatbot's response, user ID, and chat session ID.

*   **`POST /save_chat_message`**
    *   **Description**: Saves a chat message (user query and LLM response) to the database.
    *   **Request Body**: `ChatMessageCreate` schema (user_id, chat_session_id, user_query, llm_resp).
    *   **Response**: JSON message indicating successful save.

*   **`POST /upload_document`**
    *   **Description**: Uploads a document (PDF or TXT) for RAG processing. The document is processed, and a vector store is created/updated.
    *   **Request Body**: `UploadFile` (file).
    *   **Response**: JSON message indicating successful upload and processing.