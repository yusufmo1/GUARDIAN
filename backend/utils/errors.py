"""
Custom Exception Classes

Defines custom exceptions for the GUARDIAN application to provide
better error handling and more informative error messages.

Exception Hierarchy:
- GuardianError (base)
  - DocumentError
    - DocumentNotFoundError
    - DocumentProcessingError
    - UnsupportedFormatError
  - ProtocolError
    - ProtocolValidationError
    - ProtocolTooLongError
    - ProtocolTooShortError
  - EmbeddingError
    - ModelLoadError
    - EmbeddingGenerationError
  - VectorDBError
    - IndexError
    - SearchError
  - LLMError
    - LLMConnectionError
    - LLMResponseError
  - ReportError
    - ReportGenerationError
    - TemplateError
"""

class GuardianError(Exception):
    """
    Base exception class for all GUARDIAN-related errors.
    
    Provides a common interface for all custom exceptions
    with optional error codes and additional context.
    """
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }

# Document-related errors
class DocumentError(GuardianError):
    """Base class for document processing errors."""
    pass

class DocumentNotFoundError(DocumentError):
    """Raised when a requested document cannot be found."""
    pass

class DocumentProcessingError(DocumentError):
    """Raised when document processing fails."""
    pass

class UnsupportedFormatError(DocumentError):
    """Raised when an unsupported file format is provided."""
    pass

# Protocol-related errors
class ProtocolError(GuardianError):
    """Base class for protocol processing errors."""
    pass

class ProtocolValidationError(ProtocolError):
    """Raised when protocol validation fails."""
    pass

class ProtocolTooLongError(ProtocolError):
    """Raised when protocol exceeds maximum length."""
    pass

class ProtocolTooShortError(ProtocolError):
    """Raised when protocol is below minimum length."""
    pass

# Embedding-related errors
class EmbeddingError(GuardianError):
    """Base class for embedding processing errors."""
    pass

class ModelLoadError(EmbeddingError):
    """Raised when embedding model fails to load."""
    pass

class EmbeddingGenerationError(EmbeddingError):
    """Raised when embedding generation fails."""
    pass

# Vector database errors
class VectorDBError(GuardianError):
    """Base class for vector database errors."""
    pass

class IndexError(VectorDBError):
    """Raised when vector index operations fail."""
    pass

class SearchError(VectorDBError):
    """Raised when vector search operations fail."""
    pass

# LLM integration errors
class LLMError(GuardianError):
    """Base class for LLM integration errors."""
    pass

class LLMConnectionError(LLMError):
    """Raised when connection to LLM API fails."""
    pass

class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or malformed."""
    pass

# Report generation errors
class ReportError(GuardianError):
    """Base class for report generation errors."""
    pass

class ReportGenerationError(ReportError):
    """Raised when report generation fails."""
    pass

class TemplateError(ReportError):
    """Raised when report template processing fails."""
    pass

class TemplateNotFoundError(TemplateError):
    """Raised when a requested template cannot be found."""
    pass

# Visualization errors
class VisualizationError(GuardianError):
    """Base class for visualization generation errors."""
    pass

class DataError(GuardianError):
    """Base class for data-related errors."""
    pass

# Additional specific errors
class ValidationError(GuardianError):
    """Raised when input validation fails."""
    pass