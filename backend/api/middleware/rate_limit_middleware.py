"""
Rate Limiting Middleware

Implements rate limiting for the GUARDIAN API to prevent abuse and ensure fair usage.
"""

from flask import request, g, jsonify
from functools import wraps
import time
import logging

from ...utils.security import rate_limiter
from ..middleware.auth_middleware import get_current_user

logger = logging.getLogger(__name__)


def init_rate_limiting(app):
    """Initialize rate limiting for the Flask app."""
    
    @app.before_request
    def check_rate_limit():
        """Check rate limit for incoming requests."""
        # Skip rate limiting in development mode
        if app.config.get('ENV') == 'development' or app.config.get('DEBUG'):
            return None
            
        # Skip rate limiting for health checks and documentation
        exempt_endpoints = [
            'health.basic_health_check',
            'health.detailed_health_check',
            'health.ready_check',
            'api.serve_swagger_ui',
            'api.serve_swagger_json',
            'api.serve_redoc'
        ]
        
        if request.endpoint in exempt_endpoints:
            return None
        
        # Determine the appropriate rate limit type based on endpoint
        limit_type = 'default'
        
        if request.endpoint and 'auth' in request.endpoint:
            limit_type = 'auth'
        elif request.endpoint and 'upload' in request.endpoint:
            limit_type = 'upload'
        elif request.endpoint and ('analyze' in request.endpoint or 'analysis' in request.endpoint):
            limit_type = 'analysis'
        
        # Get identifier (user ID if authenticated, IP address otherwise)
        user = get_current_user()
        identifier = user['id'] if user else request.remote_addr
        
        # Check rate limit
        key = rate_limiter._get_bucket_key(identifier, request.endpoint or 'unknown')
        remaining, allowed = rate_limiter._update_bucket(key, limit_type)
        
        # Store rate limit info in g for response headers
        g.rate_limit_info = {
            'limit_type': limit_type,
            'remaining': remaining,
            'allowed': allowed
        }
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {identifier} on {request.endpoint}",
                extra={
                    'identifier': identifier,
                    'endpoint': request.endpoint,
                    'limit_type': limit_type
                }
            )
            
            # Calculate retry after
            limit = rate_limiter.limits.get(limit_type, rate_limiter.limits['default'])
            retry_after = limit['per']
            
            response = jsonify({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Please wait {retry_after} seconds before trying again.',
                'retry_after': retry_after
            })
            response.status_code = 429
            
            # Add rate limit headers
            response.headers['X-RateLimit-Limit'] = str(limit['rate'])
            response.headers['X-RateLimit-Remaining'] = '0'
            response.headers['X-RateLimit-Reset'] = str(int(time.time() + retry_after))
            response.headers['Retry-After'] = str(retry_after)
            
            return response
    
    @app.after_request
    def add_rate_limit_headers(response):
        """Add rate limit headers to response."""
        if hasattr(g, 'rate_limit_info'):
            info = g.rate_limit_info
            limit_type = info['limit_type']
            remaining = info['remaining']
            
            limit = rate_limiter.limits.get(limit_type, rate_limiter.limits['default'])
            
            response.headers['X-RateLimit-Limit'] = str(limit['rate'])
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit['per']))
        
        return response


# Decorator for custom rate limits on specific endpoints
def rate_limit(limit_type: str = 'default'):
    """
    Decorator to apply rate limiting to specific routes.
    
    Args:
        limit_type: Type of rate limit to apply ('default', 'auth', 'upload', 'analysis')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier
            user = get_current_user()
            identifier = user['id'] if user else request.remote_addr
            
            # Check rate limit
            key = rate_limiter._get_bucket_key(identifier, request.endpoint or f.__name__)
            remaining, allowed = rate_limiter._update_bucket(key, limit_type)
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {f.__name__}",
                    extra={
                        'identifier': identifier,
                        'function': f.__name__,
                        'limit_type': limit_type
                    }
                )
                
                limit = rate_limiter.limits.get(limit_type, rate_limiter.limits['default'])
                retry_after = limit['per']
                
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please wait {retry_after} seconds before trying again.',
                    'retry_after': retry_after
                }), 429
            
            # Store rate limit info for headers
            g.rate_limit_info = {
                'limit_type': limit_type,
                'remaining': remaining,
                'allowed': allowed
            }
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Convenience decorators for common rate limit types
auth_rate_limit = rate_limit('auth')
upload_rate_limit = rate_limit('upload')
analysis_rate_limit = rate_limit('analysis')