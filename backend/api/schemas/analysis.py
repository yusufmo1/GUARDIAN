"""
Protocol Analysis API Schemas

Pydantic models for protocol analysis endpoints including request validation,
response formatting, and compliance assessment structures.

Features:
- Protocol analysis request/response models
- Compliance assessment schemas
- Analysis history and batch processing models
- Validation rules for protocol analysis
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseResponse, SuccessResponse, PaginatedResponse, ProcessingInfo

class ProtocolAnalysisRequest(BaseModel):
    """
    Request model for protocol analysis.
    
    Attributes:
        protocol_text: Protocol text content to analyze
        protocol_title: Optional protocol title
        protocol_type: Type of protocol (analytical, manufacturing, etc.)
        analysis_options: Analysis configuration options
        metadata: Additional protocol metadata
    """
    protocol_text: str = Field(min_length=50, max_length=50000)
    protocol_title: Optional[str] = Field(None, max_length=200)
    protocol_type: Optional[str] = Field(None, max_length=50)
    analysis_options: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('protocol_text')
    def validate_protocol_text(cls, v):
        if not v.strip():
            raise ValueError('Protocol text cannot be empty or whitespace only')
        return v.strip()
    
    @validator('protocol_title')
    def validate_protocol_title(cls, v):
        if v is not None:
            return v.strip()
        return v

class ComplianceIssueSchema(BaseModel):
    """
    Individual compliance issue.
    
    Attributes:
        issue_type: Type of issue (terminology, procedure, missing, formatting)
        severity: Severity level (critical, major, minor)
        description: Issue description
        location: Location in protocol where issue occurs
        recommendation: Recommended action to fix the issue
        reference_section: Relevant Pharmacopoeia section
    """
    issue_type: str = Field(max_length=50)
    severity: str = Field(max_length=20)
    description: str = Field(max_length=1000)
    location: Optional[str] = Field(None, max_length=200)
    recommendation: Optional[str] = Field(None, max_length=500)
    reference_section: Optional[str] = Field(None, max_length=100)

class SimilarSectionSchema(BaseModel):
    """
    Similar Pharmacopoeia section found via vector search.
    
    Attributes:
        section_text: Text content of the similar section
        similarity_score: Similarity score (0.0 to 1.0)
        section_metadata: Metadata about the section
        chunk_index: Index in the vector database
    """
    section_text: str = Field(max_length=5000)
    similarity_score: float = Field(ge=0.0, le=1.0)
    section_metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_index: int = Field(ge=0)

class ComplianceAssessmentSchema(BaseModel):
    """
    Complete compliance assessment result.
    
    Attributes:
        compliance_score: Overall compliance score (0-100)
        compliance_status: Status (compliant, partial, non-compliant)
        confidence_score: Confidence in assessment (0-100)
        issues: List of identified compliance issues
        recommendations: General recommendations
        missing_elements: Required elements that are missing
        terminology_corrections: Terminology corrections needed
        strengths: Positive aspects of the protocol
        analysis_text: Full analysis text
    """
    compliance_score: int = Field(ge=0, le=100)
    compliance_status: str = Field(max_length=20)
    confidence_score: int = Field(ge=0, le=100)
    issues: List[ComplianceIssueSchema] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    missing_elements: List[str] = Field(default_factory=list)
    terminology_corrections: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    analysis_text: str = Field(max_length=10000)

class ProtocolAnalysisResult(BaseModel):
    """
    Complete protocol analysis result.
    
    Attributes:
        analysis_id: Unique identifier for this analysis
        protocol_input: Original protocol input information
        similar_sections: List of similar Pharmacopoeia sections found
        compliance_analysis: LLM-generated compliance analysis
        processing_time: Total time taken for analysis in seconds
        timestamp: When analysis was performed
        search_metadata: Metadata about the similarity search
        llm_metadata: Metadata about the LLM analysis
    """
    analysis_id: str = Field(max_length=100)
    protocol_input: Dict[str, Any] = Field(default_factory=dict)
    similar_sections: List[SimilarSectionSchema] = Field(default_factory=list)
    compliance_analysis: ComplianceAssessmentSchema
    processing_time: float = Field(ge=0)
    timestamp: datetime
    search_metadata: Dict[str, Any] = Field(default_factory=dict)
    llm_metadata: Dict[str, Any] = Field(default_factory=dict)

class ProtocolAnalysisResponse(SuccessResponse):
    """
    Response for protocol analysis request.
    
    Attributes:
        data: Protocol analysis result
    """
    data: ProtocolAnalysisResult

class BatchAnalysisRequest(BaseModel):
    """
    Request model for batch protocol analysis.
    
    Attributes:
        protocols: List of protocols to analyze
        batch_options: Batch processing options
        notification_email: Optional email for completion notification
    """
    protocols: List[ProtocolAnalysisRequest] = Field(min_items=1, max_items=10)
    batch_options: Dict[str, Any] = Field(default_factory=dict)
    notification_email: Optional[str] = Field(None, max_length=254)
    
    @validator('notification_email')
    def validate_email(cls, v):
        if v is not None:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError('Invalid email format')
        return v

class BatchAnalysisItem(BaseModel):
    """
    Individual item in batch analysis result.
    
    Attributes:
        index: Index of protocol in original request
        analysis_id: Analysis ID if successful
        result: Analysis result if successful
        error: Error information if failed
        processing_info: Processing status information
    """
    index: int = Field(ge=0)
    analysis_id: Optional[str] = None
    result: Optional[ProtocolAnalysisResult] = None
    error: Optional[str] = None
    processing_info: ProcessingInfo

class BatchAnalysisResult(BaseModel):
    """
    Result of batch protocol analysis.
    
    Attributes:
        batch_id: Unique identifier for the batch
        total_protocols: Total number of protocols in batch
        completed_count: Number of completed analyses
        failed_count: Number of failed analyses
        results: Individual analysis results
        batch_processing_time: Total time for batch processing
        created_at: When batch was created
        completed_at: When batch was completed (if applicable)
    """
    batch_id: str = Field(max_length=100)
    total_protocols: int = Field(ge=1)
    completed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    results: List[BatchAnalysisItem] = Field(default_factory=list)
    batch_processing_time: float = Field(ge=0, default=0.0)
    created_at: datetime
    completed_at: Optional[datetime] = None

class BatchAnalysisResponse(SuccessResponse):
    """
    Response for batch analysis request.
    
    Attributes:
        data: Batch analysis result
    """
    data: BatchAnalysisResult

class AnalysisHistoryItem(BaseModel):
    """
    Item in analysis history.
    
    Attributes:
        analysis_id: Analysis identifier
        protocol_title: Protocol title (if provided)
        compliance_score: Compliance score achieved
        compliance_status: Compliance status
        processing_time: Time taken for analysis
        timestamp: When analysis was performed
        protocol_length: Length of protocol text
    """
    analysis_id: str = Field(max_length=100)
    protocol_title: Optional[str] = Field(None, max_length=200)
    compliance_score: int = Field(ge=0, le=100)
    compliance_status: str = Field(max_length=20)
    processing_time: float = Field(ge=0)
    timestamp: datetime
    protocol_length: int = Field(ge=0)

class AnalysisHistoryResponse(PaginatedResponse):
    """
    Response for analysis history request.
    
    Attributes:
        data: List of analysis history items
    """
    data: List[AnalysisHistoryItem]

class AnalysisStatsSchema(BaseModel):
    """
    Analysis statistics.
    
    Attributes:
        total_analyses: Total number of analyses performed
        avg_compliance_score: Average compliance score
        avg_processing_time: Average processing time in seconds
        compliance_distribution: Distribution of compliance statuses
        recent_activity: Recent analysis activity
        top_issues: Most common compliance issues
    """
    total_analyses: int = Field(ge=0)
    avg_compliance_score: float = Field(ge=0, le=100)
    avg_processing_time: float = Field(ge=0)
    compliance_distribution: Dict[str, int] = Field(default_factory=dict)
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)
    top_issues: List[Dict[str, Any]] = Field(default_factory=list)

class AnalysisStatsResponse(SuccessResponse):
    """
    Response for analysis statistics request.
    
    Attributes:
        data: Analysis statistics
    """
    data: AnalysisStatsSchema