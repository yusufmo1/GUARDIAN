"""
Security Utilities

Enhanced security utilities for the GUARDIAN system including:
- Advanced encryption with key derivation
- CSRF protection
- Input validation and sanitization
- Rate limiting utilities
"""

import os
import base64
import hashlib
import secrets
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g, abort, jsonify
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import html
import bleach
from collections import defaultdict
import time

from ..config.settings import settings
from . import logger


class EnhancedEncryption:
    """Enhanced encryption with key derivation and rotation support."""
    
    def __init__(self, master_key: Optional[str] = None):
        """Initialize with master key or from environment."""
        self.master_key = master_key or os.getenv('SECRET_KEY')
        if not self.master_key:
            raise ValueError("SECRET_KEY environment variable not set")
        
        # Use PBKDF2 for key derivation
        self.salt = os.getenv('ENCRYPTION_SALT', 'guardian_default_salt').encode()
        self.key = self._derive_key(self.master_key, self.salt)
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt string data."""
        if not data:
            return None
        return self.fernet.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data to string."""
        if not encrypted_data:
            return None
        return self.fernet.decrypt(encrypted_data).decode()
    
    def encrypt_dict(self, data: Dict[str, Any]) -> bytes:
        """Encrypt dictionary data as JSON."""
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt JSON data to dictionary."""
        import json
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)


class CSRFProtection:
    """CSRF protection using double-submit cookie pattern."""
    
    TOKEN_LENGTH = 32
    TOKEN_NAME = 'csrf_token'
    HEADER_NAME = 'X-CSRF-Token'
    SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']
    
    @staticmethod
    def generate_token() -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(CSRFProtection.TOKEN_LENGTH)
    
    @staticmethod
    def verify_token(session_token: str, request_token: str) -> bool:
        """Verify CSRF token using constant-time comparison."""
        if not session_token or not request_token:
            return False
        return secrets.compare_digest(session_token, request_token)
    
    @staticmethod
    def protect(f):
        """Decorator to protect routes with CSRF validation."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip CSRF check for safe methods
            if request.method in CSRFProtection.SAFE_METHODS:
                return f(*args, **kwargs)
            
            # Get CSRF token from session
            session_token = g.get('csrf_token')
            if not session_token:
                logger.warning("CSRF token missing from session")
                abort(403, "CSRF validation failed")
            
            # Get CSRF token from request (header or form)
            request_token = request.headers.get(CSRFProtection.HEADER_NAME)
            if not request_token:
                request_token = request.form.get(CSRFProtection.TOKEN_NAME)
            
            # Verify token
            if not CSRFProtection.verify_token(session_token, request_token):
                logger.warning("CSRF token validation failed")
                abort(403, "CSRF validation failed")
            
            return f(*args, **kwargs)
        return decorated_function


