"""
Protocol Analysis API Endpoints

REST API endpoints for protocol compliance analysis against European
Pharmacopoeia standards. Provides single and batch analysis capabilities,
result retrieval, and analysis history management.

Features:
- POST /api/analyze - Main protocol analysis
- GET /api/analyze/{analysis_id} - Get analysis results
- POST /api/analyze/batch - Batch protocol analysis
- GET /api/analyze/history - Analysis history
- GET /api/analyze/stats - Analysis statistics
"""
import uuid
import time
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest, NotFound

from ...config.settings import settings
from ...utils import logger
from ...services.analysis_service import analysis_service
from ..schemas import (
    ProtocolAnalysisRequest,
    ProtocolAnalysisResponse,
    ProtocolAnalysisResult,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    AnalysisHistoryResponse,
    AnalysisStatsResponse,
    ErrorResponse,
    ErrorDetail,
    ComplianceAssessmentSchema,
    SimilarSectionSchema
)
from ..middleware.validation import validate_json

# Create blueprint
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analyze')

@analysis_bp.route('', methods=['POST'])
@validate_json(ProtocolAnalysisRequest)
def analyze_protocol(validated_data: ProtocolAnalysisRequest):
    """
    Analyze a protocol for compliance with pharmaceutical standards.
    
    Request Body:
        ProtocolAnalysisRequest: Protocol analysis request
        
    Returns:
        ProtocolAnalysisResponse: Analysis results
        
    Raises:
        400: Invalid request data
        500: Analysis processing error
    """
    try:
        # Use validated data from middleware
        analysis_request = validated_data
        
        logger.info(
            "Starting protocol analysis",
            protocol_title=analysis_request.protocol_title,
            protocol_length=len(analysis_request.protocol_text),
            options=analysis_request.analysis_options
        )
        
        # Extract analysis options
        options = analysis_request.analysis_options or {}
        
        # Perform protocol analysis
        result = analysis_service.analyze_protocol(
            protocol_text=analysis_request.protocol_text,
            protocol_title=analysis_request.protocol_title or "",
            protocol_type=analysis_request.protocol_type or "",
            top_k_sections=options.get('top_k_sections'),
            metadata=analysis_request.metadata
        )
        
        # Convert to response format
        response_data = _convert_analysis_result_to_schema(result)
        
        response = ProtocolAnalysisResponse(
            message=f"Protocol analysis completed successfully in {result.processing_time:.2f}s",
            data=response_data
        )
        
        logger.info(
            "Protocol analysis completed",
            analysis_id=result.analysis_id,
            compliance_score=result.compliance_analysis.compliance_score,
            processing_time=result.processing_time
        )
        
        return jsonify(response.dict()), 200
        
    except ValueError as e:
        logger.error(f"Validation error in protocol analysis: {str(e)}")
        error_response = ErrorResponse(
            message="Invalid request data",
            errors=[ErrorDetail(
                error_code="VALIDATION_ERROR",
                error_type="validation",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 400
        
    except Exception as e:
        logger.error(f"Protocol analysis failed: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Protocol analysis failed",
            errors=[ErrorDetail(
                error_code="ANALYSIS_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@analysis_bp.route('/<analysis_id>', methods=['GET'])
def get_analysis_result(analysis_id: str):
    """
    Get analysis result by ID.
    
    Args:
        analysis_id: Analysis identifier
        
    Returns:
        ProtocolAnalysisResponse: Analysis results
        
    Raises:
        404: Analysis not found
        500: Retrieval error
    """
    try:
        logger.info("Retrieving analysis result", analysis_id=analysis_id)
        
        # Get analysis result from service
        result = analysis_service.get_analysis_result(analysis_id)
        
        if result is None:
            logger.warning("Analysis not found", analysis_id=analysis_id)
            error_response = ErrorResponse(
                message="Analysis not found",
                errors=[ErrorDetail(
                    error_code="ANALYSIS_NOT_FOUND",
                    error_type="not_found",
                    details={"analysis_id": analysis_id}
                )]
            )
            return jsonify(error_response.dict()), 404
        
        # Convert to response format
        response_data = _convert_analysis_result_to_schema(result)
        
        response = ProtocolAnalysisResponse(
            message="Analysis result retrieved successfully",
            data=response_data
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve analysis result: {str(e)}", analysis_id=analysis_id, exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve analysis result",
            errors=[ErrorDetail(
                error_code="RETRIEVAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@analysis_bp.route('/batch', methods=['POST'])
@validate_json(BatchAnalysisRequest)
def batch_analyze_protocols(validated_data: BatchAnalysisRequest):
    """
    Analyze multiple protocols in batch.
    
    Request Body:
        BatchAnalysisRequest: Batch analysis request
        
    Returns:
        BatchAnalysisResponse: Batch analysis results
        
    Raises:
        400: Invalid request data
        500: Batch processing error
    """
    try:
        # Get validated request data
        batch_request = validated_data
        
        logger.info(
            "Starting batch protocol analysis",
            num_protocols=len(batch_request.protocols),
            batch_options=batch_request.batch_options
        )
        
        batch_id = f"batch_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        start_time = time.time()
        
        # Process each protocol
        results = []
        completed_count = 0
        failed_count = 0
        
        for i, protocol_request in enumerate(batch_request.protocols):
            try:
                # Analyze individual protocol
                result = analysis_service.analyze_protocol(
                    protocol_text=protocol_request.protocol_text,
                    protocol_title=protocol_request.protocol_title or "",
                    protocol_type=protocol_request.protocol_type or "",
                    metadata=protocol_request.metadata
                )
                
                # Convert to response format
                response_data = _convert_analysis_result_to_schema(result)
                
                from ..schemas.analysis import BatchAnalysisItem, ProcessingInfo
                
                item = BatchAnalysisItem(
                    index=i,
                    analysis_id=result.analysis_id,
                    result=response_data,
                    processing_info=ProcessingInfo(
                        status="completed",
                        progress=100.0,
                        completed_at=result.timestamp
                    )
                )
                results.append(item)
                completed_count += 1
                
                logger.debug(f"Completed analysis {i+1}/{len(batch_request.protocols)}")
                
            except Exception as e:
                logger.error(f"Failed to analyze protocol {i}: {str(e)}")
                
                from ..schemas.analysis import BatchAnalysisItem, ProcessingInfo
                
                item = BatchAnalysisItem(
                    index=i,
                    error=str(e),
                    processing_info=ProcessingInfo(
                        status="failed",
                        error_message=str(e)
                    )
                )
                results.append(item)
                failed_count += 1
        
        processing_time = time.time() - start_time
        
        # Create batch result
        from ..schemas.analysis import BatchAnalysisResult
        from datetime import datetime
        
        batch_result = BatchAnalysisResult(
            batch_id=batch_id,
            total_protocols=len(batch_request.protocols),
            completed_count=completed_count,
            failed_count=failed_count,
            results=results,
            batch_processing_time=processing_time,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        response = BatchAnalysisResponse(
            message=f"Batch analysis completed: {completed_count} successful, {failed_count} failed",
            data=batch_result
        )
        
        logger.info(
            "Batch protocol analysis completed",
            batch_id=batch_id,
            completed=completed_count,
            failed=failed_count,
            processing_time=processing_time
        )
        
        return jsonify(response.dict()), 200
        
    except ValueError as e:
        logger.error(f"Validation error in batch analysis: {str(e)}")
        error_response = ErrorResponse(
            message="Invalid batch request data",
            errors=[ErrorDetail(
                error_code="VALIDATION_ERROR",
                error_type="validation",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 400
        
    except Exception as e:
        logger.error(f"Batch protocol analysis failed: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Batch protocol analysis failed",
            errors=[ErrorDetail(
                error_code="BATCH_ANALYSIS_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@analysis_bp.route('/history', methods=['GET'])
def get_analysis_history():
    """
    Get analysis history with pagination.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        
    Returns:
        AnalysisHistoryResponse: Paginated analysis history
        
    Raises:
        400: Invalid query parameters
        500: Retrieval error
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Validate parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
            
        logger.info("Retrieving analysis history", page=page, per_page=per_page)
        
        # Get analysis history
        analysis_ids = analysis_service.list_analysis_history(limit=per_page * 10)  # Get more for pagination
        
        # Convert to history items
        history_items = []
        for analysis_id in analysis_ids:
            result = analysis_service.get_analysis_result(analysis_id)
            if result:
                from ..schemas.analysis import AnalysisHistoryItem
                
                item = AnalysisHistoryItem(
                    analysis_id=result.analysis_id,
                    protocol_title=result.protocol_input.protocol_title,
                    compliance_score=result.compliance_analysis.compliance_score,
                    compliance_status=result.compliance_analysis.compliance_status,
                    processing_time=result.processing_time,
                    timestamp=result.timestamp,
                    protocol_length=len(result.protocol_input.protocol_text)
                )
                history_items.append(item)
        
        # Apply pagination
        total_items = len(history_items)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = history_items[start_idx:end_idx]
        
        # Create pagination metadata
        from ..schemas.base import PaginationMetadata
        
        pagination = PaginationMetadata(
            page=page,
            per_page=per_page,
            total_items=total_items
        )
        
        response = AnalysisHistoryResponse(
            message=f"Retrieved {len(page_items)} analysis history items",
            data=page_items,
            pagination=pagination
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve analysis history: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve analysis history",
            errors=[ErrorDetail(
                error_code="HISTORY_RETRIEVAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@analysis_bp.route('/stats', methods=['GET'])
def get_analysis_stats():
    """
    Get analysis statistics.
    
    Returns:
        AnalysisStatsResponse: Analysis statistics
        
    Raises:
        500: Statistics retrieval error
    """
    try:
        logger.info("Retrieving analysis statistics")
        
        # Get stats from analysis service
        stats = analysis_service.get_analysis_stats()
        
        # Convert to schema format
        from ..schemas.analysis import AnalysisStatsSchema
        
        stats_schema = AnalysisStatsSchema(
            total_analyses=stats.get('total_analyses', 0),
            avg_compliance_score=stats.get('avg_compliance_score', 0.0),
            avg_processing_time=stats.get('avg_processing_time_seconds', 0.0),
            compliance_distribution=stats.get('compliance_status_distribution', {}),
            recent_activity=[],  # TODO: Implement recent activity tracking
            top_issues=[]  # TODO: Implement top issues tracking
        )
        
        response = AnalysisStatsResponse(
            message="Analysis statistics retrieved successfully",
            data=stats_schema
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve analysis statistics: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve analysis statistics",
            errors=[ErrorDetail(
                error_code="STATS_RETRIEVAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

def _convert_analysis_result_to_schema(result) -> ProtocolAnalysisResult:
    """
    Convert internal AnalysisResult to API schema format.
    
    Args:
        result: Internal AnalysisResult object
        
    Returns:
        ProtocolAnalysisResult: API schema format
    """
    # Convert similar sections
    similar_sections = []
    for section in result.similar_sections or []:
        schema_section = SimilarSectionSchema(
            section_text=section.section_text,
            similarity_score=section.similarity_score,
            section_metadata=section.section_metadata,
            chunk_index=section.chunk_index
        )
        similar_sections.append(schema_section)
    
    # Convert compliance analysis
    from ..schemas.analysis import ComplianceIssueSchema
    
    issues = []
    for issue_text in result.compliance_analysis.issues or []:
        issue = ComplianceIssueSchema(
            issue_type="general",
            severity="medium",
            description=issue_text,
            location="",
            recommendation="",
            reference_section=""
        )
        issues.append(issue)
    
    compliance_schema = ComplianceAssessmentSchema(
        compliance_score=result.compliance_analysis.compliance_score,
        compliance_status=result.compliance_analysis.compliance_status,
        confidence_score=result.compliance_analysis.confidence_score,
        issues=issues,
        recommendations=result.compliance_analysis.recommendations or [],
        missing_elements=result.compliance_analysis.missing_elements or [],
        terminology_corrections=result.compliance_analysis.terminology_corrections or [],
        strengths=[],  # TODO: Extract strengths from analysis
        analysis_text=result.compliance_analysis.analysis_text
    )
    
    # Create protocol analysis result
    analysis_result = ProtocolAnalysisResult(
        analysis_id=result.analysis_id,
        protocol_input={
            "protocol_text": result.protocol_input.protocol_text,
            "protocol_title": result.protocol_input.protocol_title,
            "protocol_type": result.protocol_input.protocol_type,
            "metadata": result.protocol_input.metadata or {}
        },
        similar_sections=similar_sections,
        compliance_analysis=compliance_schema,
        processing_time=result.processing_time,
        timestamp=result.timestamp,
        search_metadata=result.search_params or {},
        llm_metadata=result.llm_params or {}
    )
    
    return analysis_result