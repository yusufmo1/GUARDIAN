"""
Document Model

Manages user documents with Google Drive integration and processing status
for the multi-tenant GUARDIAN system.
"""

from sqlalchemy import Column, String, BigInteger, Text, Integer, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum as PyEnum
from datetime import datetime
from .base import BaseModel

class ProcessingStatus(PyEnum):
    """Document processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"

class DocumentType(PyEnum):
    """Document type enumeration for categorization."""
    GROUND_TRUTH = "ground_truth"  # European Pharmacopoeia standards, regulatory documents
    PROTOCOL = "protocol"          # User protocols to be analyzed
    REFERENCE = "reference"        # Additional reference materials
    ANALYSIS_RESULT = "analysis_result"  # Generated analysis reports

class DocumentCategory(PyEnum):
    """Document category enumeration for detailed classification."""
    # Ground Truth categories
    EUROPEAN_PHARMACOPOEIA = "european_pharmacopoeia"
    USP_STANDARD = "usp_standard"
    ICH_GUIDELINE = "ich_guideline"
    FDA_GUIDANCE = "fda_guidance"
    EMA_GUIDELINE = "ema_guideline"
    
    # Protocol categories
    ANALYTICAL_METHOD = "analytical_method"
    MANUFACTURING_PROTOCOL = "manufacturing_protocol"
    QUALITY_CONTROL = "quality_control"
    VALIDATION_PROTOCOL = "validation_protocol"
    CLINICAL_PROTOCOL = "clinical_protocol"
    
    # Reference categories
    RESEARCH_PAPER = "research_paper"
    TECHNICAL_DOCUMENT = "technical_document"
    STANDARD_OPERATING_PROCEDURE = "sop"
    
    # Analysis categories
    COMPLIANCE_REPORT = "compliance_report"
    ANALYSIS_SUMMARY = "analysis_summary"
    OTHER = "other"

class Document(BaseModel):
    """
    Document model for user-uploaded documents.
    
    Tracks documents through the processing pipeline from upload
    to vectorization, with Google Drive integration for persistence.
    
    Attributes:
        user_id: Foreign key to users table
        filename: Sanitized filename for storage
        original_filename: Original filename from upload
        file_size: File size in bytes
        file_type: File extension/type
        document_type: Type categorization (ground_truth, protocol, etc.)
        document_category: Detailed category classification
        google_drive_file_id: Google Drive file ID for the document
        local_file_path: Local temporary file path
        processing_status: Current processing status
        processing_started_at: When processing began
        processing_completed_at: When processing completed
        processing_error: Error message if processing failed
        num_chunks: Number of text chunks created
        vector_index_name: Name of the associated vector index
        document_metadata: Additional metadata (JSON)
        
    Relationships:
        user: The user who uploaded this document
    """
    __tablename__ = 'documents'
    
    # Foreign key to users
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    
    # Document categorization
    document_type = Column(
        SQLEnum(DocumentType, name='document_type'),
        default=DocumentType.PROTOCOL,
        nullable=False,
        index=True
    )
    document_category = Column(
        SQLEnum(DocumentCategory, name='document_category'),
        default=DocumentCategory.OTHER,
        nullable=False,
        index=True
    )
    
    # Google Drive integration
    google_drive_file_id = Column(String(255), index=True)
    local_file_path = Column(Text)
    
    # Processing information
    processing_status = Column(
        SQLEnum(ProcessingStatus, name='processing_status'),
        default=ProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_error = Column(Text)
    
    # Processing results
    num_chunks = Column(Integer)
    vector_index_name = Column(String(255))
    
    # Additional metadata
    document_metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    
    def start_processing(self):
        """Mark document as processing and set start time."""
        self.processing_status = ProcessingStatus.PROCESSING
        self.processing_started_at = datetime.utcnow()
        self.processing_error = None
    
    def complete_processing(self, num_chunks: int, vector_index_name: str, metadata: dict = None):
        """Mark document as completed and set results."""
        self.processing_status = ProcessingStatus.COMPLETED
        self.processing_completed_at = datetime.utcnow()
        self.num_chunks = num_chunks
        self.vector_index_name = vector_index_name
        if metadata:
            self.document_metadata = {**(self.document_metadata or {}), **metadata}
        self.processing_error = None
    
    def fail_processing(self, error_message: str):
        """Mark document as failed and set error message."""
        self.processing_status = ProcessingStatus.FAILED
        self.processing_completed_at = datetime.utcnow()
        self.processing_error = error_message
    
    def is_processed(self) -> bool:
        """Check if document has been successfully processed."""
        return self.processing_status == ProcessingStatus.COMPLETED
    
    def is_processing(self) -> bool:
        """Check if document is currently being processed."""
        return self.processing_status == ProcessingStatus.PROCESSING
    
    def is_failed(self) -> bool:
        """Check if document processing failed."""
        return self.processing_status == ProcessingStatus.FAILED
    
    def get_processing_time(self) -> float:
        """
        Get processing time in seconds.
        
        Returns:
            float: Processing time in seconds, or 0 if not completed
        """
        if not self.processing_started_at:
            return 0.0
        
        end_time = self.processing_completed_at or datetime.utcnow()
        return (end_time - self.processing_started_at).total_seconds()
    
    def get_file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)
    
    def set_drive_file_id(self, file_id: str):
        """Set the Google Drive file ID."""
        self.google_drive_file_id = file_id
    
    def has_drive_backup(self) -> bool:
        """Check if document is backed up to Google Drive."""
        return bool(self.google_drive_file_id)
    
    def get_display_name(self) -> str:
        """Get display name for the document."""
        return self.original_filename or self.filename
    
    def is_ground_truth(self) -> bool:
        """Check if document is a ground truth document."""
        return self.document_type == DocumentType.GROUND_TRUTH
    
    def is_protocol(self) -> bool:
        """Check if document is a protocol document."""
        return self.document_type == DocumentType.PROTOCOL
    
    def is_reference(self) -> bool:
        """Check if document is a reference document."""
        return self.document_type == DocumentType.REFERENCE
    
    def is_analysis_result(self) -> bool:
        """Check if document is an analysis result."""
        return self.document_type == DocumentType.ANALYSIS_RESULT
    
    def set_document_type(self, doc_type: DocumentType, category: DocumentCategory = None):
        """Set document type and optionally category."""
        self.document_type = doc_type
        if category:
            self.document_category = category
    
    def get_type_display_name(self) -> str:
        """Get human-readable display name for document type."""
        type_names = {
            DocumentType.GROUND_TRUTH: "Ground Truth",
            DocumentType.PROTOCOL: "Protocol",
            DocumentType.REFERENCE: "Reference",
            DocumentType.ANALYSIS_RESULT: "Analysis Result"
        }
        return type_names.get(self.document_type, "Unknown")
    
    def get_category_display_name(self) -> str:
        """Get human-readable display name for document category."""
        category_names = {
            # Ground Truth categories
            DocumentCategory.EUROPEAN_PHARMACOPOEIA: "European Pharmacopoeia",
            DocumentCategory.USP_STANDARD: "USP Standard",
            DocumentCategory.ICH_GUIDELINE: "ICH Guideline",
            DocumentCategory.FDA_GUIDANCE: "FDA Guidance",
            DocumentCategory.EMA_GUIDELINE: "EMA Guideline",
            # Protocol categories
            DocumentCategory.ANALYTICAL_METHOD: "Analytical Method",
            DocumentCategory.MANUFACTURING_PROTOCOL: "Manufacturing Protocol",
            DocumentCategory.QUALITY_CONTROL: "Quality Control",
            DocumentCategory.VALIDATION_PROTOCOL: "Validation Protocol",
            DocumentCategory.CLINICAL_PROTOCOL: "Clinical Protocol",
            # Reference categories
            DocumentCategory.RESEARCH_PAPER: "Research Paper",
            DocumentCategory.TECHNICAL_DOCUMENT: "Technical Document",
            DocumentCategory.STANDARD_OPERATING_PROCEDURE: "SOP",
            # Analysis categories
            DocumentCategory.COMPLIANCE_REPORT: "Compliance Report",
            DocumentCategory.ANALYSIS_SUMMARY: "Analysis Summary",
            DocumentCategory.OTHER: "Other"
        }
        return category_names.get(self.document_category, "Other")
    
    def to_dict(self) -> dict:
        """Convert document to dictionary."""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'file_size_mb': self.get_file_size_mb(),
            'file_type': self.file_type,
            'document_type': self.document_type.value,
            'document_category': self.document_category.value,
            'document_type_display': self.get_type_display_name(),
            'document_category_display': self.get_category_display_name(),
            'google_drive_file_id': self.google_drive_file_id,
            'has_drive_backup': self.has_drive_backup(),
            'processing_status': self.processing_status.value,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            'processing_time_seconds': self.get_processing_time(),
            'processing_error': self.processing_error,
            'num_chunks': self.num_chunks,
            'vector_index_name': self.vector_index_name,
            'metadata': self.document_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def get_user_documents(cls, db_session, user_id: str, 
                          status: ProcessingStatus = None,
                          file_type: str = None,
                          document_type: DocumentType = None,
                          document_category: DocumentCategory = None,
                          limit: int = None):
        """
        Get documents for a specific user with optional filtering.
        
        Args:
            db_session: SQLAlchemy database session
            user_id: User ID to filter by
            status: Optional processing status filter
            file_type: Optional file type filter
            document_type: Optional document type filter
            document_category: Optional document category filter
            limit: Optional limit on number of results
            
        Returns:
            Query result with user's documents
        """
        query = db_session.query(cls).filter(cls.user_id == user_id)
        
        if status:
            query = query.filter(cls.processing_status == status)
        
        if file_type:
            query = query.filter(cls.file_type == file_type)
        
        if document_type:
            query = query.filter(cls.document_type == document_type)
        
        if document_category:
            query = query.filter(cls.document_category == document_category)
        
        query = query.order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_processing_stats(cls, db_session, user_id: str = None) -> dict:
        """
        Get document processing statistics.
        
        Args:
            db_session: SQLAlchemy database session
            user_id: Optional user ID to filter by
            
        Returns:
            dict: Processing statistics
        """
        query = db_session.query(cls)
        
        if user_id:
            query = query.filter(cls.user_id == user_id)
        
        all_docs = query.all()
        
        if not all_docs:
            return {"message": "No documents found"}
        
        total_docs = len(all_docs)
        completed_docs = len([d for d in all_docs if d.is_processed()])
        failed_docs = len([d for d in all_docs if d.is_failed()])
        processing_docs = len([d for d in all_docs if d.is_processing()])
        
        total_size = sum(d.file_size for d in all_docs)
        avg_processing_time = (
            sum(d.get_processing_time() for d in all_docs if d.is_processed()) /
            max(completed_docs, 1)
        )
        
        file_types = {}
        document_types = {}
        document_categories = {}
        
        for doc in all_docs:
            file_types[doc.file_type] = file_types.get(doc.file_type, 0) + 1
            document_types[doc.document_type.value] = document_types.get(doc.document_type.value, 0) + 1
            document_categories[doc.document_category.value] = document_categories.get(doc.document_category.value, 0) + 1
        
        return {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs,
            "processing_documents": processing_docs,
            "success_rate": f"{completed_docs/total_docs*100:.1f}%" if total_docs > 0 else "0%",
            "total_storage_mb": total_size / (1024 * 1024),
            "avg_processing_time_seconds": avg_processing_time,
            "file_types": file_types,
            "document_types": document_types,
            "document_categories": document_categories
        }
    
    @classmethod 
    def get_ground_truth_documents(cls, db_session, user_id: str, limit: int = None):
        """Get only ground truth documents for a user."""
        return cls.get_user_documents(
            db_session=db_session,
            user_id=user_id,
            document_type=DocumentType.GROUND_TRUTH,
            status=ProcessingStatus.COMPLETED,
            limit=limit
        )
    
    @classmethod
    def get_protocol_documents(cls, db_session, user_id: str, limit: int = None):
        """Get only protocol documents for a user."""
        return cls.get_user_documents(
            db_session=db_session,
            user_id=user_id,
            document_type=DocumentType.PROTOCOL,
            status=ProcessingStatus.COMPLETED,
            limit=limit
        )
    
    @classmethod
    def count_documents_by_type(cls, db_session, user_id: str) -> dict:
        """Count documents by type for a user."""
        query = db_session.query(cls).filter(cls.user_id == user_id)
        documents = query.all()
        
        counts = {
            'ground_truth': 0,
            'protocol': 0,
            'reference': 0,
            'analysis_result': 0
        }
        
        for doc in documents:
            if doc.document_type == DocumentType.GROUND_TRUTH:
                counts['ground_truth'] += 1
            elif doc.document_type == DocumentType.PROTOCOL:
                counts['protocol'] += 1
            elif doc.document_type == DocumentType.REFERENCE:
                counts['reference'] += 1
            elif doc.document_type == DocumentType.ANALYSIS_RESULT:
                counts['analysis_result'] += 1
        
        return counts
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.processing_status.value})>"