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

from database import get_db, chat_db_instance, ChatSession, ChatMessage
from auth import get_current_active_user
from routes import auth_routes
from schema import ChatMessageCreate # Import new schemas
from sqlalchemy.orm import Session

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
# Include authentication routes
app.include_router(auth_routes.router, prefix="/auth")


# Instantiate the Chatbot class, which handles the conversational logic and agent interactions.
chatbot = Chatbot()

# Process the predefined document on startup
document_path = "C:\\ValueHealth\\Training\\LangGraph\\Simple_langgraph\\langchain-academy\\chatbot\\backend\\rag\\Document.pdf"    
collection_name = "hp_victus_faq"

@app.on_event("startup")
async def startup_event():
    chat_db_instance.create_tables()
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
    chat_session_id: str # Renamed from thread_id
    content: str

# Define a POST endpoint for chat interactions.
@app.post("/chat")
async def chat(message: Message, current_user = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Check if the query has been asked before and a non-null LLM response exists
    cached_message = db.query(ChatMessage).filter(
        ChatMessage.chat_session_id == message.chat_session_id,
        ChatMessage.user_query == message.content,
        ChatMessage.llm_resp.isnot(None) & (ChatMessage.llm_resp != "")
    ).first()

    if cached_message:
        print(f"Fetching response from cache for query: {message.content}")
        return {"response": cached_message.llm_resp, "user_id": str(current_user.id), "chat_session_id": message.chat_session_id}

    # If not cached or llm_resp is null, invoke the chatbot
    response = chatbot.invoke(message.content, message.chat_session_id, str(current_user.id))
    return {"response": response, "user_id": str(current_user.id), "chat_session_id": message.chat_session_id}

@app.post("/save_chat_message", status_code=status.HTTP_201_CREATED)
async def save_chat_message(chat_message: ChatMessageCreate, db: Session = Depends(get_db), current_user = Depends(get_current_active_user)):
    # Ensure the user_id in the chat_message matches the authenticated user's ID
    if chat_message.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User ID mismatch")

    # Check if chat session exists, if not, create a new one
    chat_session = db.query(ChatSession).filter(
        ChatSession.id == chat_message.chat_session_id,
        ChatSession.user_id == chat_message.user_id
    ).first()

    if not chat_session:
        new_session = ChatSession(
            id=chat_message.chat_session_id,
            user_id=chat_message.user_id,
            session_name="New Chat"
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        chat_session = new_session
        print(f"Created new chat session: {chat_session.id} for user: {chat_session.user_id}")

    # Create a single ChatMessage entry for both user query and LLM response
    new_message = ChatMessage(
        chat_session_id=chat_message.chat_session_id,
        user_query=chat_message.user_query,
        llm_resp=chat_message.llm_resp
    )
    print(f"Saving message - User Query: {chat_message.user_query}, /nLLM Response: {chat_message.llm_resp} /nfor session: {chat_message.chat_session_id}")

    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    print(f"Successfully saved message with ID: {new_message.id}")
    return {"message": "Chat message saved successfully"}

# Define a POST endpoint for uploading documents for RAG processing.
@app.post("/upload_document")
async def upload_document(file: UploadFile = File(...), current_user = Depends(get_current_active_user)):
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
