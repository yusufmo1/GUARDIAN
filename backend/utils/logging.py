"""
Logging Configuration

Centralized logging configuration for the GUARDIAN application.
Provides structured logging with different levels and formatters
for development and production environments.

Features:
- Console and file logging
- JSON formatting for production
- Request ID tracking
- Performance logging
- Error tracking with context
"""
import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
import traceback

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON objects with consistent structure
    for easier parsing and analysis in production environments.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
            
        return json.dumps(log_entry)

class GuardianLogger:
    """
    Custom logger class for GUARDIAN application.
    
    Provides convenience methods for common logging patterns
    and maintains consistent formatting across the application.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure logger with appropriate handlers and formatters."""
        if self.logger.handlers:
            return  # Already configured
            
        self.logger.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for persistent logs
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'guardian.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # Use JSON formatter for file logs
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional extra fields."""
        self._log_with_extra(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional extra fields."""
        self._log_with_extra(logging.WARNING, message, kwargs)
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Log error message with optional exception and extra fields."""
        if exception:
            kwargs['exception_type'] = type(exception).__name__
            kwargs['exception_message'] = str(exception)
        self._log_with_extra(logging.ERROR, message, kwargs, exc_info=exception is not None)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional extra fields."""
        self._log_with_extra(logging.DEBUG, message, kwargs)
    
    def _log_with_extra(self, level: int, message: str, extra_fields: Dict[str, Any], 
                       exc_info: bool = False):
        """Internal method to log with extra fields."""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self.logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration_ms: float, user_id: str = None):
        """Log HTTP request with timing information."""
        self.info(
            f"{method} {path} - {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            request_type="http_request"
        )
    
    def log_analysis(self, protocol_id: str, document_id: str, 
                    similarity_scores: list, llm_response_time: float):
        """Log protocol analysis with performance metrics."""
        self.info(
            f"Protocol analysis completed for {protocol_id}",
            protocol_id=protocol_id,
            document_id=document_id,
            max_similarity=max(similarity_scores) if similarity_scores else 0,
            min_similarity=min(similarity_scores) if similarity_scores else 0,
            avg_similarity=sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0,
            llm_response_time_ms=llm_response_time * 1000,
            analysis_type="protocol_compliance"
        )
    
    def log_embedding_generation(self, text_length: int, num_chunks: int, 
                               embedding_time: float, model_name: str):
        """Log embedding generation performance."""
        self.info(
            f"Generated embeddings for {num_chunks} chunks",
            text_length=text_length,
            num_chunks=num_chunks,
            embedding_time_ms=embedding_time * 1000,
            model_name=model_name,
            operation_type="embedding_generation"
        )
    
    def log_vector_search(self, query_length: int, num_results: int, 
                         search_time: float, index_size: int):
        """Log vector search performance."""
        self.info(
            f"Vector search returned {num_results} results",
            query_length=query_length,
            num_results=num_results,
            search_time_ms=search_time * 1000,
            index_size=index_size,
            operation_type="vector_search"
        )

# Global logger instance
logger = GuardianLogger("guardian")

def get_logger(name: str) -> GuardianLogger:
    """
    Get a logger instance for a specific module or component.
    
    Args:
        name: Logger name, typically __name__ of the calling module
        
    Returns:
        Configured GuardianLogger instance
    """
    return GuardianLogger(name)