"""
Error Handler Middleware

Provides centralized error handling for the Flask application with structured
JSON responses and proper HTTP status codes.
"""

import logging
import traceback
from typing import Any, Dict, Tuple
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

# Set up logger
logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle 400 Bad Request errors"""
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'error_code': 'BAD_REQUEST',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request data',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'error_code': 'UNAUTHORIZED',
            'message': 'Authentication required or invalid credentials',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'error_code': 'FORBIDDEN',
            'message': 'Access denied - insufficient permissions',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 403

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'error_code': 'NOT_FOUND',
            'message': f'Resource not found: {request.path}',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'error_code': 'METHOD_NOT_ALLOWED',
            'message': f'Method {request.method} not allowed for {request.path}',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 405

    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        return jsonify({
            'success': False,
            'error': 'Unprocessable Entity',
            'error_code': 'VALIDATION_ERROR',
            'message': 'Request data validation failed',
            'details': str(error.description) if hasattr(error, 'description') else None,
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 422

    @app.errorhandler(429)
    def handle_rate_limit(error):
        """Handle 429 Too Many Requests errors"""
        return jsonify({
            'success': False,
            'error': 'Too Many Requests',
            'error_code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Rate limit exceeded - please try again later',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 429

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal server error: {error}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'error_code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 500

    @app.errorhandler(502)
    def handle_bad_gateway(error):
        """Handle 502 Bad Gateway errors"""
        return jsonify({
            'success': False,
            'error': 'Bad Gateway',
            'error_code': 'BAD_GATEWAY',
            'message': 'External service unavailable',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 502

    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle 503 Service Unavailable errors"""
        return jsonify({
            'success': False,
            'error': 'Service Unavailable',
            'error_code': 'SERVICE_UNAVAILABLE',
            'message': 'Service temporarily unavailable',
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 503

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle generic HTTP exceptions"""
        return jsonify({
            'success': False,
            'error': error.name,
            'error_code': error.name.upper().replace(' ', '_'),
            'message': error.description,
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), error.code

    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all other exceptions"""
        logger.error(f"Unhandled exception: {error}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'error_code': 'UNHANDLED_EXCEPTION',
            'message': 'An unexpected error occurred',
            'details': str(error) if app.debug else None,
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }), 500


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Dict[str, Any] = None
) -> Tuple[Dict[str, Any], int]:
    """
    Create a standardized error response.
    
    Args:
        error_code: Unique error code identifier
        message: Human-readable error message
        status_code: HTTP status code
        details: Optional additional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'error_code': error_code,
        'message': message,
        'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
    }
    
    if details:
        response['details'] = details
        
    return response, status_code


class GuardianAPIError(Exception):
    """Custom exception for Guardian API errors"""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'API_ERROR'
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            'success': False,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'timestamp': logger.handlers[0].formatter.formatTime() if logger.handlers else None
        }


class ValidationError(GuardianAPIError):
    """Exception for validation errors"""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code='VALIDATION_ERROR',
            details=details or {}
        )
        if field:
            self.details['field'] = field


class AuthenticationError(GuardianAPIError):
    """Exception for authentication errors"""
    
    def __init__(self, message: str = "Authentication required", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code='AUTHENTICATION_ERROR',
            details=details or {}
        )


class AuthorizationError(GuardianAPIError):
    """Exception for authorization errors"""
    
    def __init__(self, message: str = "Access denied", details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            status_code=403,
            error_code='AUTHORIZATION_ERROR',
            details=details or {}
        )


class ResourceNotFoundError(GuardianAPIError):
    """Exception for resource not found errors"""
    
    def __init__(self, resource: str, identifier: str = None, details: Dict[str, Any] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
            
        super().__init__(
            message=message,
            status_code=404,
            error_code='RESOURCE_NOT_FOUND',
            details=details or {}
        )


class ExternalServiceError(GuardianAPIError):
    """Exception for external service errors"""
    
    def __init__(self, service: str, message: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message or f"{service} service unavailable",
            status_code=502,
            error_code='EXTERNAL_SERVICE_ERROR',
            details=details or {'service': service}
        )