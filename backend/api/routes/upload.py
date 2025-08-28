"""
Document Upload and Management API Endpoints

REST API endpoints for uploading, managing, and processing European
Pharmacopoeia documents and other reference materials.

Features:
- POST /api/documents/upload - Upload reference documents
- GET /api/documents - List documents with filtering
- GET /api/documents/{doc_id} - Get document information
- POST /api/documents/{doc_id}/process - Process document
- DELETE /api/documents/{doc_id} - Delete document
- POST /api/documents/bulk - Bulk operations
- GET /api/documents/stats - Document statistics
"""
import base64
import uuid
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, NotFound

from ...config.settings import settings
from ...utils import logger, DocumentError, DocumentNotFoundError, UnsupportedFormatError
from ...services.document_service import document_service
from ..schemas import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListRequest,
    DocumentListResponse,
    DocumentProcessingRequest,
    DocumentProcessingResponse,
    DocumentStatsResponse,
    BulkDocumentRequest,
    BulkDocumentResponse,
    ErrorResponse,
    ErrorDetail,
    FileMetadata,
    ProcessingInfo
)
from ..middleware.validation import validate_json

# Create blueprint
upload_bp = Blueprint('upload', __name__, url_prefix='/api/documents')

@upload_bp.route('/upload', methods=['POST'])
@validate_json(DocumentUploadRequest)
def upload_document(validated_data: DocumentUploadRequest):
    """
    Upload a reference document for processing.
    
    Request Body:
        DocumentUploadRequest: Document upload request with base64 content
        
    Returns:
        DocumentUploadResponse: Upload result with document info
        
    Raises:
        400: Invalid request data or unsupported file type
        413: File too large
        500: Upload processing error
    """
    try:
        # Get validated request data
        upload_request = validated_data
        
        logger.info(
            "Starting document upload",
            filename=upload_request.filename,
            file_type=upload_request.file_type,
            document_type=upload_request.document_type
        )
        
        # Decode base64 file content
        try:
            file_content = base64.b64decode(upload_request.file_content)
        except Exception as e:
            logger.error(f"Failed to decode base64 content: {str(e)}")
            error_response = ErrorResponse(
                message="Invalid file content encoding",
                errors=[ErrorDetail(
                    error_code="INVALID_ENCODING",
                    error_type="validation",
                    details={"message": "File content must be valid base64"}
                )]
            )
            return jsonify(error_response.dict()), 400
        
        # Check file size
        if len(file_content) > settings.api.max_file_size:
            logger.warning(
                f"File too large: {len(file_content)} bytes",
                filename=upload_request.filename,
                max_size=settings.api.max_file_size
            )
            error_response = ErrorResponse(
                message=f"File too large (max {settings.api.max_file_size // (1024*1024)}MB)",
                errors=[ErrorDetail(
                    error_code="FILE_TOO_LARGE",
                    error_type="validation",
                    details={
                        "file_size": len(file_content),
                        "max_size": settings.api.max_file_size
                    }
                )]
            )
            return jsonify(error_response.dict()), 413
        
        # Upload document to service
        document_id = document_service.upload_document(
            file_content=file_content,
            filename=upload_request.filename,
            file_type=upload_request.file_type
        )
        
        # Get document info
        doc_info = document_service.get_document_info(document_id)
        
        # Process immediately if requested
        if upload_request.process_immediately:
            logger.info(f"Processing document immediately", document_id=document_id)
            try:
                success = document_service.process_document(document_id)
                if success:
                    # Refresh document info to get updated processing status
                    doc_info = document_service.get_document_info(document_id)
                    logger.info(f"Document processed successfully", document_id=document_id)
                else:
                    logger.warning(f"Document processing failed", document_id=document_id)
            except Exception as e:
                logger.error(f"Document processing failed: {str(e)}", document_id=document_id)
        
        # Convert to response format
        response_data = _convert_document_info_to_schema(doc_info, upload_request.document_type)
        
        response = DocumentUploadResponse(
            message=f"Document uploaded successfully: {upload_request.filename}",
            data=response_data
        )
        
        logger.info(
            "Document upload completed",
            document_id=document_id,
            filename=upload_request.filename,
            processed=doc_info.processed
        )
        
        return jsonify(response.dict()), 201
        
    except UnsupportedFormatError as e:
        logger.error(f"Unsupported file format: {str(e)}")
        error_response = ErrorResponse(
            message="Unsupported file format",
            errors=[ErrorDetail(
                error_code="UNSUPPORTED_FORMAT",
                error_type="validation",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 400
        
    except DocumentError as e:
        logger.error(f"Document upload failed: {str(e)}")
        error_response = ErrorResponse(
            message="Document upload failed",
            errors=[ErrorDetail(
                error_code="UPLOAD_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in document upload: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Document upload failed",
            errors=[ErrorDetail(
                error_code="INTERNAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@upload_bp.route('', methods=['GET'])
def list_documents():
    """
    List uploaded documents with filtering and pagination.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        document_type: Filter by document type
        processed_only: Only return processed documents
        search_term: Search term for filename
        
    Returns:
        DocumentListResponse: Paginated list of documents
        
    Raises:
        400: Invalid query parameters
        500: Retrieval error
    """
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        document_type = request.args.get('document_type')
        processed_only = request.args.get('processed_only', type=bool)
        search_term = request.args.get('search_term')
        
        # Validate parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
            
        logger.info(
            "Listing documents",
            page=page,
            per_page=per_page,
            document_type=document_type,
            processed_only=processed_only,
            search_term=search_term
        )
        
        # Get documents from service
        documents = document_service.list_documents(
            processed_only=processed_only or False,
            file_type=document_type
        )
        
        # Apply search filter if provided
        if search_term:
            search_term_lower = search_term.lower()
            documents = [
                doc for doc in documents 
                if search_term_lower in doc.filename.lower()
            ]
        
        # Apply pagination
        total_items = len(documents)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_documents = documents[start_idx:end_idx]
        
        # Convert to response format
        document_schemas = []
        for doc_info in page_documents:
            schema = _convert_document_info_to_schema(doc_info)
            document_schemas.append(schema)
        
        # Create pagination metadata
        from ..schemas.base import PaginationMetadata
        import math
        
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
        
        pagination = PaginationMetadata(
            page=page,
            per_page=per_page,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        response = DocumentListResponse(
            message=f"Retrieved {len(document_schemas)} documents",
            data=document_schemas,
            pagination=pagination
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve documents",
            errors=[ErrorDetail(
                error_code="LIST_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@upload_bp.route('/<document_id>', methods=['GET'])
def get_document_info(document_id: str):
    """
    Get information about a specific document.
    
    Args:
        document_id: Document identifier
        
    Returns:
        DocumentUploadResponse: Document information
        
    Raises:
        404: Document not found
        500: Retrieval error
    """
    try:
        logger.info("Retrieving document info", document_id=document_id)
        
        # Get document info from service
        doc_info = document_service.get_document_info(document_id)
        
        # Convert to response format
        response_data = _convert_document_info_to_schema(doc_info)
        
        response = DocumentUploadResponse(
            message="Document information retrieved successfully",
            data=response_data
        )
        
        return jsonify(response.dict()), 200
        
    except DocumentNotFoundError:
        logger.warning("Document not found", document_id=document_id)
        error_response = ErrorResponse(
            message="Document not found",
            errors=[ErrorDetail(
                error_code="DOCUMENT_NOT_FOUND",
                error_type="not_found",
                details={"document_id": document_id}
            )]
        )
        return jsonify(error_response.dict()), 404
        
    except Exception as e:
        logger.error(f"Failed to retrieve document info: {str(e)}", document_id=document_id, exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve document information",
            errors=[ErrorDetail(
                error_code="RETRIEVAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@upload_bp.route('/<document_id>/process', methods=['POST'])
@validate_json(DocumentProcessingRequest)
def process_document(validated_data: DocumentProcessingRequest, document_id: str):
    """
    Process a document through the embedding pipeline.
    
    Args:
        document_id: Document identifier
        
    Request Body:
        DocumentProcessingRequest: Processing options
        
    Returns:
        DocumentProcessingResponse: Processing result
        
    Raises:
        404: Document not found
        500: Processing error
    """
    try:
        # Get validated request data
        processing_request = validated_data
        
        logger.info(
            "Starting document processing",
            document_id=document_id,
            create_index=processing_request.create_index,
            index_name=processing_request.index_name
        )
        
        # Process document
        success = document_service.process_document(
            document_id=document_id,
            create_index=processing_request.create_index,
            index_name=processing_request.index_name
        )
        
        if not success:
            error_response = ErrorResponse(
                message="Document processing failed",
                errors=[ErrorDetail(
                    error_code="PROCESSING_FAILED",
                    error_type="processing",
                    details={"document_id": document_id}
                )]
            )
            return jsonify(error_response.dict()), 500
        
        # Get updated document info
        doc_info = document_service.get_document_info(document_id)
        
        # Convert to response format
        response_data = _convert_document_info_to_schema(doc_info)
        
        response = DocumentProcessingResponse(
            message="Document processed successfully",
            data=response_data
        )
        
        logger.info(
            "Document processing completed",
            document_id=document_id,
            processing_time=doc_info.processing_time,
            num_chunks=doc_info.num_chunks
        )
        
        return jsonify(response.dict()), 200
        
    except DocumentNotFoundError:
        logger.warning("Document not found for processing", document_id=document_id)
        error_response = ErrorResponse(
            message="Document not found",
            errors=[ErrorDetail(
                error_code="DOCUMENT_NOT_FOUND",
                error_type="not_found",
                details={"document_id": document_id}
            )]
        )
        return jsonify(error_response.dict()), 404
        
    except Exception as e:
        logger.error(f"Document processing failed: {str(e)}", document_id=document_id, exception=e)
        error_response = ErrorResponse(
            message="Document processing failed",
            errors=[ErrorDetail(
                error_code="PROCESSING_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@upload_bp.route('/<document_id>', methods=['DELETE'])
def delete_document(document_id: str):
    """
    Delete a document and its associated files.
    
    Args:
        document_id: Document identifier
        
    Returns:
        SuccessResponse: Deletion confirmation
        
    Raises:
        404: Document not found
        500: Deletion error
    """
    try:
        logger.info("Deleting document", document_id=document_id)
        
        # Delete document
        success = document_service.delete_document(document_id)
        
        if not success:
            error_response = ErrorResponse(
                message="Failed to delete document",
                errors=[ErrorDetail(
                    error_code="DELETE_FAILED",
                    error_type="processing",
                    details={"document_id": document_id}
                )]
            )
            return jsonify(error_response.dict()), 500
        
        from ..schemas.base import SuccessResponse
        
        response = SuccessResponse(
            message="Document deleted successfully",
            data={"document_id": document_id}
        )
        
        logger.info("Document deleted successfully", document_id=document_id)
        
        return jsonify(response.dict()), 200
        
    except DocumentNotFoundError:
        logger.warning("Document not found for deletion", document_id=document_id)
        error_response = ErrorResponse(
            message="Document not found",
            errors=[ErrorDetail(
                error_code="DOCUMENT_NOT_FOUND",
                error_type="not_found",
                details={"document_id": document_id}
            )]
        )
        return jsonify(error_response.dict()), 404
        
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}", document_id=document_id, exception=e)
        error_response = ErrorResponse(
            message="Failed to delete document",
            errors=[ErrorDetail(
                error_code="DELETE_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@upload_bp.route('/stats', methods=['GET'])
def get_document_stats():
    """
    Get document processing statistics.
    
    Returns:
        DocumentStatsResponse: Document statistics
        
    Raises:
        500: Statistics retrieval error
    """
    try:
        logger.info("Retrieving document statistics")
        
        # Get stats from document service
        stats = document_service.get_processing_stats()
        
        # Convert to schema format
        from ..schemas.documents import DocumentStatsSchema
        
        stats_schema = DocumentStatsSchema(
            total_documents=stats.get('total_documents', 0),
            processed_documents=stats.get('processed_documents', 0),
            failed_documents=stats.get('failed_documents', 0),
            total_size_mb=stats.get('total_storage_mb', 0.0),
            avg_processing_time=stats.get('avg_processing_time_seconds', 0.0),
            document_types=stats.get('file_types', {}),
            recent_uploads=[]  # TODO: Implement recent uploads tracking
        )
        
        response = DocumentStatsResponse(
            message="Document statistics retrieved successfully",
            data=stats_schema
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve document statistics: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve document statistics",
            errors=[ErrorDetail(
                error_code="STATS_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

def _convert_document_info_to_schema(doc_info, document_type: str = None) -> DocumentInfo:
    """
    Convert internal DocumentInfo to API schema format.
    
    Args:
        doc_info: Internal DocumentInfo object
        document_type: Optional document type override
        
    Returns:
        DocumentInfo: API schema format
    """
    from datetime import datetime
    
    # Create file metadata
    file_metadata = FileMetadata(
        filename=doc_info.filename,
        file_size=doc_info.file_size,
        file_type=doc_info.file_type,
        upload_time=datetime.fromtimestamp(doc_info.upload_time)
    )
    
    # Create processing info
    processing_status = "completed" if doc_info.processed else "pending"
    if doc_info.error:
        processing_status = "failed"
    
    from ..schemas.base import ProcessingInfo
    
    processing_info = ProcessingInfo(
        status=processing_status,
        progress=100.0 if doc_info.processed else 0.0,
        started_at=datetime.fromtimestamp(doc_info.upload_time),
        completed_at=datetime.fromtimestamp(doc_info.upload_time + doc_info.processing_time) if doc_info.processed else None,
        error_message=doc_info.error if doc_info.error else None
    )
    
    # Create document info schema
    document_info = DocumentInfo(
        document_id=doc_info.document_id,
        filename=doc_info.filename,
        file_metadata=file_metadata,
        document_type=document_type,
        processing_info=processing_info,
        metadata=doc_info.metadata or {},
        created_at=datetime.fromtimestamp(doc_info.upload_time),
        updated_at=datetime.fromtimestamp(doc_info.upload_time)
    )
    
    return document_info