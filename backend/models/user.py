"""
User Model

Represents authenticated users in the GUARDIAN system with Google OAuth integration.
Stores user profile information and encrypted Google Drive access tokens.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet
import os
import base64
from datetime import datetime
from .base import BaseModel

class User(BaseModel):
    """
    User model for Google OAuth authenticated users.
    
    Stores user profile information, Google Drive tokens (encrypted),
    and relationships to user's documents and sessions.
    
    Attributes:
        google_id: Unique Google user identifier
        email: User's email address from Google
        name: User's full name from Google
        picture_url: URL to user's Google profile picture
        drive_refresh_token: Encrypted Google Drive refresh token
        drive_access_token: Encrypted Google Drive access token
        drive_token_expiry: When the access token expires
        last_login: Last login timestamp
        is_active: Whether user account is active
        
    Relationships:
        sessions: User's active sessions
        documents: User's uploaded documents
        chat_sessions: User's chat sessions
        vector_sessions: User's vector database sessions
    """
    __tablename__ = 'users'
    
    # Google OAuth fields
    google_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    picture_url = Column(Text)
    
    # Encrypted Google Drive tokens
    drive_refresh_token = Column(LargeBinary)  # Encrypted
    drive_access_token = Column(LargeBinary)   # Encrypted
    drive_token_expiry = Column(DateTime)
    
    # User status
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    vector_sessions = relationship("VectorSession", back_populates="user", cascade="all, delete-orphan")
    
    def __init__(self, **kwargs):
        # Encrypt tokens before storing if provided
        if 'drive_refresh_token' in kwargs and kwargs['drive_refresh_token']:
            kwargs['drive_refresh_token'] = self._encrypt_token(kwargs['drive_refresh_token'])
        if 'drive_access_token' in kwargs and kwargs['drive_access_token']:
            kwargs['drive_access_token'] = self._encrypt_token(kwargs['drive_access_token'])
        super().__init__(**kwargs)
    
    @staticmethod
    def _get_encryption_key():
        """Get encryption key from environment."""
        key = os.getenv('SECRET_KEY')
        if not key:
            raise ValueError("SECRET_KEY environment variable not set")
        
        # Create Fernet key from SECRET_KEY
        key_bytes = key.encode()[:32]  # Fernet needs 32 bytes
        key_bytes = key_bytes.ljust(32, b'0')  # Pad if shorter
        return base64.urlsafe_b64encode(key_bytes)
    
    @staticmethod
    def _encrypt_token(token: str) -> bytes:
        """Encrypt a token for secure storage."""
        if not token:
            return None
        
        fernet = Fernet(User._get_encryption_key())
        return fernet.encrypt(token.encode())
    
    @staticmethod
    def _decrypt_token(encrypted_token: bytes) -> str:
        """Decrypt a token for use."""
        if not encrypted_token:
            return None
            
        fernet = Fernet(User._get_encryption_key())
        return fernet.decrypt(encrypted_token).decode()
    
    def set_drive_refresh_token(self, token: str):
        """Set and encrypt the Google Drive refresh token."""
        self.drive_refresh_token = self._encrypt_token(token) if token else None
    
    def get_drive_refresh_token(self) -> str:
        """Get and decrypt the Google Drive refresh token."""
        return self._decrypt_token(self.drive_refresh_token)
    
    def set_drive_access_token(self, token: str):
        """Set and encrypt the Google Drive access token."""
        self.drive_access_token = self._encrypt_token(token) if token else None
    
    def get_drive_access_token(self) -> str:
        """Get and decrypt the Google Drive access token."""
        return self._decrypt_token(self.drive_access_token)
    
    def decrypt_drive_access_token(self) -> str:
        """Decrypt the Google Drive access token (alias for get_drive_access_token)."""
        return self.get_drive_access_token()
    
    def decrypt_drive_refresh_token(self) -> str:
        """Decrypt the Google Drive refresh token (alias for get_drive_refresh_token)."""
        return self.get_drive_refresh_token()
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = datetime.utcnow()
    
    def is_drive_token_valid(self) -> bool:
        """Check if the Google Drive token is still valid."""
        if not self.drive_token_expiry:
            return False
        return datetime.utcnow() < self.drive_token_expiry
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            'id': str(self.id),
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'picture_url': self.picture_url,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'drive_connected': bool(self.drive_refresh_token),
            'drive_token_valid': self.is_drive_token_valid(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"