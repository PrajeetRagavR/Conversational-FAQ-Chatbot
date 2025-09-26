from sqlalchemy import create_engine, Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()

class ChatDB:
    def __init__(self, database_url: str = None):
        load_dotenv()
        self.DATABASE_URL = database_url or os.getenv("DATABASE_URL", "postgresql://postgres:user@localhost/chatbot_db")
        self.engine = create_engine(self.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        if not database_exists(self.engine.url):
            create_database(self.engine.url)
        Base.metadata.create_all(bind=self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

chat_db_instance = ChatDB()

def get_db():
    yield from chat_db_instance.get_db()

# Define User model
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")

# Define ChatSession model
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_name = Column(String, default="New Chat")
    created_at = Column(DateTime, default=datetime.now)
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session")

# Define ChatMessage model
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    user_query= Column(String, nullable=True)
    llm_resp= Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")