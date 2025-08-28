"""
Vector Session Model

Manages user-specific vector database sessions with temporary loading
and Google Drive persistence for the GUARDIAN system.
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
from .base import BaseModel

class VectorSession(BaseModel):
    """
    Vector session model for managing user-specific vector databases.
    
    Each user's vector database is loaded into a temporary session when needed
    and persisted to Google Drive when inactive. This provides isolation
    between users while managing memory efficiently.
    
    Attributes:
        user_id: Foreign key to users table
        session_token: Unique token identifying this session
        google_drive_folder_id: Google Drive folder containing VDB files
        local_temp_path: Local temporary directory for this session
        is_loaded: Whether the VDB is currently loaded in memory
        loaded_at: When the VDB was loaded into memory
        last_accessed: Last time this session was accessed
        expires_at: When this session expires and should be cleaned up
        
    Relationships:
        user: The user this session belongs to
    """
    __tablename__ = 'vector_sessions'
    
    # Foreign key to users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Session identification
    session_token = Column(String(255), nullable=False, index=True)
    
    # Google Drive integration
    google_drive_folder_id = Column(String(255), index=True)
    
    # Local session management
    local_temp_path = Column(Text)
    is_loaded = Column(Boolean, default=False, nullable=False, index=True)
    loaded_at = Column(DateTime)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="vector_sessions")
    
    @classmethod
    def create_session(cls, user_id: str, session_token: str, 
                      duration_hours: int = 2) -> 'VectorSession':
        """
        Create a new vector session for a user.
        
        Args:
            user_id: The user's ID
            session_token: Unique session token
            duration_hours: How long the session should last (default: 2 hours)
            
        Returns:
            VectorSession: New session instance
        """
        expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        return cls(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            local_temp_path=f"/tmp/guardian_sessions/{user_id}/{session_token}"
        )
    
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_active(self) -> bool:
        """Check if the session is active (not expired and loaded)."""
        return not self.is_expired() and self.is_loaded
    
    def extend_session(self, hours: int = 2):
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.update_last_accessed()
    
    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.utcnow()
    
    def mark_loaded(self):
        """Mark the vector database as loaded into memory."""
        self.is_loaded = True
        self.loaded_at = datetime.utcnow()
        self.update_last_accessed()
    
    def mark_unloaded(self):
        """Mark the vector database as unloaded from memory."""
        self.is_loaded = False
        self.loaded_at = None
    
    def set_drive_folder_id(self, folder_id: str):
        """Set the Google Drive folder ID for this session."""
        self.google_drive_folder_id = folder_id
    
    def has_drive_backup(self) -> bool:
        """Check if session data is backed up to Google Drive."""
        return bool(self.google_drive_folder_id)
    
    def get_session_duration(self) -> timedelta:
        """Get how long the session has been active."""
        if not self.loaded_at:
            return timedelta(0)
        return datetime.utcnow() - self.loaded_at
    
    def get_remaining_time(self) -> timedelta:
        """Get the remaining time before session expires."""
        if self.is_expired():
            return timedelta(0)
        return self.expires_at - datetime.utcnow()
    
    def get_idle_time(self) -> timedelta:
        """Get how long the session has been idle."""
        return datetime.utcnow() - self.last_accessed
    
    def should_cleanup(self, idle_threshold_minutes: int = 30) -> bool:
        """
        Check if session should be cleaned up due to inactivity.
        
        Args:
            idle_threshold_minutes: Minutes of inactivity before cleanup
            
        Returns:
            bool: True if session should be cleaned up
        """
        if self.is_expired():
            return True
        
        idle_time = self.get_idle_time()
        return idle_time > timedelta(minutes=idle_threshold_minutes)
    
    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'session_token': self.session_token,
            'google_drive_folder_id': self.google_drive_folder_id,
            'has_drive_backup': self.has_drive_backup(),
            'local_temp_path': self.local_temp_path,
            'is_loaded': self.is_loaded,
            'is_active': self.is_active(),
            'loaded_at': self.loaded_at.isoformat() if self.loaded_at else None,
            'last_accessed': self.last_accessed.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'session_duration_seconds': int(self.get_session_duration().total_seconds()),
            'remaining_time_seconds': int(self.get_remaining_time().total_seconds()),
            'idle_time_seconds': int(self.get_idle_time().total_seconds()),
            'should_cleanup': self.should_cleanup(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_user_active_session(cls, db_session, user_id: str):
        """
        Get the active vector session for a user.
        
        Args:
            db_session: SQLAlchemy database session
            user_id: User ID to find session for
            
        Returns:
            VectorSession or None: Active session if found
        """
        return db_session.query(cls).filter(
            cls.user_id == user_id,
            cls.is_loaded == True,
            cls.expires_at > datetime.utcnow()
        ).first()
    
    @classmethod
    def cleanup_expired_sessions(cls, db_session) -> int:
        """
        Clean up all expired vector sessions.
        
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
    
    @classmethod
    def cleanup_idle_sessions(cls, db_session, idle_threshold_minutes: int = 30) -> int:
        """
        Clean up sessions that have been idle too long.
        
        Args:
            db_session: SQLAlchemy database session
            idle_threshold_minutes: Minutes of inactivity before cleanup
            
        Returns:
            int: Number of sessions cleaned up
        """
        idle_threshold = datetime.utcnow() - timedelta(minutes=idle_threshold_minutes)
        
        idle_sessions = db_session.query(cls).filter(
            cls.last_accessed < idle_threshold,
            cls.is_loaded == True
        )
        
        # Mark as unloaded instead of deleting
        count = 0
        for session in idle_sessions:
            session.mark_unloaded()
            count += 1
        
        db_session.commit()
        return count
    
    @classmethod
    def get_session_stats(cls, db_session, user_id: str = None) -> dict:
        """
        Get statistics about vector sessions.
        
        Args:
            db_session: SQLAlchemy database session
            user_id: Optional user ID to filter by
            
        Returns:
            dict: Session statistics
        """
        query = db_session.query(cls)
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        all_sessions = query.all()
        
        if not all_sessions:
            return {"message": "No sessions found"}
        
        total_sessions = len(all_sessions)
        active_sessions = len([s for s in all_sessions if s.is_active()])
        loaded_sessions = len([s for s in all_sessions if s.is_loaded])
        expired_sessions = len([s for s in all_sessions if s.is_expired()])
        
        avg_duration = (
            sum(s.get_session_duration().total_seconds() for s in all_sessions if s.loaded_at) /
            max(loaded_sessions, 1)
        )
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "loaded_sessions": loaded_sessions,
            "expired_sessions": expired_sessions,
            "avg_session_duration_seconds": avg_duration,
            "sessions_with_drive_backup": len([s for s in all_sessions if s.has_drive_backup()])
        }
    
    def __repr__(self):
        return f"<VectorSession(id={self.id}, user_id={self.user_id}, loaded={self.is_loaded}, expires={self.expires_at})>"