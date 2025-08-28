"""
Report API Schemas

Pydantic models for report generation and management API endpoints.
Defines request/response schemas for all report-related operations.
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

from .base import BaseResponse, PaginationMetadata

# ===== Request Schemas =====

class ReportConfigSchema(BaseModel):
    """
    Configuration options for report generation.
    
    Attributes:
        report_format: Output format ('pdf', 'html', 'json')
        template_name: Template to use for generation
        include_logo: Whether to include organization logos
        include_clustering: Whether to include clustering analysis
        include_detailed_analysis: Whether to include detailed section analysis
        custom_styling: Custom CSS styling
        branding_options: Branding configuration
        page_size: PDF page size ('A4', 'Letter', etc.)
        orientation: Page orientation ('portrait', 'landscape')
    """
    report_format: str = Field(default="pdf", description="Output format")
    template_name: str = Field(default="compliance_report", description="Template name")
    include_logo: bool = Field(default=True, description="Include organization logos")
    include_clustering: bool = Field(default=True, description="Include clustering analysis")
    include_detailed_analysis: bool = Field(default=True, description="Include detailed analysis")
    custom_styling: Optional[str] = Field(None, description="Custom CSS styling")
    branding_options: Optional[Dict[str, Any]] = Field(None, description="Branding options")
    page_size: str = Field(default="A4", description="PDF page size")
    orientation: str = Field(default="portrait", description="Page orientation")

    @validator('report_format')
    def validate_format(cls, v):
        allowed_formats = ['pdf', 'html', 'json']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Format must be one of: {allowed_formats}")
        return v.lower()

    @validator('page_size')
    def validate_page_size(cls, v):
        allowed_sizes = ['A4', 'A3', 'Letter', 'Legal']
        if v not in allowed_sizes:
            raise ValueError(f"Page size must be one of: {allowed_sizes}")
        return v

    @validator('orientation')
    def validate_orientation(cls, v):
        allowed_orientations = ['portrait', 'landscape']
        if v.lower() not in allowed_orientations:
            raise ValueError(f"Orientation must be one of: {allowed_orientations}")
        return v.lower()

class ReportDataSchema(BaseModel):
    """
    Data configuration for report generation.
    
    Attributes:
        title: Report title
        subtitle: Report subtitle
        author: Report author
        organization: Organization name
        custom_sections: Additional custom sections
        metadata: Additional metadata
    """
    title: str = Field(default="Protocol Compliance Analysis Report", description="Report title")
    subtitle: str = Field(default="Pharmaceutical Standards Compliance", description="Report subtitle")
    author: str = Field(default="GUARDIAN Analysis System", description="Report author")
    organization: str = Field(default="Queen Mary University of London", description="Organization name")
    custom_sections: Optional[List[Dict[str, Any]]] = Field(None, description="Custom sections")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ReportGenerationRequest(BaseModel):
    """
    Request for generating a single report.
    
    Attributes:
        analysis_ids: List of analysis IDs to include in report
        report_config: Report configuration options
        report_data: Report data configuration
    """
    analysis_ids: List[str] = Field(..., min_items=1, description="Analysis IDs to include")
    report_config: Optional[ReportConfigSchema] = Field(None, description="Report configuration")
    report_data: Optional[ReportDataSchema] = Field(None, description="Report data configuration")

    @validator('analysis_ids')
    def validate_analysis_ids(cls, v):
        if not v:
            raise ValueError("At least one analysis ID is required")
        return v

class BatchReportRequestItem(BaseModel):
    """
    Single report request within a batch.
    
    Attributes:
        analysis_ids: Analysis IDs for this report
        report_config: Configuration for this report
        report_data: Data configuration for this report
    """
    analysis_ids: List[str] = Field(..., min_items=1, description="Analysis IDs")
    report_config: Optional[ReportConfigSchema] = Field(None, description="Report configuration")
    report_data: Optional[ReportDataSchema] = Field(None, description="Report data")

class BatchReportRequest(BaseModel):
    """
    Request for generating multiple reports in batch.
    
    Attributes:
        report_requests: List of individual report requests
        batch_options: Batch processing options
    """
    report_requests: List[BatchReportRequestItem] = Field(..., min_items=1, description="Report requests")
    batch_options: Optional[Dict[str, Any]] = Field(None, description="Batch options")

    @validator('report_requests')
    def validate_report_requests(cls, v):
        if not v:
            raise ValueError("At least one report request is required")
        if len(v) > 10:  # Limit batch size
            raise ValueError("Maximum 10 reports allowed per batch")
        return v

# ===== Response Schemas =====

class ReportInfoSchema(BaseModel):
    """
    Information about a generated report.
    
    Attributes:
        report_id: Unique report identifier
        title: Report title
        format: Report format
        file_size: File size in bytes
        pages: Number of pages (for PDF)
        analysis_count: Number of analyses included
        template_used: Template that was used
        generation_time: Time taken to generate (seconds)
        created_at: When report was created
        download_url: URL to download the report
        metadata: Additional metadata
    """
    report_id: str = Field(..., description="Unique report identifier")
    title: str = Field(..., description="Report title")
    format: str = Field(..., description="Report format")
    file_size: int = Field(..., description="File size in bytes")
    pages: Optional[int] = Field(None, description="Number of pages")
    analysis_count: int = Field(..., description="Number of analyses included")
    template_used: str = Field(..., description="Template used")
    generation_time: float = Field(..., description="Generation time in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    download_url: str = Field(..., description="Download URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ReportGenerationResponse(BaseResponse):
    """Response for report generation request."""
    data: ReportInfoSchema

class BatchReportItem(BaseModel):
    """
    Single report result within a batch response.
    
    Attributes:
        index: Index in the batch
        report_id: Report ID (if successful)
        result: Report information (if successful)
        error: Error message (if failed)
        processing_info: Processing status information
    """
    index: int = Field(..., description="Index in batch")
    report_id: Optional[str] = Field(None, description="Report ID if successful")
    result: Optional[ReportInfoSchema] = Field(None, description="Report info if successful")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_info: Dict[str, Any] = Field(default_factory=dict, description="Processing status")

class BatchReportResult(BaseModel):
    """
    Result of batch report generation.
    
    Attributes:
        batch_id: Unique batch identifier
        total_reports: Total number of reports requested
        completed_count: Number of successfully completed reports
        failed_count: Number of failed reports
        results: Individual report results
        batch_processing_time: Total batch processing time
        created_at: When batch was started
        completed_at: When batch was completed
    """
    batch_id: str = Field(..., description="Batch identifier")
    total_reports: int = Field(..., description="Total reports requested")
    completed_count: int = Field(..., description="Successfully completed")
    failed_count: int = Field(..., description="Failed reports")
    results: List[BatchReportItem] = Field(..., description="Individual results")
    batch_processing_time: float = Field(..., description="Total processing time")
    created_at: datetime = Field(..., description="Batch start time")
    completed_at: datetime = Field(..., description="Batch completion time")

class BatchReportResponse(BaseResponse):
    """Response for batch report generation."""
    data: BatchReportResult

class ReportListResponse(BaseResponse):
    """Response for report listing."""
    data: List[ReportInfoSchema]
    pagination: Optional[PaginationMetadata] = None

class ReportTemplateInfo(BaseModel):
    """
    Information about a report template.
    
    Attributes:
        template_name: Internal template name
        display_name: User-friendly display name
        description: Template description
        supported_formats: List of supported output formats
        features: List of template features
        preview_url: URL to template preview (optional)
        metadata: Additional template metadata
    """
    template_name: str = Field(..., description="Internal template name")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Template description")
    supported_formats: List[str] = Field(..., description="Supported output formats")
    features: List[str] = Field(..., description="Template features")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class TemplateListResponse(BaseResponse):
    """Response for template listing."""
    data: List[ReportTemplateInfo]

class ReportStatsSchema(BaseModel):
    """
    Report generation statistics.
    
    Attributes:
        total_reports: Total number of reports generated
        format_distribution: Distribution by format
        total_size_mb: Total size of all reports in MB
        avg_generation_time: Average generation time in seconds
        avg_file_size_mb: Average file size in MB
        recent_activity: Recent report generation activity
    """
    total_reports: int = Field(..., description="Total reports generated")
    format_distribution: Dict[str, int] = Field(..., description="Distribution by format")
    total_size_mb: float = Field(..., description="Total size in MB")
    avg_generation_time: float = Field(..., description="Average generation time")
    avg_file_size_mb: float = Field(..., description="Average file size in MB")
    recent_activity: List[Dict[str, Any]] = Field(..., description="Recent activity")

class ReportStatsResponse(BaseResponse):
    """Response for report statistics."""
    data: ReportStatsSchema

# ===== Visualization Schemas =====

class VisualizationConfigSchema(BaseModel):
    """
    Configuration for visualization generation.
    
    Attributes:
        plot_type: Type of visualization
        color_scheme: Color scheme to use
        figure_size: Figure size as [width, height]
        interactive: Whether to create interactive plot
        save_format: Format to save plot
        theme: Visual theme
    """
    plot_type: str = Field(default="scatter", description="Visualization type")
    color_scheme: str = Field(default="viridis", description="Color scheme")
    figure_size: List[int] = Field(default=[12, 8], description="Figure size [width, height]")
    interactive: bool = Field(default=False, description="Create interactive plot")
    save_format: str = Field(default="png", description="Save format")
    theme: str = Field(default="light", description="Visual theme")

    @validator('plot_type')
    def validate_plot_type(cls, v):
        allowed_types = ['scatter', 'heatmap', 'network', 'trends', 'clustering']
        if v.lower() not in allowed_types:
            raise ValueError(f"Plot type must be one of: {allowed_types}")
        return v.lower()

    @validator('save_format')
    def validate_save_format(cls, v):
        allowed_formats = ['png', 'svg', 'html', 'json']
        if v.lower() not in allowed_formats:
            raise ValueError(f"Save format must be one of: {allowed_formats}")
        return v.lower()

    @validator('theme')
    def validate_theme(cls, v):
        allowed_themes = ['light', 'dark', 'academic']
        if v.lower() not in allowed_themes:
            raise ValueError(f"Theme must be one of: {allowed_themes}")
        return v.lower()

class ClusteringConfigSchema(BaseModel):
    """
    Configuration for clustering analysis.
    
    Attributes:
        algorithm: Clustering algorithm to use
        n_clusters: Number of clusters (optional)
        normalize_features: Whether to normalize features
        random_state: Random state for reproducibility
    """
    algorithm: str = Field(default="kmeans", description="Clustering algorithm")
    n_clusters: Optional[int] = Field(None, description="Number of clusters")
    normalize_features: bool = Field(default=True, description="Normalize features")
    random_state: int = Field(default=42, description="Random state")

    @validator('algorithm')
    def validate_algorithm(cls, v):
        allowed_algorithms = ['kmeans', 'dbscan', 'hierarchical']
        if v.lower() not in allowed_algorithms:
            raise ValueError(f"Algorithm must be one of: {allowed_algorithms}")
        return v.lower()

    @validator('n_clusters')
    def validate_n_clusters(cls, v):
        if v is not None and (v < 2 or v > 10):
            raise ValueError("Number of clusters must be between 2 and 10")
        return v

class VisualizationRequest(BaseModel):
    """
    Request for creating a visualization.
    
    Attributes:
        analysis_ids: Analysis IDs to visualize
        visualization_config: Visualization configuration
        clustering_config: Clustering configuration (optional)
    """
    analysis_ids: List[str] = Field(..., min_items=1, description="Analysis IDs")
    visualization_config: Optional[VisualizationConfigSchema] = Field(None, description="Visualization config")
    clustering_config: Optional[ClusteringConfigSchema] = Field(None, description="Clustering config")

class VisualizationInfoSchema(BaseModel):
    """
    Information about a generated visualization.
    
    Attributes:
        visualization_id: Unique identifier
        plot_type: Type of visualization
        format: File format
        file_size: File size in bytes
        interactive: Whether visualization is interactive
        generation_time: Time taken to generate
        created_at: Creation timestamp
        download_url: URL to download visualization
        metadata: Additional metadata
    """
    visualization_id: str = Field(..., description="Unique identifier")
    plot_type: str = Field(..., description="Visualization type")
    format: str = Field(..., description="File format")
    file_size: int = Field(..., description="File size in bytes")
    interactive: bool = Field(..., description="Is interactive")
    generation_time: float = Field(..., description="Generation time")
    created_at: datetime = Field(..., description="Creation timestamp")
    download_url: str = Field(..., description="Download URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class VisualizationResponse(BaseResponse):
    """Response for visualization generation."""
    data: VisualizationInfoSchema

class VisualizationListResponse(BaseResponse):
    """Response for visualization listing."""
    data: List[VisualizationInfoSchema]
    pagination: Optional[PaginationMetadata] = None

# ===== Export Schemas to __init__.py =====

__all__ = [
    # Request schemas
    'ReportConfigSchema',
    'ReportDataSchema', 
    'ReportGenerationRequest',
    'BatchReportRequestItem',
    'BatchReportRequest',
    'VisualizationConfigSchema',
    'ClusteringConfigSchema',
    'VisualizationRequest',
    
    # Response schemas
    'ReportInfoSchema',
    'ReportGenerationResponse',
    'BatchReportItem',
    'BatchReportResult',
    'BatchReportResponse',
    'ReportListResponse',
    'ReportTemplateInfo',
    'TemplateListResponse',
    'ReportStatsSchema',
    'ReportStatsResponse',
    'VisualizationInfoSchema',
    'VisualizationResponse',
    'VisualizationListResponse'
]