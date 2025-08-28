"""
Report Generation API Endpoints

REST API endpoints for generating, downloading, and managing compliance
analysis reports for the GUARDIAN system. Supports PDF, HTML, and JSON
formats with customization options.

Features:
- POST /api/reports/generate - Generate new reports
- GET /api/reports/{report_id} - Download specific report
- GET /api/reports - List available reports
- POST /api/reports/batch - Generate multiple reports
- GET /api/reports/templates - Available report templates
- DELETE /api/reports/{report_id} - Delete report
- GET /api/reports/stats - Report generation statistics
"""
import uuid
import time
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, send_file, abort
from werkzeug.exceptions import BadRequest, NotFound

from ...config.settings import settings
from ...utils import logger, ReportError, TemplateError
from ...services.report_service import report_service
from ...services.analysis_service import analysis_service
from ...services.visualization_service import visualization_service
from ..schemas import (
    ReportGenerationRequest,
    ReportGenerationResponse,
    BatchReportRequest,
    BatchReportResponse,
    ReportListResponse,
    ReportStatsResponse,
    TemplateListResponse,
    ErrorResponse,
    ErrorDetail
)
from ..middleware.validation import validate_json

# Create blueprint
reports_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@reports_bp.route('/generate', methods=['POST'])
@validate_json(ReportGenerationRequest)
def generate_report():
    """
    Generate a compliance analysis report.
    
    Request Body:
        ReportGenerationRequest: Report generation parameters
        
    Returns:
        ReportGenerationResponse: Generated report information
        
    Raises:
        400: Invalid request data
        404: Analysis results not found
        500: Report generation error
    """
    try:
        # Get validated request data
        report_request = request.validated_json
        
        logger.info(
            "Starting report generation",
            analysis_ids=report_request.analysis_ids,
            format=report_request.report_config.get('report_format', 'pdf'),
            template=report_request.report_config.get('template_name', 'compliance_report')
        )
        
        # Retrieve analysis results
        analysis_results = []
        missing_analyses = []
        
        for analysis_id in report_request.analysis_ids:
            result = analysis_service.get_analysis_result(analysis_id)
            if result:
                analysis_results.append(result)
            else:
                missing_analyses.append(analysis_id)
        
        if not analysis_results:
            error_response = ErrorResponse(
                message="No valid analysis results found",
                errors=[ErrorDetail(
                    error_code="NO_ANALYSIS_RESULTS",
                    error_type="not_found",
                    details={"missing_analyses": missing_analyses}
                )]
            )
            return jsonify(error_response.dict()), 404
        
        if missing_analyses:
            logger.warning(f"Some analysis results not found: {missing_analyses}")
        
        # Prepare report configuration
        from ...services.report_service import ReportConfig, ReportData
        
        config_dict = report_request.report_config or {}
        report_config = ReportConfig(
            report_format=config_dict.get('report_format', 'pdf'),
            template_name=config_dict.get('template_name', 'compliance_report'),
            include_logo=config_dict.get('include_logo', True),
            include_clustering=config_dict.get('include_clustering', True),
            include_detailed_analysis=config_dict.get('include_detailed_analysis', True),
            custom_styling=config_dict.get('custom_styling'),
            branding_options=config_dict.get('branding_options'),
            page_size=config_dict.get('page_size', 'A4'),
            orientation=config_dict.get('orientation', 'portrait')
        )
        
        # Prepare report data
        data_dict = report_request.report_data or {}
        report_data = ReportData(
            analysis_results=analysis_results,
            title=data_dict.get('title', 'Protocol Compliance Analysis Report'),
            subtitle=data_dict.get('subtitle', 'Pharmaceutical Standards Compliance'),
            author=data_dict.get('author', 'GUARDIAN Analysis System'),
            organization=data_dict.get('organization', 'Queen Mary University of London'),
            custom_sections=data_dict.get('custom_sections'),
            metadata=data_dict.get('metadata')
        )
        
        # Generate report
        report_result = report_service.generate_report(
            analysis_results=analysis_results,
            config=report_config,
            report_data=report_data
        )
        
        # Convert to response format
        from ..schemas.reports import ReportInfoSchema
        from datetime import datetime
        
        report_info = ReportInfoSchema(
            report_id=report_result.report_id,
            title=report_data.title,
            format=report_result.format,
            file_size=report_result.file_size,
            pages=report_result.pages,
            analysis_count=len(analysis_results),
            template_used=report_result.template_used,
            generation_time=report_result.generation_time,
            created_at=datetime.utcnow(),
            download_url=f"/api/reports/{report_result.report_id}",
            metadata=report_result.metadata or {}
        )
        
        response = ReportGenerationResponse(
            message=f"Report generated successfully in {report_result.generation_time:.2f}s",
            data=report_info
        )
        
        logger.info(
            "Report generation completed",
            report_id=report_result.report_id,
            format=report_result.format,
            file_size=report_result.file_size,
            generation_time=report_result.generation_time
        )
        
        return jsonify(response.dict()), 201
        
    except ReportError as e:
        logger.error(f"Report generation failed: {str(e)}")
        error_response = ErrorResponse(
            message="Report generation failed",
            errors=[ErrorDetail(
                error_code="REPORT_GENERATION_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500
        
    except TemplateError as e:
        logger.error(f"Template not found: {str(e)}")
        error_response = ErrorResponse(
            message="Report template not found",
            errors=[ErrorDetail(
                error_code="TEMPLATE_NOT_FOUND",
                error_type="not_found",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 404
        
    except ValueError as e:
        logger.error(f"Validation error in report generation: {str(e)}")
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
        logger.error(f"Unexpected error in report generation: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Report generation failed",
            errors=[ErrorDetail(
                error_code="INTERNAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@reports_bp.route('/<report_id>', methods=['GET'])
def download_report(report_id: str):
    """
    Download a generated report.
    
    Args:
        report_id: Report identifier
        
    Query Parameters:
        inline: Whether to display inline (default: false)
        
    Returns:
        File download or error response
        
    Raises:
        404: Report not found
        500: Download error
    """
    try:
        logger.info("Downloading report", report_id=report_id)
        
        # Get report information
        report_result = report_service.get_report(report_id)
        
        if not report_result:
            logger.warning("Report not found", report_id=report_id)
            error_response = ErrorResponse(
                message="Report not found",
                errors=[ErrorDetail(
                    error_code="REPORT_NOT_FOUND",
                    error_type="not_found",
                    details={"report_id": report_id}
                )]
            )
            return jsonify(error_response.dict()), 404
        
        # Check if file exists
        from pathlib import Path
        file_path = Path(report_result.file_path)
        if not file_path.exists():
            logger.error("Report file not found on disk", file_path=str(file_path))
            error_response = ErrorResponse(
                message="Report file not found",
                errors=[ErrorDetail(
                    error_code="FILE_NOT_FOUND",
                    error_type="not_found",
                    details={"file_path": str(file_path)}
                )]
            )
            return jsonify(error_response.dict()), 404
        
        # Determine MIME type
        mime_types = {
            'pdf': 'application/pdf',
            'html': 'text/html',
            'json': 'application/json',
            'png': 'image/png',
            'svg': 'image/svg+xml'
        }
        
        mime_type = mime_types.get(report_result.format, 'application/octet-stream')
        
        # Check if inline display is requested
        inline = request.args.get('inline', 'false').lower() == 'true'
        
        # Generate filename
        filename = f"{report_id}.{report_result.format}"
        
        logger.info(
            "Serving report file",
            report_id=report_id,
            file_path=str(file_path),
            mime_type=mime_type,
            inline=inline
        )
        
        return send_file(
            str(file_path),
            mimetype=mime_type,
            as_attachment=not inline,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Report download failed: {str(e)}", report_id=report_id, exception=e)
        error_response = ErrorResponse(
            message="Report download failed",
            errors=[ErrorDetail(
                error_code="DOWNLOAD_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@reports_bp.route('', methods=['GET'])
def list_reports():
    """
    List generated reports with pagination and filtering.
    
    Query Parameters:
        page: Page number (default: 1)
        per_page: Items per page (default: 20)
        format: Filter by report format
        
    Returns:
        ReportListResponse: Paginated list of reports
        
    Raises:
        400: Invalid query parameters
        500: Retrieval error
    """
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        format_filter = request.args.get('format')
        
        # Validate parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
            
        logger.info(
            "Listing reports",
            page=page,
            per_page=per_page,
            format_filter=format_filter
        )
        
        # Get reports from service
        all_reports = report_service.list_reports(limit=per_page * 10)  # Get more for filtering
        
        # Apply format filter if provided
        if format_filter:
            all_reports = [r for r in all_reports if r.format == format_filter]
        
        # Apply pagination
        total_items = len(all_reports)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_reports = all_reports[start_idx:end_idx]
        
        # Convert to response format
        from ..schemas.reports import ReportInfoSchema
        from datetime import datetime
        
        report_schemas = []
        for report_result in page_reports:
            # Get file creation time as created_at
            from pathlib import Path
            try:
                file_path = Path(report_result.file_path)
                created_at = datetime.fromtimestamp(file_path.stat().st_ctime)
            except:
                created_at = datetime.utcnow()
            
            schema = ReportInfoSchema(
                report_id=report_result.report_id,
                title=f"Report {report_result.report_id}",  # Default title
                format=report_result.format,
                file_size=report_result.file_size,
                pages=report_result.pages,
                analysis_count=0,  # Not available in list view
                template_used=report_result.template_used,
                generation_time=report_result.generation_time,
                created_at=created_at,
                download_url=f"/api/reports/{report_result.report_id}",
                metadata=report_result.metadata or {}
            )
            report_schemas.append(schema)
        
        # Create pagination metadata
        from ..schemas.base import PaginationMetadata
        
        pagination = PaginationMetadata(
            page=page,
            per_page=per_page,
            total_items=total_items
        )
        
        response = ReportListResponse(
            message=f"Retrieved {len(report_schemas)} reports",
            data=report_schemas,
            pagination=pagination
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to list reports: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve reports",
            errors=[ErrorDetail(
                error_code="LIST_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@reports_bp.route('/batch', methods=['POST'])
@validate_json(BatchReportRequest)
def generate_batch_reports():
    """
    Generate multiple reports in batch.
    
    Request Body:
        BatchReportRequest: Batch report generation request
        
    Returns:
        BatchReportResponse: Batch generation results
        
    Raises:
        400: Invalid request data
        500: Batch processing error
    """
    try:
        # Get validated request data
        batch_request = request.validated_json
        
        logger.info(
            "Starting batch report generation",
            num_requests=len(batch_request.report_requests),
            batch_options=batch_request.batch_options
        )
        
        batch_id = f"batch_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        start_time = time.time()
        
        # Process each report request
        results = []
        completed_count = 0
        failed_count = 0
        
        for i, report_req in enumerate(batch_request.report_requests):
            try:
                # Retrieve analysis results for this report
                analysis_results = []
                for analysis_id in report_req.analysis_ids:
                    result = analysis_service.get_analysis_result(analysis_id)
                    if result:
                        analysis_results.append(result)
                
                if not analysis_results:
                    raise ReportError(f"No valid analysis results found for report {i}")
                
                # Prepare configurations
                from ...services.report_service import ReportConfig, ReportData
                
                config_dict = report_req.report_config or {}
                report_config = ReportConfig(**config_dict)
                
                data_dict = report_req.report_data or {}
                report_data = ReportData(
                    analysis_results=analysis_results,
                    **data_dict
                )
                
                # Generate report
                report_result = report_service.generate_report(
                    analysis_results=analysis_results,
                    config=report_config,
                    report_data=report_data
                )
                
                # Convert to response format
                from ..schemas.reports import BatchReportItem, ReportInfoSchema
                from datetime import datetime
                
                report_info = ReportInfoSchema(
                    report_id=report_result.report_id,
                    title=report_data.title,
                    format=report_result.format,
                    file_size=report_result.file_size,
                    pages=report_result.pages,
                    analysis_count=len(analysis_results),
                    template_used=report_result.template_used,
                    generation_time=report_result.generation_time,
                    created_at=datetime.utcnow(),
                    download_url=f"/api/reports/{report_result.report_id}",
                    metadata=report_result.metadata or {}
                )
                
                item = BatchReportItem(
                    index=i,
                    report_id=report_result.report_id,
                    result=report_info,
                    processing_info={
                        "status": "completed",
                        "progress": 100.0,
                        "completed_at": datetime.utcnow()
                    }
                )
                results.append(item)
                completed_count += 1
                
                logger.debug(f"Completed report {i+1}/{len(batch_request.report_requests)}")
                
            except Exception as e:
                logger.error(f"Failed to generate report {i}: {str(e)}")
                
                from ..schemas.reports import BatchReportItem
                from datetime import datetime
                
                item = BatchReportItem(
                    index=i,
                    error=str(e),
                    processing_info={
                        "status": "failed",
                        "error_message": str(e)
                    }
                )
                results.append(item)
                failed_count += 1
        
        processing_time = time.time() - start_time
        
        # Create batch result
        from ..schemas.reports import BatchReportResult
        from datetime import datetime
        
        batch_result = BatchReportResult(
            batch_id=batch_id,
            total_reports=len(batch_request.report_requests),
            completed_count=completed_count,
            failed_count=failed_count,
            results=results,
            batch_processing_time=processing_time,
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        
        response = BatchReportResponse(
            message=f"Batch report generation completed: {completed_count} successful, {failed_count} failed",
            data=batch_result
        )
        
        logger.info(
            "Batch report generation completed",
            batch_id=batch_id,
            completed=completed_count,
            failed=failed_count,
            processing_time=processing_time
        )
        
        return jsonify(response.dict()), 200
        
    except ValueError as e:
        logger.error(f"Validation error in batch report generation: {str(e)}")
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
        logger.error(f"Batch report generation failed: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Batch report generation failed",
            errors=[ErrorDetail(
                error_code="BATCH_REPORT_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@reports_bp.route('/templates', methods=['GET'])
def list_report_templates():
    """
    Get available report templates.
    
    Returns:
        TemplateListResponse: Available report templates
        
    Raises:
        500: Template retrieval error
    """
    try:
        logger.info("Retrieving available report templates")
        
        # Get available templates from the templates directory
        from pathlib import Path
        templates_dir = Path(__file__).parent.parent.parent / "templates"
        
        templates = []
        
        # Scan for HTML templates
        for template_file in templates_dir.glob("*.html"):
            template_name = template_file.stem
            
            # Basic template info (could be enhanced with metadata files)
            template_info = {
                "template_name": template_name,
                "display_name": template_name.replace('_', ' ').title(),
                "description": f"Template for {template_name.replace('_', ' ')} reports",
                "supported_formats": ["pdf", "html"],
                "features": [
                    "Professional layout",
                    "Responsive design",
                    "Compliance analysis",
                    "Statistical summaries"
                ],
                "preview_url": None,  # Could add preview functionality
                "metadata": {
                    "file_path": str(template_file),
                    "file_size": template_file.stat().st_size
                }
            }
            
            # Add specific features based on template name
            if "compliance" in template_name:
                template_info["features"].extend([
                    "Clustering analysis",
                    "Issue tracking",
                    "Recommendations"
                ])
            
            templates.append(template_info)
        
        # Add default templates info even if files don't exist
        if not templates:
            templates = [
                {
                    "template_name": "compliance_report",
                    "display_name": "Compliance Report",
                    "description": "Standard protocol compliance analysis report",
                    "supported_formats": ["pdf", "html", "json"],
                    "features": [
                        "Executive summary",
                        "Detailed analysis results",
                        "Clustering visualization",
                        "Professional branding"
                    ],
                    "preview_url": None,
                    "metadata": {}
                },
                {
                    "template_name": "summary_report",
                    "display_name": "Summary Report",
                    "description": "Concise summary of compliance analysis",
                    "supported_formats": ["pdf", "html"],
                    "features": [
                        "Key metrics",
                        "Status overview",
                        "Quick insights"
                    ],
                    "preview_url": None,
                    "metadata": {}
                }
            ]
        
        response = TemplateListResponse(
            message=f"Retrieved {len(templates)} available templates",
            data=templates
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve report templates: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve report templates",
            errors=[ErrorDetail(
                error_code="TEMPLATE_RETRIEVAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@reports_bp.route('/<report_id>', methods=['DELETE'])
def delete_report(report_id: str):
    """
    Delete a generated report.
    
    Args:
        report_id: Report identifier
        
    Returns:
        SuccessResponse: Deletion confirmation
        
    Raises:
        404: Report not found
        500: Deletion error
    """
    try:
        logger.info("Deleting report", report_id=report_id)
        
        # Delete report
        success = report_service.delete_report(report_id)
        
        if not success:
            logger.warning("Report not found for deletion", report_id=report_id)
            error_response = ErrorResponse(
                message="Report not found",
                errors=[ErrorDetail(
                    error_code="REPORT_NOT_FOUND",
                    error_type="not_found",
                    details={"report_id": report_id}
                )]
            )
            return jsonify(error_response.dict()), 404
        
        from ..schemas.base import SuccessResponse
        
        response = SuccessResponse(
            message="Report deleted successfully",
            data={"report_id": report_id}
        )
        
        logger.info("Report deleted successfully", report_id=report_id)
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to delete report: {str(e)}", report_id=report_id, exception=e)
        error_response = ErrorResponse(
            message="Failed to delete report",
            errors=[ErrorDetail(
                error_code="DELETE_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@reports_bp.route('/stats', methods=['GET'])
def get_report_stats():
    """
    Get report generation statistics.
    
    Returns:
        ReportStatsResponse: Report statistics
        
    Raises:
        500: Statistics retrieval error
    """
    try:
        logger.info("Retrieving report statistics")
        
        # Get reports from service
        all_reports = report_service.list_reports(limit=1000)  # Get all reports
        
        # Calculate statistics
        total_reports = len(all_reports)
        format_distribution = {}
        total_size = 0
        generation_times = []
        
        for report in all_reports:
            # Format distribution
            format_distribution[report.format] = format_distribution.get(report.format, 0) + 1
            
            # Total size
            total_size += report.file_size
            
            # Generation times
            if report.generation_time > 0:
                generation_times.append(report.generation_time)
        
        # Calculate averages
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0.0
        avg_file_size = total_size / total_reports if total_reports > 0 else 0.0
        
        # Convert to schema format
        from ..schemas.reports import ReportStatsSchema
        
        stats_schema = ReportStatsSchema(
            total_reports=total_reports,
            format_distribution=format_distribution,
            total_size_mb=total_size / (1024 * 1024),
            avg_generation_time=avg_generation_time,
            avg_file_size_mb=avg_file_size / (1024 * 1024),
            recent_activity=[]  # TODO: Implement recent activity tracking
        )
        
        response = ReportStatsResponse(
            message="Report statistics retrieved successfully",
            data=stats_schema
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve report statistics: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve report statistics",
            errors=[ErrorDetail(
                error_code="STATS_RETRIEVAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500