"""
Authentication API Routes

Provides endpoints for Google OAuth authentication, session management,
and user authentication for the GUARDIAN system.
"""

from flask import Blueprint, request, jsonify, redirect, g
from pydantic import BaseModel, ValidationError
from typing import Optional
from datetime import datetime

from ...models import get_db_session
import backend.models.base as models_base
from ...services.auth.auth_service import AuthService, AuthenticationError
from ...api.middleware.auth_middleware import (
    require_authentication, 
    optional_authentication,
    AuthMiddleware
)
from ...api.middleware.rate_limit_middleware import auth_rate_limit
from ...utils import logger

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Pydantic models for request validation
class OAuthCallbackRequest(BaseModel):
    code: str
    state: str

class LogoutRequest(BaseModel):
    session_token: Optional[str] = None

@auth_bp.route('/google/initiate', methods=['GET'])
def initiate_google_oauth():
    """
    Initiate Google OAuth flow.
    
    Returns authorization URL and state token for CSRF protection.
    
    Returns:
        JSON response with authorization URL and state
    """
    try:
        # Get database session
        if not models_base.db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = models_base.db_config.get_session()
        
        try:
            auth_service = AuthService(db_session)
            oauth_data = auth_service.initiate_oauth_flow()
            
            logger.info("OAuth flow initiated")
            
            return jsonify({
                'success': True,
                'data': oauth_data,
                'message': 'OAuth flow initiated successfully'
            })
            
        finally:
            db_session.close()
            
    except AuthenticationError as e:
        logger.error(f"OAuth initiation failed: {str(e)}")
        return jsonify({
            'error': 'OAuth initiation failed',
            'error_code': 'OAUTH_INIT_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in OAuth initiation: {str(e)}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'message': 'Failed to initiate OAuth flow'
        }), 500

@auth_bp.route('/google/callback', methods=['POST'])
# @auth_rate_limit  # Temporarily disabled for development
def handle_google_oauth_callback():
    """
    Handle Google OAuth callback.
    
    Exchanges authorization code for tokens and creates user session.
    
    Request body:
        {
            "code": "authorization_code_from_google",
            "state": "state_token_from_initiate"
        }
    
    Returns:
        JSON response with session token and user information
    """
    try:
        # Validate request data
        try:
            request_data = OAuthCallbackRequest(**request.get_json())
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': e.errors()
            }), 400
        
        # Get client info
        client_info = AuthMiddleware.get_client_info()
        
        # Get database session
        if not models_base.db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = models_base.db_config.get_session()
        
        try:
            auth_service = AuthService(db_session)
            
            # Handle OAuth callback
            auth_result = auth_service.handle_oauth_callback(
                code=request_data.code,
                state=request_data.state,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            logger.info(
                "OAuth callback handled successfully",
                user_email=auth_result['user']['email']
            )
            
            return jsonify({
                'success': True,
                'data': auth_result,
                'message': 'Authentication successful'
            })
            
        finally:
            db_session.close()
            
    except AuthenticationError as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        return jsonify({
            'error': 'Authentication failed',
            'error_code': 'AUTH_CALLBACK_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {str(e)}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'message': 'Authentication process failed'
        }), 500

@auth_bp.route('/google/callback', methods=['GET'])
def handle_google_oauth_callback_redirect():
    """
    Handle OAuth callback as a redirect (alternative to POST).
    
    This endpoint handles the direct redirect from Google OAuth.
    Typically used for web applications that receive the callback as a redirect.
    """
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')
        
        if error:
            logger.warning(f"OAuth callback received error: {error}")
            return redirect(f"/auth/error?error={error}")
        
        if not code or not state:
            logger.warning("OAuth callback missing code or state")
            return redirect("/auth/error?error=missing_parameters")
        
        # Get client info
        client_info = AuthMiddleware.get_client_info()
        
        # Get database session
        if not models_base.db_config:
            return redirect("/auth/error?error=database_error")
        
        db_session = models_base.db_config.get_session()
        
        try:
            auth_service = AuthService(db_session)
            
            # Handle OAuth callback
            auth_result = auth_service.handle_oauth_callback(
                code=code,
                state=state,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent']
            )
            
            # Redirect to frontend with session token
            session_token = auth_result['session_token']
            frontend_url = f"/auth/success?token={session_token}"
            
            logger.info(
                "OAuth redirect callback handled successfully",
                user_email=auth_result['user']['email']
            )
            
            return redirect(frontend_url)
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"OAuth redirect callback failed: {str(e)}", exception=e)
        return redirect("/auth/error?error=callback_failed")

@auth_bp.route('/validate', methods=['GET'])
@require_authentication
def validate_session():
    """
    Validate current session and return user information.
    
    Requires valid Bearer token in Authorization header.
    
    Returns:
        JSON response with current user and session information
    """
    try:
        # User context is injected by @require_authentication
        user = g.current_user
        session = g.current_session
        
        logger.debug(f"Session validated for user {user['id']}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'session': session,
                'authenticated': True
            },
            'message': 'Session is valid'
        })
        
    except Exception as e:
        logger.error(f"Session validation error: {str(e)}", exception=e)
        return jsonify({
            'error': 'Session validation failed',
            'error_code': 'VALIDATION_ERROR',
            'message': 'Failed to validate session'
        }), 500

