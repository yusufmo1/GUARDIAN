"""
Utilities Package

Common utilities and helper functions for the GUARDIAN application.
Provides centralized access to logging, error handling, and other
utility functions.
"""

from .logging import logger, get_logger, GuardianLogger
from .errors import (
    GuardianError,
    DocumentError, DocumentNotFoundError, DocumentProcessingError, UnsupportedFormatError,
    ProtocolError, ProtocolValidationError, ProtocolTooLongError, ProtocolTooShortError,
    EmbeddingError, ModelLoadError, EmbeddingGenerationError,
    VectorDBError, IndexError, SearchError,
    LLMError, LLMConnectionError, LLMResponseError,
    ReportError, ReportGenerationError, TemplateError
)

__all__ = [
    # Logging
    'logger', 'get_logger', 'GuardianLogger',
    
    # Base errors
    'GuardianError',
    
    # Document errors
    'DocumentError', 'DocumentNotFoundError', 'DocumentProcessingError', 'UnsupportedFormatError',
    
    # Protocol errors
    'ProtocolError', 'ProtocolValidationError', 'ProtocolTooLongError', 'ProtocolTooShortError',
    
    # Embedding errors
    'EmbeddingError', 'ModelLoadError', 'EmbeddingGenerationError',
    
    # Vector DB errors
    'VectorDBError', 'IndexError', 'SearchError',
    
    # LLM errors
    'LLMError', 'LLMConnectionError', 'LLMResponseError',
    
    # Report errors
    'ReportError', 'ReportGenerationError', 'TemplateError'
]