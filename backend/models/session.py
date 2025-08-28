"""
User Session Model

Manages user authentication sessions with secure token handling and
automatic expiration for the GUARDIAN system.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, INET
from datetime import datetime, timedelta
import secrets
import hashlib
from .base import BaseModel
from ..utils.security import SecureTokenGenerator

class UserSession(BaseModel):
    """
    User session model for managing authentication sessions.
    
    Stores session tokens (hashed), expiration times, and session metadata
    for secure user authentication in the GUARDIAN system.
    
    Attributes:
        user_id: Foreign key to users table
        session_token_hash: SHA-256 hash of the session token
        expires_at: When the session expires
        last_accessed: Last time session was used
        ip_address: IP address where session was created
        user_agent: Browser/client user agent string
        
    Relationships:
        user: The user this session belongs to
    """
    __tablename__ = 'user_sessions'
    
    # Foreign key to users
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('users.id', ondelete='CASCADE'), 
        nullable=False,
        index=True
    )
    
    # Session data
    session_token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Session metadata
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a cryptographically secure session token using enhanced security.
        
        Returns:
            str: A cryptographically secure URL-safe token
        """
        # Use the enhanced secure token generator
        return SecureTokenGenerator.generate_session_token(length=32)
    
    @staticmethod
    def hash_session_token(token: str) -> str:
        """
        Hash a session token for secure storage using enhanced security.
        
        Args:
            token: The raw session token
            
        Returns:
            str: SHA-256 hash of the token with salt
        """
        # Use enhanced hashing with environment-based salt
        import os
        salt = os.getenv('SESSION_SALT', 'guardian_session_salt')
        return SecureTokenGenerator.hash_token(token, salt)
    
    @classmethod
    def create_session(cls, user_id: str, duration_hours: int = 24, 
                      ip_address: str = None, user_agent: str = None) -> tuple:
        """
        Create a new session for a user.
        
        Args:
            user_id: The user's ID
            duration_hours: How long the session should last
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            tuple: (session_instance, raw_token)
        """
        # Generate session token
        raw_token = cls.generate_session_token()
        token_hash = cls.hash_session_token(raw_token)
        
        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        # Create session instance
        session = cls(
            user_id=user_id,
            session_token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return session, raw_token
    
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the session is valid (not expired)."""
        return not self.is_expired()
    
    def extend_session(self, hours: int = 24):
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.last_accessed = datetime.utcnow()
    
    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
    
    def verify_token(self, raw_token: str) -> bool:
        """
        Verify a raw token against this session.
        
        Args:
            raw_token: The raw session token to verify
            
        Returns:
            bool: True if token matches and session is valid
        """
        if self.is_expired():
            return False
            
        token_hash = self.hash_session_token(raw_token)
        return token_hash == self.session_token_hash
    
    def get_remaining_time(self) -> timedelta:
        """Get the remaining time before session expires."""
        if self.is_expired():
            return timedelta(0)
        return self.expires_at - datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'expires_at': self.expires_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'user_agent': self.user_agent,
            'is_valid': self.is_valid(),
            'remaining_time_seconds': int(self.get_remaining_time().total_seconds()),
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def cleanup_expired_sessions(cls, db_session):
        """
        Remove all expired sessions from the database.
        
        Args:
            db_session: SQLAlchemy database session
            
        Returns:
            int: Number of sessions cleaned up
        """
        expired_sessions = db_session.query(cls).filter(
            cls.expires_at < datetime.utcnow()
        )
        count = expired_sessions.count()
        expired_sessions.delete()
        db_session.commit()
        return count
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"