@auth_bp.route('/user', methods=['GET'])
@require_authentication
def get_current_user():
    """
    Get current authenticated user information.
    
    Requires valid Bearer token in Authorization header.
    
    Returns:
        JSON response with user information
    """
    try:
        user = g.current_user
        
        # Get additional user stats if needed
        auth_service = g.auth_service
        sessions = auth_service.get_user_sessions(user['id'])
        
        user_data = {
            **user,
            'active_sessions': len(sessions),
            'sessions': sessions
        }
        
        return jsonify({
            'success': True,
            'data': user_data,
            'message': 'User information retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Get user error: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to get user information',
            'error_code': 'GET_USER_ERROR',
            'message': 'Could not retrieve user information'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@optional_authentication
def logout():
    """
    Logout user by invalidating their session.
    
    Can accept session token in request body or Authorization header.
    
    Request body (optional):
        {
            "session_token": "token_to_logout"
        }
    
    Returns:
        JSON response confirming logout
    """
    try:
        # Try to get token from request body or header
        session_token = None
        
        if request.is_json:
            try:
                request_data = LogoutRequest(**request.get_json())
                session_token = request_data.session_token
            except ValidationError:
                pass
        
        # If no token in body, try header
        if not session_token:
            session_token = AuthMiddleware.extract_bearer_token()
        
        if not session_token:
            return jsonify({
                'error': 'No session token provided',
                'error_code': 'TOKEN_MISSING',
                'message': 'Session token required for logout'
            }), 400
        
        # Get database session
        if not models_base.db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = models_base.db_config.get_session()
        
        try:
            auth_service = AuthService(db_session)
            success = auth_service.logout_user(session_token)
            
            if success:
                logger.info("User logged out successfully")
                return jsonify({
                    'success': True,
                    'message': 'Logged out successfully'
                })
            else:
                return jsonify({
                    'error': 'Logout failed',
                    'error_code': 'LOGOUT_FAILED',
                    'message': 'Session not found or already expired'
                }), 400
                
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exception=e)
        return jsonify({
            'error': 'Logout failed',
            'error_code': 'LOGOUT_ERROR',
            'message': 'Failed to logout user'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@require_authentication
def refresh_tokens():
    """
    Refresh Google Drive access tokens for the current user.
    
    Requires valid Bearer token in Authorization header.
    
    Returns:
        JSON response confirming token refresh
    """
    try:
        user = g.current_user
        auth_service = g.auth_service
        
        success = auth_service.refresh_drive_token(user['id'])
        
        if success:
            logger.info(f"Drive tokens refreshed for user {user['id']}")
            return jsonify({
                'success': True,
                'message': 'Drive tokens refreshed successfully'
            })
        else:
            return jsonify({
                'error': 'Token refresh failed',
                'error_code': 'REFRESH_FAILED',
                'message': 'Could not refresh Drive tokens. Re-authentication may be required.'
            }), 400
            
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exception=e)
        return jsonify({
            'error': 'Token refresh failed',
            'error_code': 'REFRESH_ERROR',
            'message': 'Failed to refresh tokens'
        }), 500

@auth_bp.route('/sessions', methods=['GET'])
@require_authentication
def get_user_sessions():
    """
    Get all active sessions for the current user.
    
    Requires valid Bearer token in Authorization header.
    
    Returns:
        JSON response with list of active sessions
    """
    try:
        user = g.current_user
        auth_service = g.auth_service
        
        sessions = auth_service.get_user_sessions(user['id'])
        
        return jsonify({
            'success': True,
            'data': {
                'sessions': sessions,
                'total_sessions': len(sessions)
            },
            'message': 'Sessions retrieved successfully'
        })
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to get sessions',
            'error_code': 'GET_SESSIONS_ERROR',
            'message': 'Could not retrieve user sessions'
        }), 500

# Health check endpoint for auth system
@auth_bp.route('/health', methods=['GET'])
def auth_health():
    """
    Health check for authentication system.
    
    Returns:
        JSON response with auth system status
    """
    try:
        # Check database connection
        db_available = bool(models_base.db_config)
        
        # Try to create auth service
        auth_service_available = False
        if db_available:
            try:
                db_session = models_base.db_config.get_session()
                auth_service = AuthService(db_session)
                auth_service_available = True
                db_session.close()
            except Exception:
                pass
        
        status = 'healthy' if db_available and auth_service_available else 'unhealthy'
        
        return jsonify({
            'success': True,
            'status': status,
            'components': {
                'database': 'available' if db_available else 'unavailable',
                'auth_service': 'available' if auth_service_available else 'unavailable',
                'oauth_configured': bool(models_base.db_config and models_base.db_config.SessionLocal)
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Auth health check error: {str(e)}", exception=e)
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500