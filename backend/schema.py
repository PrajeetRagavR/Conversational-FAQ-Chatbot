from pydantic import BaseModel, Field, EmailStr
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class UserProfile(BaseModel):
    user_name: str = Field(description="The name of the user.")
    user_location: str = Field(description="The location of the user.")
    interests: list[str] = Field(description="A list of the user's interests.")

# Authentication schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: UUID # Add user_id to the Token schema

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[UUID] = None

class ChatSessionCreate(BaseModel):
    session_name: Optional[str] = "New Chat"

class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    session_name: str
    created_at: datetime
    last_updated: datetime

class ChatMessageCreate(BaseModel):
    chat_session_id: UUID
    user_id: UUID
    user_query: Optional[str] = None
    llm_resp: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: UUID
    chat_session_id: UUID
    content: str
    is_user: bool
    timestamp: datetime

def get_across_thread_memory():
    return InMemoryStore()

def get_within_thread_memory():
    return MemorySaver()