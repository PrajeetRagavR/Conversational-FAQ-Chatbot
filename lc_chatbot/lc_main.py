# Import necessary modules from FastAPI, Pydantic, and other custom files.
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Security
from pydantic import BaseModel
# Import the Chatbot class from langchain_chatbot.py for handling conversational logic.
from langchain_chatbot import Chatbot
# Import the regular expression module for token validation.
import re
# Import the os module for interacting with the operating system, like path manipulation.
import os
# Import RAG (Retrieval-Augmented Generation) related functions for document processing.
from rag.rag import process_document_for_rag, create_vector_store, get_retriever
# Import Annotated for type hinting with metadata and APIKeyHeader for security.
from typing import Annotated
from fastapi.security import APIKeyHeader

# Initialize the FastAPI application.
app = FastAPI()

# Import CORS middleware to handle Cross-Origin Resource Sharing.
from fastapi.middleware.cors import CORSMiddleware

# Define the allowed origins for CORS. These are the client URLs that can access this API.
origins = [
    "http://localhost:8501",  # Streamlit frontend application
    "http://localhost:8000"   # FastAPI backend itself (e.g., for Swagger UI testing)
]

# Add the CORS middleware to the FastAPI application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret token format requirement (example: ABC123).
# In production, use JWT or a secure token service.
SECRET_TOKEN_REGEX = r"^ABC\d{3}$"

# Asynchronous function to verify the authentication token.
async def verify_token(token: Annotated[str, Security(APIKeyHeader(name="Authorization", auto_error=False))]):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Require 'Bearer ' prefix
    if not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '"
        )

    # Extract the raw token value (e.g., "ABC123")
    token_value = token[len("Bearer "):]

    # Validate the token format
    if not re.match(SECRET_TOKEN_REGEX, token_value):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )

    return token_value  # return validated token

# Instantiate the Chatbot class, which handles the conversational logic and agent interactions.
chatbot = Chatbot()

# Define the Pydantic model for incoming chat messages.
class Message(BaseModel):
    user_id: str
    thread_id: str
    content: str

# Define a POST endpoint for chat interactions.
@app.post("/chat")
async def chat(message: Message, token: Annotated[str, Depends(verify_token)]):
    response = chatbot.invoke(message.content, message.thread_id, message.user_id)
    return {"response": response}

# Define a POST endpoint for uploading documents for RAG processing.
@app.post("/upload_document")
async def upload_document(token: Annotated[str, Depends(verify_token)], file: UploadFile = File(...)):
    upload_dir = "./backend/rag/uploaded_documents"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    # Use filename (without extension) as collection name
    collection_name = file.filename.split('.')[0]
    process_document_for_rag(file_path, collection_name=collection_name)
    
    # Import RAG utility functions here to avoid circular dependencies
    from rag.rag import load_documents, split_documents
    documents = load_documents(file_path)
    splits = split_documents(documents)
    vectorstore = create_vector_store(splits, collection_name=collection_name)
    retriever = get_retriever(vectorstore)
    chatbot.set_retriever(retriever)

    return {"message": f"File '{file.filename}' uploaded successfully and processed for RAG."}

# Entry point for running the FastAPI application using Uvicorn.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
