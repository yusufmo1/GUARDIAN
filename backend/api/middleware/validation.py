"""
Validation Middleware

Provides request validation utilities for JSON payloads, file uploads,
and query parameters with proper error handling.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from functools import wraps
from flask import request, jsonify
from werkzeug.datastructures import FileStorage

from .error_handler import ValidationError, create_error_response
from ...utils.security import InputValidator

# Set up logger
logger = logging.getLogger(__name__)

# File upload constraints
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    'pdf', 'txt', 'doc', 'docx', 'rtf',
    'json', 'csv', 'xlsx', 'xls'
}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'text/plain',
    'text/csv',
    'application/json',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/rtf',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}


def validate_json(required_fields: List[str] = None, optional_fields: List[str] = None):
    """
    Decorator to validate JSON request payloads.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Raises:
        ValidationError: If validation fails
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON content
            if not request.is_json:
                raise ValidationError(
                    message="Request must contain JSON data",
                    details={'content_type': request.content_type}
                )
            
            try:
                data = request.get_json()
            except Exception as e:
                raise ValidationError(
                    message="Invalid JSON format",
                    details={'error': str(e)}
                )
            
            if data is None:
                raise ValidationError(
                    message="Request body cannot be empty",
                    details={'content_length': request.content_length}
                )
            
            # Validate required fields
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    raise ValidationError(
                        message=f"Missing required fields: {', '.join(missing_fields)}",
                        details={
                            'missing_fields': missing_fields,
                            'provided_fields': list(data.keys())
                        }
                    )
            
            # Validate field types and constraints
            validated_data = {}
            all_fields = (required_fields or []) + (optional_fields or [])
            
            for field in all_fields:
                if field in data:
                    # Sanitize the field value
                    validated_data[field] = sanitize_input(data[field])
            
            # Add validated data to request context
            request.validated_json = validated_data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_file_upload(
    required: bool = True,
    max_size: int = MAX_FILE_SIZE,
    allowed_extensions: set = None,
    allowed_mime_types: set = None
):
    """
    Decorator to validate file uploads.
    
    Args:
        required: Whether file upload is required
        max_size: Maximum file size in bytes
        allowed_extensions: Set of allowed file extensions
        allowed_mime_types: Set of allowed MIME types
        
    Raises:
        ValidationError: If validation fails
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_EXTENSIONS
    if allowed_mime_types is None:
        allowed_mime_types = ALLOWED_MIME_TYPES
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if files are present in request
            if 'file' not in request.files:
                if required:
                    raise ValidationError(
                        message="No file provided in request",
                        field='file'
                    )
                else:
                    return f(*args, **kwargs)
            
            file: FileStorage = request.files['file']
            
            # Check if file was actually selected
            if file.filename == '':
                if required:
                    raise ValidationError(
                        message="No file selected",
                        field='file'
                    )
                else:
                    return f(*args, **kwargs)
            
            # Validate file size
            if file.content_length and file.content_length > max_size:
                raise ValidationError(
                    message=f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB",
                    field='file',
                    details={
                        'file_size': file.content_length,
                        'max_size': max_size
                    }
                )
            
            # Validate filename for security
            if file.filename:
                # Validate filename security
                if not InputValidator.validate_filename(file.filename):
                    raise ValidationError(
                        message="Invalid filename. Please use only alphanumeric characters, hyphens, underscores, dots and spaces.",
                        field='file',
                        details={
                            'filename': file.filename
                        }
                    )
                
                # Validate file extension
                file_extension = file.filename.rsplit('.', 1)[-1].lower()
                if file_extension not in allowed_extensions:
                    raise ValidationError(
                        message=f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}",
                        field='file',
                        details={
                            'file_extension': file_extension,
                            'allowed_extensions': list(allowed_extensions)
                        }
                    )
            
            # Validate MIME type
            if file.mimetype and file.mimetype not in allowed_mime_types:
                raise ValidationError(
                    message=f"MIME type not allowed: {file.mimetype}",
                    field='file',
                    details={
                        'mime_type': file.mimetype,
                        'allowed_mime_types': list(allowed_mime_types)
                    }
                )
            
            # Add validated file to request context
            request.validated_file = file
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_query_params(
    required_params: List[str] = None,
    optional_params: List[str] = None,
    param_types: Dict[str, type] = None
):
    """
    Decorator to validate query parameters.
    
    Args:
        required_params: List of required parameter names
        optional_params: List of optional parameter names
        param_types: Dictionary mapping parameter names to expected types
        
    Raises:
        ValidationError: If validation fails
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            validated_params = {}
            
            # Validate required parameters
            if required_params:
                missing_params = []
                for param in required_params:
                    if param not in request.args:
                        missing_params.append(param)
                
                if missing_params:
                    raise ValidationError(
                        message=f"Missing required query parameters: {', '.join(missing_params)}",
                        details={
                            'missing_params': missing_params,
                            'provided_params': list(request.args.keys())
                        }
                    )
            
            # Process and validate parameter types
            all_params = (required_params or []) + (optional_params or [])
            param_types = param_types or {}
            
            for param in all_params:
                if param in request.args:
                    value = request.args.get(param)
                    
                    # Apply type conversion if specified
                    if param in param_types:
                        try:
                            expected_type = param_types[param]
                            if expected_type == bool:
                                value = value.lower() in ('true', '1', 'yes', 'on')
                            elif expected_type == int:
                                value = int(value)
                            elif expected_type == float:
                                value = float(value)
                            elif expected_type == list:
                                value = value.split(',')
                            # str type doesn't need conversion
                            
                        except (ValueError, TypeError) as e:
                            raise ValidationError(
                                message=f"Invalid type for parameter '{param}': expected {expected_type.__name__}",
                                field=param,
                                details={
                                    'provided_value': request.args.get(param),
                                    'expected_type': expected_type.__name__,
                                    'error': str(e)
                                }
                            )
                    
                    validated_params[param] = value
            
            # Add validated parameters to request context
            request.validated_params = validated_params
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def validate_pagination_params():
    """
    Decorator to validate common pagination parameters (page, per_page, limit, offset).
    """
    return validate_query_params(
        optional_params=['page', 'per_page', 'limit', 'offset'],
        param_types={
            'page': int,
            'per_page': int,
            'limit': int,
            'offset': int
        }
    )


