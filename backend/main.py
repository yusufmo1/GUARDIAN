"""
Main Application Entry Point

Bootstraps the Flask application for the GUARDIAN system with all necessary 
configurations, middleware, and route handlers. Uses the application factory 
pattern for better testability and configuration management.

GUARDIAN System:
- Protocol compliance analysis against pharmaceutical standards
- Document chunking and vector similarity search
- LLM-powered compliance feedback generation
- PDF report generation with compliance analysis

Key Features:
- CORS configuration for production and development
- Centralized error handling
- Blueprint-based route organization
- Automatic service initialization with graceful fallback

Usage:
    Development: python main.py
    Production: gunicorn main:app
"""
from flask import Flask
from flask_cors import CORS
import threading
import time
import atexit

from .config.settings import settings
from .utils import logger
from .api.middleware.error_handler import register_error_handlers
from .api.middleware.csrf_middleware import init_csrf_protection
from .api.middleware.rate_limit_middleware import init_rate_limiting

# Import database configuration
from .models import DatabaseConfig, Base
import backend.models.base as models_base

# Import services for background tasks
from .services.session_vector_service import SessionVectorService

# Import all route blueprints
from .api.routes import health_bp
from .api.routes.analysis import analysis_bp
from .api.routes.upload import upload_bp
from .api.routes.search import search_bp
from .api.routes.reports import reports_bp
from .api.routes.auth import auth_bp
from .api.routes.session_analysis import session_analysis_bp
from .api.routes.chat import chat_bp
from .api.docs.swagger import docs_bp

def create_app() -> Flask:
    """
    Application factory function.
    
    Creates and configures the Flask application with all necessary
    components for the GUARDIAN protocol compliance analysis system.
    This pattern allows for easy testing and multiple app instances 
    with different configurations.
    
    Returns:
        Configured Flask application instance
        
    Configuration includes:
        - CORS for cross-origin requests
        - Error handlers for consistent error responses
        - API route blueprints
        - Service initialization (embedding models, vector DB)
    """
    app = Flask(__name__)
    
    # Configure app
    app.config['JSON_AS_ASCII'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    
    # Configure CORS for production and development
    # Allows frontend to communicate with API across domains
    CORS(app, 
         origins=[
             "https://guardian-app.com",  # Production domain (placeholder)
             "https://www.guardian-app.com",  # Production www domain
             "http://localhost:5173",  # Development frontend (Vite)
             "http://localhost:3000",  # Alternative development port (React)
             "http://localhost:3001",  # Docker frontend port
             "http://localhost:8080"   # Alternative development port
         ],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'Accept', 'X-CSRF-Token'],
         expose_headers=['X-CSRF-Token'],
         supports_credentials=True)
    
    # Initialize database
    _initialize_database()
    
    # Register error handlers
    register_error_handlers(app)
    
    # Initialize CSRF protection
    init_csrf_protection(app)
    
    # Initialize rate limiting
    init_rate_limiting(app)
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(auth_bp)  # Authentication routes
    app.register_blueprint(session_analysis_bp)  # Session-based analysis routes
    app.register_blueprint(chat_bp)  # Chat routes
    app.register_blueprint(docs_bp)
    
    # Initialize services
    # This will be expanded as we create the services
    
    # Start background cleanup task
    _start_cleanup_task()
    
    # Register cleanup on app shutdown
    atexit.register(_stop_cleanup_task)
    
    logger.info("GUARDIAN application initialized successfully")
    return app

def _initialize_database():
    """
    Initialize database connection and create tables if needed.
    
    Sets up the global database configuration and creates tables
    for the multi-tenant authentication system.
    """
    try:
        # Initialize database configuration
        models_base.db_config = DatabaseConfig(settings.database.url)
        models_base.db_config.initialize()
        
        # Create tables if they don't exist
        logger.info("Creating database tables if needed...")
        models_base.db_config.create_tables()
        
        logger.info(
            "Database initialized successfully",
            database_url=settings.database.url[:50] + "..." if len(settings.database.url) > 50 else settings.database.url
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exception=e)
        logger.warning(
            "Application will start without database functionality. "
            "Authentication and user management will not be available."
        )
        models_base.db_config = None

# Global variable to control the cleanup thread
cleanup_thread = None
cleanup_stop_event = threading.Event()

def _cleanup_expired_sessions():
    """
    Background task to clean up expired sessions periodically.
    
    Runs every 30 minutes to:
    - Clean up expired authentication sessions
    - Clean up expired vector database sessions
    - Backup VDB data to Drive before cleanup
    """
    logger.info("Starting session cleanup background task")
    
    while not cleanup_stop_event.is_set():
        try:
            # Clean up expired auth sessions
            if models_base.db_config:
                from .services.auth.auth_service import AuthService
                db_session = models_base.db_config.get_session()
                try:
                    auth_service = AuthService(db_session)
                    auth_sessions_cleaned = auth_service.cleanup_expired_sessions()
                    logger.info(f"Cleaned up {auth_sessions_cleaned} expired auth sessions")
                finally:
                    db_session.close()
            
            # Clean up expired vector database sessions
            try:
                vector_service = SessionVectorService()
                vdb_sessions_cleaned = vector_service.cleanup_expired_sessions()
                logger.info(f"Cleaned up {vdb_sessions_cleaned} expired VDB sessions")
            except Exception as e:
                logger.error(f"Failed to cleanup VDB sessions: {str(e)}", exception=e)
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}", exception=e)
        
        # Wait 30 minutes before next cleanup, checking every second for stop signal
        for _ in range(1800):  # 30 minutes = 1800 seconds
            if cleanup_stop_event.is_set():
                break
            time.sleep(1)
    
    logger.info("Session cleanup background task stopped")

def _start_cleanup_task():
    """Start the background cleanup task."""
    global cleanup_thread
    
    if cleanup_thread is None or not cleanup_thread.is_alive():
        cleanup_stop_event.clear()
        cleanup_thread = threading.Thread(target=_cleanup_expired_sessions, daemon=True)
        cleanup_thread.start()
        logger.info("Background cleanup task started")

def _stop_cleanup_task():
    """Stop the background cleanup task."""
    global cleanup_thread
    
    if cleanup_thread and cleanup_thread.is_alive():
        logger.info("Stopping background cleanup task...")
        cleanup_stop_event.set()
        cleanup_thread.join(timeout=5)
        logger.info("Background cleanup task stopped")

# Create application instance
# This is what WSGI servers (like gunicorn) will import
app = create_app()

if __name__ == '__main__':
    # Development server - runs when script is executed directly
    # In production, use Gunicorn via: gunicorn --config gunicorn.conf.py backend.main:app
    
    import os
    
    # Check if we're in production environment
    flask_env = os.getenv('FLASK_ENV', 'development').lower()
    
    if flask_env == 'production':
        logger.warning(
            "Production environment detected. "
            "Consider using Gunicorn: 'gunicorn --config gunicorn.conf.py backend.main:app'"
        )
    
    logger.info(f"Starting GUARDIAN development server in {flask_env} mode")
    app.run(
        host=settings.api.host,
        port=settings.api.port,
        debug=settings.api.debug and flask_env != 'production'
    )