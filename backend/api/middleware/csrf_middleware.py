"""
CSRF Protection Middleware

Implements CSRF protection for the GUARDIAN API using double-submit cookie pattern.
"""

from flask import request, g, make_response, jsonify
from functools import wraps
import logging

from ...utils.security import csrf, SecureTokenGenerator
from ..middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)


def init_csrf_protection(app):
    """Initialize CSRF protection for the Flask app."""
    
    @app.before_request
    def csrf_protect():
        """Check CSRF token for state-changing requests."""
        # Skip CSRF for preflight requests
        if request.method == 'OPTIONS':
            return None
        
        # Skip CSRF for safe methods
        if request.method in csrf.SAFE_METHODS:
            return None
        
        # Skip CSRF for public endpoints
        public_endpoints = [
            'auth.google_initiate',
            'auth.google_callback',
            'health.health_check',
            'health.detailed_health',
            'api.serve_swagger_ui',
            'api.serve_swagger_json',
            'api.serve_redoc'
        ]
        
        if request.endpoint in public_endpoints:
            return None
        
        # Get user context
        user = get_current_user()
        if not user:
            # No CSRF check needed for unauthenticated requests
            return None
        
        # Get CSRF token from session
        session_token = g.get('csrf_token')
        
        # Get CSRF token from request
        request_token = request.headers.get(csrf.HEADER_NAME)
        if not request_token and request.is_json:
            # Try to get from JSON body
            request_token = request.get_json(silent=True, cache=True).get('csrf_token') if request.get_json(silent=True, cache=True) else None
        elif not request_token:
            # Try to get from form data
            request_token = request.form.get(csrf.TOKEN_NAME)
        
        # Verify token
        if not session_token or not request_token:
            logger.warning(f"CSRF token missing for user {user['id']}")
            return jsonify({
                'error': 'CSRF validation failed',
                'message': 'Missing CSRF token. Please refresh and try again.'
            }), 403
        
        if not csrf.verify_token(session_token, request_token):
            logger.warning(f"CSRF token validation failed for user {user['id']}")
            return jsonify({
                'error': 'CSRF validation failed',
                'message': 'Invalid CSRF token. Please refresh and try again.'
            }), 403
    
    @app.after_request
    def set_csrf_token(response):
        """Set CSRF token in response if needed."""
        # Only set for authenticated users
        user = get_current_user()
        if not user:
            return response
        
        # Check if we need to generate a new token
        if not g.get('csrf_token'):
            g.csrf_token = csrf.generate_token()
        
        # Add CSRF token to response headers for client
        response.headers['X-CSRF-Token'] = g.csrf_token
        
        return response


def csrf_exempt(f):
    """Decorator to exempt specific routes from CSRF protection."""
    f._csrf_exempt = True
    return f


def require_csrf(f):
    """Decorator to explicitly require CSRF protection."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user context
        user = get_current_user()
        if not user:
            return jsonify({
                'error': 'Authentication required',
                'message': 'Please log in to access this resource.'
            }), 401
        
        # Get CSRF token from session
        session_token = g.get('csrf_token')
        
        # Get CSRF token from request
        request_token = request.headers.get(csrf.HEADER_NAME)
        if not request_token and request.is_json:
            request_token = request.get_json(silent=True).get('csrf_token', None)
        elif not request_token:
            request_token = request.form.get(csrf.TOKEN_NAME)
        
        # Verify token
        if not session_token or not request_token:
            return jsonify({
                'error': 'CSRF validation failed',
                'message': 'Missing CSRF token.'
            }), 403
        
        if not csrf.verify_token(session_token, request_token):
            return jsonify({
                'error': 'CSRF validation failed',
                'message': 'Invalid CSRF token.'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function