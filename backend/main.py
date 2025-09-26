# Import necessary modules from FastAPI, Pydantic, and other custom files.
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel
import re
# Import the Chatbot class from chatbot.py for handling conversational logic.
from chatbot import Chatbot
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
from utils import verify_token


# Instantiate the Chatbot class, which handles the conversational logic and agent interactions.
chatbot = Chatbot()

# Process the predefined document on startup
document_path = "C:\\ValueHealth\\Training\\LangGraph\\Simple_langgraph\\langchain-academy\\chatbot\\backend\\rag\\Document.pdf"    
collection_name = "hp_victus_faq"

# Check if the document exists before processing
if os.path.exists(document_path):
    # Only process if the collection does not exist to avoid re-embedding on every startup
    # In a real-world scenario, you might have more robust versioning/checking
    try:
        # Attempt to create vector store, if it already exists, this will return the existing one
        from rag.rag import load_documents, split_documents, create_vector_store, get_retriever
        documents = load_documents(document_path)
        splits = split_documents(documents)
        vectorstore = create_vector_store(splits, collection_name=collection_name)
        retriever = get_retriever(vectorstore, k=10)
        chatbot.set_retriever(retriever)
        print(f"Document '{document_path}' processed and retriever set for chatbot.")
    except Exception as e:
        print(f"Error processing document {document_path} on startup: {e}")
else:
    print(f"Document '{document_path}' not found. RAG functionality might be limited.")

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
    
    # Use filename (without extension) as collection name and sanitize it
    base_name = file.filename.split('.')[0]
    collection_name = re.sub(r'[^a-zA-Z0-9._-]', '_', base_name)
    # Ensure the name starts and ends with an alphanumeric character
    collection_name = re.sub(r'^[^a-zA-Z0-9]+', '', collection_name)
    collection_name = re.sub(r'[^a-zA-Z0-9]+$', '', collection_name)
    # Ensure it's not empty after sanitization
    if not collection_name:
        collection_name = "uploaded_document"
    process_document_for_rag(file_path, collection_name=collection_name)
    
    # Import RAG utility functions here to avoid circular dependencies
    from rag.rag import load_documents, split_documents
    documents = load_documents(file_path)
    splits = split_documents(documents)
    vectorstore = create_vector_store(splits, collection_name=collection_name)
    retriever = get_retriever(vectorstore, k=10)
    chatbot.set_retriever(retriever)

    return {"message": f"File '{file.filename}' uploaded successfully and processed for RAG."}

# Entry point for running the FastAPI application using Uvicorn.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