def validate_search_params():
    """
    Decorator to validate common search parameters.
    """
    return validate_query_params(
        optional_params=['query', 'q', 'search', 'filter', 'sort', 'order'],
        param_types={
            'query': str,
            'q': str,
            'search': str,
            'filter': str,
            'sort': str,
            'order': str
        }
    )


def validate_content_type(allowed_types: List[str]):
    """
    Decorator to validate request content type.
    
    Args:
        allowed_types: List of allowed content types
        
    Raises:
        ValidationError: If content type is not allowed
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            content_type = request.content_type
            
            if content_type not in allowed_types:
                raise ValidationError(
                    message=f"Content type not allowed: {content_type}",
                    details={
                        'provided_content_type': content_type,
                        'allowed_types': allowed_types
                    }
                )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def sanitize_input(data: Union[str, Dict, List], max_length: int = 10000) -> Union[str, Dict, List]:
    """
    Enhanced sanitization for input data to prevent injection attacks.
    
    Args:
        data: Input data to sanitize
        max_length: Maximum length for string values
        
    Returns:
        Sanitized data
    """
    if isinstance(data, str):
        # Use enhanced sanitization from security utils
        return InputValidator.sanitize_string(data, max_length)
    
    elif isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            # Sanitize both keys and values
            sanitized_key = InputValidator.sanitize_string(str(k), 100)  # Limit key length
            sanitized[sanitized_key] = sanitize_input(v, max_length)
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_input(item, max_length) for item in data]
    
    else:
        return data


def validate_uuid(uuid_string: str) -> bool:
    """
    Enhanced UUID validation using security utilities.
    
    Args:
        uuid_string: String to validate as UUID
        
    Returns:
        True if valid UUID, False otherwise
    """
    return InputValidator.validate_uuid(uuid_string)


def validate_email(email: str) -> bool:
    """
    Enhanced email validation using security utilities.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    return InputValidator.validate_email(email)


def validate_url(url: str) -> bool:
    """
    Basic URL validation.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL format, False otherwise
    """
    import re
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))