class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Common regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\. ]+$')
    
    # Allowed tags for HTML sanitization
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'blockquote', 'code', 'pre']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > 254:  # RFC 5321
            return False
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """Validate UUID format."""
        if not uuid_str:
            return False
        return bool(InputValidator.UUID_PATTERN.match(str(uuid_str)))
    
    @staticmethod
    def validate_filename(filename: str) -> bool:
        """Validate filename for safety."""
        if not filename or len(filename) > 255:
            return False
        # Check for directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        return bool(InputValidator.FILENAME_PATTERN.match(filename))
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input by escaping HTML."""
        if not text:
            return ''
        # Truncate to max length
        text = text[:max_length]
        # Escape HTML
        return html.escape(text)
    
    @staticmethod
    def sanitize_html(html_content: str, max_length: int = 10000) -> str:
        """Sanitize HTML content using bleach."""
        if not html_content:
            return ''
        # Truncate to max length
        html_content = html_content[:max_length]
        # Clean HTML
        return bleach.clean(
            html_content,
            tags=InputValidator.ALLOWED_TAGS,
            attributes=InputValidator.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate JSON data against schema."""
        try:
            import jsonschema
            jsonschema.validate(instance=data, schema=schema)
            return True, []
        except jsonschema.exceptions.ValidationError as e:
            return False, [str(e)]
        except Exception as e:
            return False, [f"Schema validation error: {str(e)}"]


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self):
        # In-memory storage (use Redis in production)
        self.buckets = defaultdict(lambda: {'tokens': 0, 'last_update': time.time()})
        self.limits = {
            'default': {'rate': 3000, 'per': 60},  # 3000 requests per minute (50 per second)
            'auth': {'rate': 200, 'per': 60},      # 200 auth attempts per minute
            'upload': {'rate': 500, 'per': 60},    # 500 uploads per minute
            'analysis': {'rate': 1000, 'per': 60}, # 1000 analyses per minute
        }
    
    def _get_bucket_key(self, identifier: str, endpoint: str) -> str:
        """Generate bucket key for rate limiting."""
        return f"{identifier}:{endpoint}"
    
    def _update_bucket(self, key: str, limit_type: str = 'default') -> tuple[int, bool]:
        """Update token bucket and check if request is allowed."""
        limit = self.limits.get(limit_type, self.limits['default'])
        rate = limit['rate']
        per = limit['per']
        
        bucket = self.buckets[key]
        now = time.time()
        
        # Calculate tokens to add based on time passed
        time_passed = now - bucket['last_update']
        tokens_to_add = time_passed * (rate / per)
        
        # Update bucket
        bucket['tokens'] = min(rate, bucket['tokens'] + tokens_to_add)
        bucket['last_update'] = now
        
        # Check if request is allowed
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return int(bucket['tokens']), True
        
        return int(bucket['tokens']), False
    
    def limit(self, limit_type: str = 'default'):
        """Decorator for rate limiting routes."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Get identifier (user ID or IP address)
                identifier = g.get('user_id', request.remote_addr)
                endpoint = request.endpoint or 'unknown'
                
                # Check rate limit
                key = self._get_bucket_key(identifier, endpoint)
                remaining, allowed = self._update_bucket(key, limit_type)
                
                # Add rate limit headers
                response = None
                if allowed:
                    response = f(*args, **kwargs)
                else:
                    logger.warning(f"Rate limit exceeded for {identifier} on {endpoint}")
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests. Please wait before trying again.'
                    }), 429
                
                # Add rate limit headers
                if hasattr(response, 'headers'):
                    limit = self.limits.get(limit_type, self.limits['default'])
                    response.headers['X-RateLimit-Limit'] = str(limit['rate'])
                    response.headers['X-RateLimit-Remaining'] = str(remaining)
                    response.headers['X-RateLimit-Reset'] = str(int(time.time() + limit['per']))
                
                return response
            return decorated_function
        return decorator


class SecureTokenGenerator:
    """Enhanced secure token generation utilities."""
    
    @staticmethod
    def generate_session_token(length: int = 32) -> str:
        """Generate cryptographically secure session token."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key with prefix."""
        prefix = "grd"  # GUARDIAN prefix
        key = secrets.token_urlsafe(32)
        return f"{prefix}_{key}"
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate numeric verification code."""
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    
    @staticmethod
    def hash_token(token: str, salt: Optional[str] = None) -> str:
        """Hash token with optional salt using SHA-256."""
        if salt:
            token = f"{salt}{token}"
        return hashlib.sha256(token.encode()).hexdigest()
    
    @staticmethod
    def time_based_token(user_id: str, expires_in: int = 3600) -> tuple[str, datetime]:
        """Generate time-based token with expiration."""
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Create token data
        token_data = f"{user_id}:{expires_at.isoformat()}:{secrets.token_hex(16)}"
        
        # Encrypt token data
        encryption = EnhancedEncryption()
        encrypted_token = encryption.encrypt(token_data)
        
        # Encode for URL safety
        token = base64.urlsafe_b64encode(encrypted_token).decode()
        
        return token, expires_at
    
    @staticmethod
    def verify_time_based_token(token: str) -> Optional[str]:
        """Verify and decode time-based token."""
        try:
            # Decode from URL-safe base64
            encrypted_token = base64.urlsafe_b64decode(token.encode())
            
            # Decrypt token
            encryption = EnhancedEncryption()
            token_data = encryption.decrypt(encrypted_token)
            
            # Parse token data
            parts = token_data.split(':')
            if len(parts) != 3:
                return None
            
            user_id, expires_at_str, _ = parts
            expires_at = datetime.fromisoformat(expires_at_str)
            
            # Check expiration
            if datetime.utcnow() > expires_at:
                return None
            
            return user_id
            
        except Exception as e:
            logger.error(f"Failed to verify time-based token: {str(e)}")
            return None


# Global instances
encryption = EnhancedEncryption()
rate_limiter = RateLimiter()
csrf = CSRFProtection()
validator = InputValidator()
token_generator = SecureTokenGenerator()