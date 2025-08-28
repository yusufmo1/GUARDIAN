"""
Base Schemas and Common Models

Common Pydantic models used across all API endpoints for the GUARDIAN
backend application. Provides standardized request/response structures.

Features:
- Base response models with consistent structure
- Error response standardization  
- Common validation patterns
- Timestamp and metadata handling
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error" 
    PARTIAL = "partial"

class BaseResponse(BaseModel):
    """
    Base response model for all API endpoints.
    
    Attributes:
        status: Response status (success, error, partial)
        message: Human-readable message
        timestamp: ISO timestamp of response
        request_id: Optional request tracking ID
    """
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "Request completed successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ErrorDetail(BaseModel):
    """
    Detailed error information.
    
    Attributes:
        error_code: Machine-readable error code
        error_type: Type of error (validation, processing, etc.)
        field: Field that caused the error (for validation errors)
        details: Additional error context
    """
    error_code: str
    error_type: str = "unknown"
    field: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseResponse):
    """
    Standardized error response.
    
    Attributes:
        status: Always "error"
        errors: List of error details
        trace_id: Optional trace ID for debugging
    """
    status: ResponseStatus = ResponseStatus.ERROR
    errors: List[ErrorDetail] = Field(default_factory=list)
    trace_id: Optional[str] = None

class SuccessResponse(BaseResponse):
    """
    Standardized success response with data.
    
    Attributes:
        data: Response payload
        metadata: Optional response metadata
    """
    data: Any = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PaginationMetadata(BaseModel):
    """
    Pagination information for list responses.
    
    Attributes:
        page: Current page number (1-based)
        per_page: Items per page
        total_items: Total number of items
        total_pages: Total number of pages
        has_next: Whether there are more pages
        has_prev: Whether there are previous pages
    """
    page: int = Field(ge=1)
    per_page: int = Field(ge=1, le=100)
    total_items: int = Field(ge=0)
    total_pages: int = Field(ge=0)
    has_next: bool = False
    has_prev: bool = False
    
    @validator('total_pages', pre=True, always=True)
    def calculate_total_pages(cls, v, values):
        if 'total_items' in values and 'per_page' in values:
            import math
            return math.ceil(values['total_items'] / values['per_page'])
        return v
    
    @validator('has_next', pre=True, always=True)
    def calculate_has_next(cls, v, values):
        if 'page' in values and 'total_pages' in values:
            return values['page'] < values['total_pages']
        return v
    
    @validator('has_prev', pre=True, always=True)
    def calculate_has_prev(cls, v, values):
        if 'page' in values:
            return values['page'] > 1
        return v

class PaginatedResponse(SuccessResponse):
    """
    Paginated list response.
    
    Attributes:
        data: List of items
        pagination: Pagination metadata
    """
    data: List[Any] = Field(default_factory=list)
    pagination: PaginationMetadata

class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"

class ServiceHealth(BaseModel):
    """
    Health information for a service component.
    
    Attributes:
        name: Service name
        status: Health status
        response_time: Response time in milliseconds
        details: Additional health details
        last_check: Timestamp of last health check
    """
    name: str
    status: HealthStatus
    response_time: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    last_check: datetime = Field(default_factory=datetime.utcnow)

class SystemHealth(BaseModel):
    """
    Overall system health information.
    
    Attributes:
        status: Overall system status
        services: Health status of individual services
        version: Application version
        uptime: System uptime in seconds
        timestamp: Health check timestamp
    """
    status: HealthStatus
    services: List[ServiceHealth] = Field(default_factory=list)
    version: str = "1.0.0"
    uptime: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class FileMetadata(BaseModel):
    """
    File metadata information.
    
    Attributes:
        filename: Original filename
        file_size: File size in bytes
        file_type: File extension/MIME type
        upload_time: When file was uploaded
        checksum: File checksum (optional)
    """
    filename: str = Field(min_length=1, max_length=255)
    file_size: int = Field(ge=0)
    file_type: str
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    checksum: Optional[str] = None
    
    @validator('filename')
    def validate_filename(cls, v):
        # Basic filename validation
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in v for char in invalid_chars):
            raise ValueError('Filename contains invalid characters')
        return v

class ProcessingStatus(str, Enum):
    """Processing status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingInfo(BaseModel):
    """
    Processing status information.
    
    Attributes:
        status: Processing status
        progress: Progress percentage (0-100)
        started_at: When processing started
        completed_at: When processing completed (if applicable)
        error_message: Error message if processing failed
        estimated_completion: Estimated completion time
    """
    status: ProcessingStatus = ProcessingStatus.PENDING
    progress: float = Field(ge=0, le=100, default=0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    estimated_completion: Optional[datetime] = None