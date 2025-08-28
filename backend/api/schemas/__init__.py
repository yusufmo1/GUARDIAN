"""
API Schemas Package

Centralized Pydantic models for request/response validation and serialization
across all GUARDIAN backend API endpoints.

Modules:
- base: Common base models and utilities
- analysis: Protocol analysis endpoint schemas
- documents: Document management endpoint schemas
- search: Vector search endpoint schemas
"""

# Import commonly used base models
from .base import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    ResponseStatus,
    ErrorDetail,
    HealthStatus,
    ServiceHealth,
    SystemHealth,
    FileMetadata,
    ProcessingStatus,
    ProcessingInfo,
    PaginationMetadata
)

# Import analysis schemas
from .analysis import (
    ProtocolAnalysisRequest,
    ProtocolAnalysisResponse,
    ProtocolAnalysisResult,
    ComplianceAssessmentSchema,
    ComplianceIssueSchema,
    SimilarSectionSchema,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchAnalysisResult,
    AnalysisHistoryResponse,
    AnalysisStatsResponse
)

# Import document schemas
from .documents import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListRequest,
    DocumentListResponse,
    DocumentProcessingRequest,
    DocumentProcessingResponse,
    DocumentStatsResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    BulkDocumentRequest,
    BulkDocumentResponse
)

# Import search schemas
from .search import (
    VectorSearchRequest,
    VectorSearchResponse,
    VectorSearchResult,
    MultiIndexSearchRequest,
    SearchSuggestionRequest,
    SearchSuggestionResponse,
    SearchAnalyticsRequest,
    SearchAnalyticsResponse,
    AvailableIndicesResponse
)

# Import report schemas
from .reports import (
    ReportConfigSchema,
    ReportDataSchema,
    ReportGenerationRequest,
    BatchReportRequestItem,
    BatchReportRequest,
    ReportInfoSchema,
    ReportGenerationResponse,
    BatchReportItem,
    BatchReportResult,
    BatchReportResponse,
    ReportListResponse,
    ReportTemplateInfo,
    TemplateListResponse,
    ReportStatsSchema,
    ReportStatsResponse,
    VisualizationConfigSchema,
    ClusteringConfigSchema,
    VisualizationRequest,
    VisualizationInfoSchema,
    VisualizationResponse,
    VisualizationListResponse
)

__all__ = [
    # Base models
    "BaseResponse",
    "SuccessResponse", 
    "ErrorResponse",
    "PaginatedResponse",
    "ResponseStatus",
    "ErrorDetail",
    "HealthStatus",
    "ServiceHealth",
    "SystemHealth",
    "FileMetadata",
    "ProcessingStatus",
    "ProcessingInfo",
    "PaginationMetadata",
    
    # Analysis models
    "ProtocolAnalysisRequest",
    "ProtocolAnalysisResponse",
    "ProtocolAnalysisResult",
    "ComplianceAssessmentSchema",
    "ComplianceIssueSchema",
    "SimilarSectionSchema",
    "BatchAnalysisRequest",
    "BatchAnalysisResponse",
    "BatchAnalysisResult",
    "AnalysisHistoryResponse",
    "AnalysisStatsResponse",
    
    # Document models
    "DocumentUploadRequest",
    "DocumentUploadResponse",
    "DocumentInfo",
    "DocumentListRequest",
    "DocumentListResponse",
    "DocumentProcessingRequest",
    "DocumentProcessingResponse",
    "DocumentStatsResponse",
    "DocumentSearchRequest",
    "DocumentSearchResponse",
    "BulkDocumentRequest",
    "BulkDocumentResponse",
    
    # Search models
    "VectorSearchRequest",
    "VectorSearchResponse",
    "VectorSearchResult",
    "MultiIndexSearchRequest",
    "SearchSuggestionRequest",
    "SearchSuggestionResponse",
    "SearchAnalyticsRequest",
    "SearchAnalyticsResponse",
    "AvailableIndicesResponse",
    
    # Report models
    "ReportConfigSchema",
    "ReportDataSchema",
    "ReportGenerationRequest",
    "BatchReportRequestItem",
    "BatchReportRequest",
    "ReportInfoSchema",
    "ReportGenerationResponse",
    "BatchReportItem",
    "BatchReportResult",
    "BatchReportResponse",
    "ReportListResponse",
    "ReportTemplateInfo",
    "TemplateListResponse",
    "ReportStatsSchema",
    "ReportStatsResponse",
    "VisualizationConfigSchema",
    "ClusteringConfigSchema",
    "VisualizationRequest",
    "VisualizationInfoSchema",
    "VisualizationResponse",
    "VisualizationListResponse"
]