"""
Document Management API Schemas

Pydantic models for document upload, management, and processing endpoints.
Includes validation for file uploads, document metadata, and processing status.

Features:
- Document upload request/response models
- File validation and metadata schemas
- Document processing status models
- Document listing and search schemas
- Document type and category classification
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseResponse, SuccessResponse, PaginatedResponse, FileMetadata, ProcessingInfo
from ...models.document import DocumentType, DocumentCategory

class DocumentUploadRequest(BaseModel):
    """
    Request model for document upload.
    
    Attributes:
        file_content: Base64 encoded file content
        filename: Original filename
        file_type: File type/extension
        document_type: Type of document (ground_truth, protocol, etc.)
        document_category: Detailed category classification
        metadata: Additional document metadata
        process_immediately: Whether to process the document immediately
    """
    file_content: str = Field(min_length=1)
    filename: str = Field(min_length=1, max_length=255)
    file_type: Optional[str] = Field(None, max_length=20)
    document_type: DocumentType = Field(default=DocumentType.PROTOCOL)
    document_category: DocumentCategory = Field(default=DocumentCategory.OTHER)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    process_immediately: bool = True
    
    @validator('file_content')
    def validate_file_content(cls, v):
        # Basic base64 validation
        import base64
        try:
            base64.b64decode(v)
        except Exception:
            raise ValueError('Invalid base64 encoded file content')
        return v
    
    @validator('filename')
    def validate_filename(cls, v):
        # Basic filename validation
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        if any(char in v for char in invalid_chars):
            raise ValueError('Filename contains invalid characters')
        return v

class DocumentInfo(BaseModel):
    """
    Document information schema.
    
    Attributes:
        document_id: Unique document identifier
        filename: Original filename
        file_metadata: File metadata information
        document_type: Type of document (ground_truth, protocol, etc.)
        document_category: Detailed category classification
        document_type_display: Human-readable document type
        document_category_display: Human-readable document category
        processing_info: Processing status information
        metadata: Additional document metadata
        created_at: When document was uploaded
        updated_at: When document was last updated
    """
    document_id: str = Field(max_length=100)
    filename: str = Field(max_length=255)
    file_metadata: FileMetadata
    document_type: DocumentType
    document_category: DocumentCategory
    document_type_display: str = Field(max_length=100)
    document_category_display: str = Field(max_length=100)
    processing_info: ProcessingInfo
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

class DocumentUploadResponse(SuccessResponse):
    """
    Response for document upload.
    
    Attributes:
        data: Document information
    """
    data: DocumentInfo

class DocumentListRequest(BaseModel):
    """
    Request model for listing documents.
    
    Attributes:
        page: Page number (1-based)
        per_page: Items per page
        document_type: Filter by document type
        document_category: Filter by document category
        processed_only: Only return processed documents
        search_term: Search term for filename
        sort_by: Sort field (created_at, filename, file_size)
        sort_order: Sort order (asc, desc)
    """
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    document_type: Optional[DocumentType] = None
    document_category: Optional[DocumentCategory] = None
    processed_only: Optional[bool] = None
    search_term: Optional[str] = Field(None, max_length=100)
    sort_by: str = Field("created_at", max_length=50)
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

class DocumentListResponse(PaginatedResponse):
    """
    Response for document listing.
    
    Attributes:
        data: List of document information
    """
    data: List[DocumentInfo]

class DocumentProcessingRequest(BaseModel):
    """
    Request model for document processing.
    
    Attributes:
        create_index: Whether to create vector index
        index_name: Custom index name (optional)
        processing_options: Additional processing options
    """
    create_index: bool = True
    index_name: Optional[str] = Field(None, max_length=100)
    processing_options: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('index_name')
    def validate_index_name(cls, v):
        if v is not None:
            # Basic index name validation
            if not v.replace('_', '').replace('-', '').isalnum():
                raise ValueError('Index name must contain only alphanumeric characters, hyphens, and underscores')
        return v

class DocumentProcessingResponse(SuccessResponse):
    """
    Response for document processing request.
    
    Attributes:
        data: Updated document information
    """
    data: DocumentInfo

class DocumentStatsSchema(BaseModel):
    """
    Document statistics.
    
    Attributes:
        total_documents: Total number of documents
        processed_documents: Number of processed documents
        failed_documents: Number of failed documents
        total_size_mb: Total storage size in MB
        avg_processing_time: Average processing time in seconds
        document_types: Count by document type
        recent_uploads: Recent upload activity
    """
    total_documents: int = Field(ge=0)
    processed_documents: int = Field(ge=0)
    failed_documents: int = Field(ge=0)
    total_size_mb: float = Field(ge=0)
    avg_processing_time: float = Field(ge=0)
    document_types: Dict[str, int] = Field(default_factory=dict)
    recent_uploads: List[Dict[str, Any]] = Field(default_factory=list)

class DocumentStatsResponse(SuccessResponse):
    """
    Response for document statistics.
    
    Attributes:
        data: Document statistics
    """
    data: DocumentStatsSchema

class DocumentSearchRequest(BaseModel):
    """
    Request model for document content search.
    
    Attributes:
        query: Search query text
        document_types: Filter by document types
        document_categories: Filter by document categories
        max_results: Maximum number of results
        include_content: Whether to include document content in results
    """
    query: str = Field(min_length=1, max_length=500)
    document_types: Optional[List[DocumentType]] = None
    document_categories: Optional[List[DocumentCategory]] = None
    max_results: int = Field(10, ge=1, le=50)
    include_content: bool = False

class DocumentSearchResult(BaseModel):
    """
    Document search result item.
    
    Attributes:
        document_id: Document identifier
        filename: Document filename
        document_type: Document type
        document_category: Document category
        relevance_score: Search relevance score
        excerpt: Relevant text excerpt
        metadata: Document metadata
    """
    document_id: str = Field(max_length=100)
    filename: str = Field(max_length=255)
    document_type: DocumentType
    document_category: DocumentCategory
    relevance_score: float = Field(ge=0, le=1)
    excerpt: str = Field(max_length=500)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentSearchResponse(SuccessResponse):
    """
    Response for document search.
    
    Attributes:
        data: Search results
        query: Original search query
        total_results: Total number of matching documents
    """
    data: List[DocumentSearchResult]
    query: str
    total_results: int = Field(ge=0)

class BulkDocumentOperation(str, Enum):
    """Bulk operation types."""
    DELETE = "delete"
    PROCESS = "process"
    UPDATE_METADATA = "update_metadata"

class BulkDocumentRequest(BaseModel):
    """
    Request model for bulk document operations.
    
    Attributes:
        document_ids: List of document IDs to operate on
        operation: Type of bulk operation
        parameters: Operation-specific parameters
    """
    document_ids: List[str] = Field(min_items=1, max_items=100)
    operation: BulkDocumentOperation
    parameters: Dict[str, Any] = Field(default_factory=dict)

class BulkDocumentResult(BaseModel):
    """
    Result of bulk document operation.
    
    Attributes:
        operation: Operation that was performed
        total_requested: Total number of documents requested
        successful: Number of successful operations
        failed: Number of failed operations
        results: Individual operation results
        errors: Error details for failed operations
    """
    operation: BulkDocumentOperation
    total_requested: int = Field(ge=0)
    successful: int = Field(ge=0)
    failed: int = Field(ge=0)
    results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)

class BulkDocumentResponse(SuccessResponse):
    """
    Response for bulk document operations.
    
    Attributes:
        data: Bulk operation result
    """
    data: BulkDocumentResult