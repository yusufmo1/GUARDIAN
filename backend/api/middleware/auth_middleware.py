"""
Authentication Middleware

Provides decorators and middleware for protecting API routes with authentication
and injecting user context into requests for the GUARDIAN system.
"""

from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import request, jsonify, g
from sqlalchemy.orm import sessionmaker

from ...models import get_db_session
import backend.models.base as models_base
from ...services.auth.auth_service import AuthService, AuthenticationError
from ...utils import logger

class AuthMiddleware:
    """
    Authentication middleware for Flask applications.
    
    Provides decorators for protecting routes and utilities for
    extracting and validating user authentication.
    """
    
    @staticmethod
    def extract_bearer_token() -> Optional[str]:
        """
        Extract bearer token from Authorization header.
        
        Returns:
            str: Token if found, None otherwise
        """
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        parts = auth_header.split(' ')
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None
        
        return parts[1]
    
    @staticmethod
    def get_client_info() -> Dict[str, str]:
        """
        Get client information from request.
        
        Returns:
            Dict containing IP address and user agent
        """
        return {
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }

def require_authentication(f: Callable) -> Callable:
    """
    Decorator to require valid authentication for a route.
    
    Validates the session token and injects user context into g.current_user.
    Returns 401 if authentication fails.
    
    Usage:
        @app.route('/protected')
        @require_authentication
        def protected_route():
            user = g.current_user
            return jsonify({'user_id': user['id']})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Extract token from request
            token = AuthMiddleware.extract_bearer_token()
            if not token:
                logger.debug("No bearer token provided")
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_TOKEN_MISSING',
                    'message': 'Bearer token is required in Authorization header'
                }), 401
            
            # Get database session
            if not models_base.db_config:
                logger.error("Database not initialized")
                return jsonify({
                    'error': 'Internal server error',
                    'error_code': 'DATABASE_ERROR',
                    'message': 'Database connection not available'
                }), 500
            
            db_session = models_base.db_config.get_session()
            
            try:
                # Validate token with auth service
                auth_service = AuthService(db_session)
                auth_data = auth_service.validate_session(token)
                
                if not auth_data:
                    logger.debug("Invalid or expired session token")
                    return jsonify({
                        'error': 'Invalid authentication',
                        'error_code': 'AUTH_TOKEN_INVALID',
                        'message': 'Session token is invalid or expired'
                    }), 401
                
                # Store user and session in Flask's g object
                g.current_user = auth_data['user']
                g.current_session = auth_data['session']
                g.db_session = db_session
                g.auth_service = auth_service
                
                logger.debug(
                    "Authentication successful",
                    user_id=auth_data['user']['id'],
                    user_email=auth_data['user']['email']
                )
                
                # Call the original function
                try:
                    return f(*args, **kwargs)
                finally:
                    # Ensure database session is closed
                    db_session.close()
                    
            except Exception as e:
                db_session.close()
                raise e
                
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {str(e)}")
            return jsonify({
                'error': 'Authentication failed',
                'error_code': 'AUTH_ERROR',
                'message': str(e)
            }), 401
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {str(e)}", exception=e)
            return jsonify({
                'error': 'Internal server error',
                'error_code': 'AUTH_MIDDLEWARE_ERROR',
                'message': 'Authentication system temporarily unavailable'
            }), 500
    
    return decorated_function

def require_drive_access(f: Callable) -> Callable:
    """
    Decorator to require valid Google Drive access for a route.
    
    Ensures the user has valid Google Drive tokens and can access Drive API.
    Must be used together with @require_authentication.
    
    Usage:
        @app.route('/drive-operation')
        @require_authentication
        @require_drive_access
        def drive_operation():
            drive_service = g.drive_service
            return jsonify({'status': 'success'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user context exists (should be set by require_authentication)
            if not hasattr(g, 'current_user') or not hasattr(g, 'auth_service'):
                logger.error("Drive access decorator used without authentication")
                return jsonify({
                    'error': 'Authentication required',
                    'error_code': 'AUTH_REQUIRED',
                    'message': 'This endpoint requires authentication'
                }), 401
            
            # Get Drive service for user
            auth_service = g.auth_service
            drive_service = auth_service.get_drive_service(g.current_user['id'])
            
            if not drive_service:
                logger.warning(f"No Drive access for user {g.current_user['id']}")
                return jsonify({
                    'error': 'Drive access required',
                    'error_code': 'DRIVE_ACCESS_REQUIRED',
                    'message': 'Google Drive access is required for this operation. Please re-authenticate.'
                }), 403
            
            # Store Drive service in g object
            g.drive_service = drive_service
            
            logger.debug(f"Drive access validated for user {g.current_user['id']}")
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Drive access middleware error: {str(e)}", exception=e)
            return jsonify({
                'error': 'Drive access error',
                'error_code': 'DRIVE_ACCESS_ERROR',
                'message': 'Failed to validate Google Drive access'
            }), 500
    
    return decorated_function

def optional_authentication(f: Callable) -> Callable:
    """
    Decorator for routes that work with or without authentication.
    
    If a valid token is provided, user context is injected.
    If no token or invalid token, continues without user context.
    
    Usage:
        @app.route('/public-or-private')
        @optional_authentication  
        def flexible_route():
            if hasattr(g, 'current_user'):
                return jsonify({'user': g.current_user['name']})
            else:
                return jsonify({'message': 'Public access'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Try to extract and validate token
            token = AuthMiddleware.extract_bearer_token()
            
            if token and models_base.db_config:
                db_session = models_base.db_config.get_session()
                
                try:
                    auth_service = AuthService(db_session)
                    auth_data = auth_service.validate_session(token)
                    
                    if auth_data:
                        g.current_user = auth_data['user']
                        g.current_session = auth_data['session']
                        g.db_session = db_session
                        g.auth_service = auth_service
                        
                        logger.debug(f"Optional auth successful for user {auth_data['user']['id']}")
                    else:
                        db_session.close()
                        
                except Exception as e:
                    logger.debug(f"Optional auth failed: {str(e)}")
                    db_session.close()
            
            return f(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Optional authentication error: {str(e)}", exception=e)
            # Continue without authentication on error
            return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user from Flask's g object.
    
    Returns:
        Dict: User data if authenticated, None otherwise
    """
    return getattr(g, 'current_user', None)

def get_current_session() -> Optional[Dict[str, Any]]:
    """
    Get the current session from Flask's g object.
    
    Returns:
        Dict: Session data if authenticated, None otherwise
    """
    return getattr(g, 'current_session', None)

def get_auth_service() -> Optional[AuthService]:
    """
    Get the current auth service from Flask's g object.
    
    Returns:
        AuthService: Auth service if available, None otherwise
    """
    return getattr(g, 'auth_service', None)

def get_drive_service():
    """
    Get the current Drive service from Flask's g object.
    
    Returns:
        GoogleDriveService: Drive service if available, None otherwise
    """
    return getattr(g, 'drive_service', None)