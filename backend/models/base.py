"""
Database Base Configuration

Provides base configuration for SQLAlchemy models with common fields
and database connection setup for the GUARDIAN system.
"""

import uuid
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Column, String, DateTime, UUID, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

# Create base class for models
Base = declarative_base()

class BaseModel(Base):
    """
    Base model class with common fields for all tables.
    
    Provides:
    - UUID primary key
    - Created/updated timestamps
    - Common utility methods
    """
    __abstract__ = True
    
    id = Column(
        PostgresUUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"

class DatabaseConfig:
    """Database configuration and connection management."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """Initialize database connection and session factory."""
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
        
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()

# Global database instance (to be initialized in main app)
db_config = None

def get_db_session():
    """
    Dependency function to get database session.
    Used in API endpoints and services.
    """
    if not db_config:
        raise RuntimeError("Database not initialized. Call db_config.initialize() first.")
    
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()