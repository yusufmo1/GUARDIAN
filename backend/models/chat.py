"""
Chat Models

Manages chat sessions and messages with Google Drive persistence
for the GUARDIAN system's conversational AI interface.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from datetime import datetime
from .base import BaseModel

class MessageType(PyEnum):
    """Chat message type enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatSession(BaseModel):
    """
    Chat session model for managing conversation sessions.
    
    Each user can have multiple chat sessions, each representing
    a conversation thread with the AI assistant.
    
    Attributes:
        user_id: Foreign key to users table
        session_name: Human-readable name for the session
        google_drive_file_id: Google Drive file ID for session backup
        is_active: Whether the session is currently active
        
    Relationships:
        user: The user this session belongs to
        messages: All messages in this session
    """
    __tablename__ = 'chat_sessions'
    
    # Foreign key to users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Session information
    session_name = Column(String(255))
    google_drive_file_id = Column(String(255), index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="chat_session", cascade="all, delete-orphan")
    
    def generate_session_name(self):
        """Generate a default session name based on creation time."""
        if not self.session_name:
            self.session_name = f"Chat Session - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_message_count(self) -> int:
        """Get the total number of messages in this session."""
        return len(self.messages)
    
    def get_last_message(self):
        """Get the most recent message in this session."""
        if self.messages:
            return max(self.messages, key=lambda m: m.created_at)
        return None
    
    def get_conversation_summary(self, max_length: int = 100) -> str:
        """
        Get a summary of the conversation for display.
        
        Args:
            max_length: Maximum length of summary
            
        Returns:
            str: Truncated conversation summary
        """
        last_message = self.get_last_message()
        if not last_message:
            return "No messages yet"
        
        content = last_message.content
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return content
    
    def set_drive_file_id(self, file_id: str):
        """Set the Google Drive file ID for this session."""
        self.google_drive_file_id = file_id
    
    def has_drive_backup(self) -> bool:
        """Check if session is backed up to Google Drive."""
        return bool(self.google_drive_file_id)
    
    def deactivate(self):
        """Mark session as inactive."""
        self.is_active = False
    
    def activate(self):
        """Mark session as active."""
        self.is_active = True
    
    def to_dict(self, include_messages: bool = False) -> dict:
        """
        Convert session to dictionary.
        
        Args:
            include_messages: Whether to include all messages
            
        Returns:
            dict: Session data
        """
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'session_name': self.session_name,
            'google_drive_file_id': self.google_drive_file_id,
            'has_drive_backup': self.has_drive_backup(),
            'is_active': self.is_active,
            'message_count': self.get_message_count(),
            'last_message_preview': self.get_conversation_summary(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_messages:
            data['messages'] = [msg.to_dict() for msg in sorted(self.messages, key=lambda m: m.created_at)]
        
        return data
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, name={self.session_name}, messages={self.get_message_count()})>"

class ChatMessage(BaseModel):
    """
    Chat message model for individual messages within sessions.
    
    Stores individual messages from users and AI assistant responses
    with metadata for conversation tracking.
    
    Attributes:
        chat_session_id: Foreign key to chat_sessions table
        message_type: Type of message (user, assistant, system)
        content: Message content text
        message_metadata: Additional metadata (JSON)
        
    Relationships:
        chat_session: The session this message belongs to
    """
    __tablename__ = 'chat_messages'
    
    # Foreign key to chat_sessions
    chat_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey('chat_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Message information
    message_type = Column(
        SQLEnum(MessageType, name='message_type'),
        nullable=False,
        index=True
    )
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON)
    
    # Relationships
    chat_session = relationship("ChatSession", back_populates="messages")
    
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.message_type == MessageType.USER
    
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.message_type == MessageType.ASSISTANT
    
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.message_type == MessageType.SYSTEM
    
    def get_word_count(self) -> int:
        """Get the word count of the message content."""
        return len(self.content.split())
    
    def get_character_count(self) -> int:
        """Get the character count of the message content."""
        return len(self.content)
    
    def add_metadata(self, key: str, value):
        """Add metadata to the message."""
        if not self.message_metadata:
            self.message_metadata = {}
        self.message_metadata[key] = value
    
    def get_metadata(self, key: str, default=None):
        """Get metadata value by key."""
        if not self.message_metadata:
            return default
        return self.message_metadata.get(key, default)
    
    def to_dict(self) -> dict:
        """Convert message to dictionary."""
        return {
            'id': str(self.id),
            'chat_session_id': str(self.chat_session_id),
            'message_type': self.message_type.value,
            'content': self.content,
            'word_count': self.get_word_count(),
            'character_count': self.get_character_count(),
            'metadata': self.message_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def create_user_message(cls, session_id: str, content: str, metadata: dict = None):
        """
        Create a user message.
        
        Args:
            session_id: Chat session ID
            content: Message content
            metadata: Optional metadata
            
        Returns:
            ChatMessage: New user message instance
        """
        return cls(
            chat_session_id=session_id,
            message_type=MessageType.USER,
            content=content,
            message_metadata=metadata
        )
    
    @classmethod
    def create_assistant_message(cls, session_id: str, content: str, metadata: dict = None):
        """
        Create an assistant message.
        
        Args:
            session_id: Chat session ID
            content: Message content
            metadata: Optional metadata
            
        Returns:
            ChatMessage: New assistant message instance
        """
        return cls(
            chat_session_id=session_id,
            message_type=MessageType.ASSISTANT,
            content=content,
            message_metadata=metadata
        )
    
    @classmethod
    def create_system_message(cls, session_id: str, content: str, metadata: dict = None):
        """
        Create a system message.
        
        Args:
            session_id: Chat session ID
            content: Message content
            metadata: Optional metadata
            
        Returns:
            ChatMessage: New system message instance
        """
        return cls(
            chat_session_id=session_id,
            message_type=MessageType.SYSTEM,
            content=content,
            message_metadata=metadata
        )
    
    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ChatMessage(id={self.id}, type={self.message_type.value}, content='{content_preview}')>"