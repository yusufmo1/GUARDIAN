"""
Session-Aware Analysis API Endpoints

Multi-tenant API endpoints for protocol compliance analysis with user isolation.
Integrates with session-based vector databases and Google Drive persistence.

Features:
- POST /api/session/analyze - Session-based protocol analysis
- GET /api/session/analyze/{analysis_id} - Get session analysis results
- POST /api/session/documents/upload - Upload documents to user session
- GET /api/session/documents - List user's session documents
- POST /api/session/search - Search user's vector database
- GET /api/session/stats - Get user session statistics
- POST /api/session/backup - Backup user session to Drive
- POST /api/session/cleanup - Cleanup user session
"""

import uuid
import time
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, ValidationError
from werkzeug.datastructures import FileStorage

from ...services.session_aware_vector_service import session_aware_vector_service
from ...services.analysis_service import analysis_service
from ...integrations.llm.services.compliance_service import compliance_service
from ...core.processors.document_processor import DocumentProcessor
from ...api.middleware.auth_middleware import require_authentication
from ...models.document import DocumentType, DocumentCategory
from ...utils import logger
from ...config.settings import settings


# Create blueprint
session_analysis_bp = Blueprint('session_analysis', __name__, url_prefix='/api/session')


# Pydantic models for request validation
class SessionAnalysisRequest(BaseModel):
    protocol_text: str
    protocol_title: Optional[str] = None
    protocol_type: Optional[str] = None
    analysis_options: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class SessionSearchRequest(BaseModel):
    query_text: str
    top_k: Optional[int] = 10
    query_type: Optional[str] = "similarity"
    filters: Optional[Dict[str, Any]] = None

class DocumentUploadRequest(BaseModel):
    filename: str
    content: str
    document_type: DocumentType = DocumentType.PROTOCOL
    document_category: DocumentCategory = DocumentCategory.OTHER
    metadata: Optional[Dict[str, Any]] = None

class SessionActionRequest(BaseModel):
    force: Optional[bool] = False


@session_analysis_bp.route('/initialize', methods=['POST'])
@require_authentication
def initialize_session():
    """
    Initialize a vector database session for the current user.
    
    Requires authentication and creates a new session or reuses existing one.
    
    Returns:
        JSON response with session information
    """
    try:
        user = g.current_user
        session = g.current_session
        
        logger.info(f"Session initialization request - User: {user}, Session: {session}")
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        # Initialize user session
        success = session_aware_vector_service.initialize_user_session(user_id, session_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session initialized successfully',
                'data': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'initialized': True
                }
            })
        else:
            return jsonify({
                'error': 'Failed to initialize session',
                'error_code': 'SESSION_INIT_ERROR',
                'message': 'Could not initialize vector database session'
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to initialize session: {str(e)}", exception=e)
        return jsonify({
            'error': 'Session initialization failed',
            'error_code': 'INITIALIZATION_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/analyze', methods=['POST'])
@require_authentication
def analyze_protocol_session():
    """
    Analyze a protocol using the user's session-based vector database.
    
    Requires authentication and active session.
    
    Request body:
        SessionAnalysisRequest: Protocol analysis request
        
    Returns:
        JSON response with analysis results
    """
    try:
        # Validate request data
        try:
            request_data = SessionAnalysisRequest(**request.get_json())
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': e.errors()
            }), 400
        
        user = g.current_user
        session = g.current_session
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        logger.info(f"Starting session-based protocol analysis for user {user_id}")
        
        # Search user's vector database for similar sections
        search_response = session_aware_vector_service.search_user_documents(
            user_id=user_id,
            session_id=session_id,
            query_text=request_data.protocol_text,
            top_k=request_data.analysis_options.get('top_k_sections', 10) if request_data.analysis_options else 10
        )
        
        if not search_response:
            return jsonify({
                'error': 'No active session found',
                'error_code': 'SESSION_NOT_FOUND',
                'message': 'Please initialize a session first'
            }), 400
        
        # Create similar sections from search results
        similar_sections = []
        for result in search_response.results:
            similar_sections.append({
                'section_text': result.original_result.text,
                'similarity_score': result.final_score,
                'section_metadata': result.original_result.metadata,
                'chunk_index': result.original_result.id
            })
        
        # Use the compliance service for LLM analysis
        compliance_analysis = compliance_service.analyze_compliance(
            protocol_text=request_data.protocol_text,
            similar_sections=similar_sections,
            protocol_title=request_data.protocol_title,
            protocol_type=request_data.protocol_type
        )
        
        # Create analysis result
        analysis_result = {
            'analysis_id': str(uuid.uuid4()),
            'user_id': user_id,
            'session_id': session_id,
            'protocol_title': request_data.protocol_title,
            'protocol_type': request_data.protocol_type,
            'similar_sections': similar_sections,
            'compliance_analysis': compliance_analysis,
            'processing_time': search_response.search_time,
            'timestamp': time.time(),
            'search_stats': {
                'total_results': search_response.total_results,
                'indices_searched': search_response.indices_searched,
                'query_analysis': search_response.query_analysis
            }
        }
        
        # Save analysis results to user's Google Drive
        try:
            drive_service = session_aware_vector_service.get_user_drive_service(user_id)
            if drive_service:
                drive_file_id = drive_service.save_analysis_results(
                    analysis_result['analysis_id'], 
                    analysis_result
                )
                analysis_result['drive_file_id'] = drive_file_id
                logger.info(f"Saved analysis results to Drive for user {user_id}: {drive_file_id}")
            else:
                logger.warning(f"Could not save analysis results to Drive - Drive service unavailable for user {user_id}")
        except Exception as save_error:
            logger.error(f"Failed to save analysis results to Drive: {str(save_error)}", exception=save_error)
            # Continue even if Drive save fails - results are still returned to user
        
        logger.info(f"Session-based analysis completed for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Protocol analysis completed successfully',
            'data': analysis_result
        })
        
    except Exception as e:
        logger.error(f"Session-based analysis failed: {str(e)}", exception=e)
        return jsonify({
            'error': 'Analysis failed',
            'error_code': 'ANALYSIS_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/documents/upload', methods=['POST'])
@require_authentication
def upload_documents_to_session():
    """
    Upload documents to the user's vector database session.
    
    Supports both JSON content and file uploads.
    
    Request body:
        DocumentUploadRequest or multipart file upload
        
    Returns:
        JSON response with upload results
    """
    try:
        user = g.current_user
        session = g.current_session
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        documents = []
        document_processor = DocumentProcessor()
        
        # Extract document type information from form data or default values
        document_type_str = request.form.get('document_type', DocumentType.PROTOCOL.value)
        document_category_str = request.form.get('document_category', DocumentCategory.OTHER.value)
        
        try:
            document_type = DocumentType(document_type_str)
        except ValueError:
            document_type = DocumentType.PROTOCOL
            
        try:
            document_category = DocumentCategory(document_category_str)
        except ValueError:
            document_category = DocumentCategory.OTHER
        
        # Debug logging
        logger.debug(f"Request content_type: {request.content_type}")
        logger.debug(f"Request files: {list(request.files.keys())}")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Document type: {document_type}, category: {document_category}")
        
        # Check if this is a file upload request
        has_files = bool(request.files)
        
        # Handle file upload with proper chunking
        if has_files:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename:
                    # Save file temporarily for processing
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                        file.save(tmp_file.name)
                        temp_path = tmp_file.name
                    
                    try:
                        # Process document with proper chunking
                        chunks = document_processor.chunk_document(temp_path)
                        
                        # Check if we got any processable content
                        if not chunks:
                            logger.warning(f"Document {file.filename} could not be processed - no extractable text found. This may be a scanned PDF or have unsupported formatting.")
                            # Still upload to Drive but skip vector processing
                            documents.append({
                                'filename': file.filename,
                                'file_path': temp_path,  # Add file path for Google Drive backup
                                'chunks': [],  # Empty chunks - will skip vector processing
                                'processing_warning': 'No extractable text found - document uploaded to Drive only',
                                'metadata': {
                                    'uploaded_by': user_id,
                                    'session_id': session_id,
                                    'upload_method': 'file',
                                    'original_filename': file.filename,
                                    'processing_status': 'text_extraction_failed',
                                    'document_type': document_type.value,
                                    'document_category': document_category.value
                                }
                            })
                        else:
                            # Convert chunks to documents format
                            # Include file_path so the document gets backed up to Google Drive
                            documents.append({
                                'filename': file.filename,
                                'file_path': temp_path,  # Add file path for Google Drive backup
                                'chunks': chunks,
                                'metadata': {
                                    'uploaded_by': user_id,
                                    'session_id': session_id,
                                    'upload_method': 'file',
                                    'original_filename': file.filename,
                                    'processing_status': 'success',
                                    'document_type': document_type.value,
                                    'document_category': document_category.value
                                }
                            })
                        
                        logger.info(f"Processed {file.filename} into {len(chunks)} chunks")
                        
                    except Exception as e:
                        # Clean up temporary file on error
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        raise
        
        # Handle JSON content
        else:
            # Only try to parse JSON if there are no files
            try:
                json_data = request.get_json()
                if isinstance(json_data, list):
                    # Multiple documents
                    for doc_data in json_data:
                        request_data = DocumentUploadRequest(**doc_data)
                        
                        # Save content temporarily for processing
                        import tempfile
                        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
                            tmp_file.write(request_data.content)
                            temp_path = tmp_file.name
                        
                        try:
                            # Process with document processor
                            chunks = document_processor.chunk_document(temp_path)
                            
                            documents.append({
                                'filename': request_data.filename,
                                'chunks': chunks,
                                'metadata': {
                                    **(request_data.metadata or {}),
                                    'uploaded_by': user_id,
                                    'session_id': session_id,
                                    'upload_method': 'json',
                                    'original_filename': request_data.filename
                                }
                            })
                        finally:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                else:
                    # Single document
                    request_data = DocumentUploadRequest(**json_data)
                    
                    # Save content temporarily for processing
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
                        tmp_file.write(request_data.content)
                        temp_path = tmp_file.name
                    
                    try:
                        # Process with document processor
                        chunks = document_processor.chunk_document(temp_path)
                        
                        documents.append({
                            'filename': request_data.filename,
                            'chunks': chunks,
                            'metadata': {
                                **(request_data.metadata or {}),
                                'uploaded_by': user_id,
                                'session_id': session_id,
                                'upload_method': 'json',
                                'original_filename': request_data.filename
                            }
                        })
                    finally:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
            except ValidationError as e:
                return jsonify({
                    'error': 'Invalid document data',
                    'error_code': 'VALIDATION_ERROR',
                    'details': e.errors()
                }), 400
        
        if not documents:
            return jsonify({
                'error': 'No documents provided',
                'error_code': 'NO_DOCUMENTS',
                'message': 'Provide documents via files or JSON content'
            }), 400
        
        # Add documents to session
        try:
            success = session_aware_vector_service.add_documents_to_user_session(
                user_id, session_id, documents, document_type, document_category
            )
            
            if success:
                logger.info(f"Added {len(documents)} documents to session for user {user_id}")
                
                # Count documents by processing status
                docs_with_content = sum(1 for doc in documents if doc.get('chunks') and len(doc['chunks']) > 0)
                docs_without_content = sum(1 for doc in documents if not doc.get('chunks') or len(doc['chunks']) == 0)
                
                # Create response message based on processing results
                if docs_without_content > 0:
                    if docs_with_content > 0:
                        message = f'Uploaded {len(documents)} documents - {docs_with_content} processed for analysis, {docs_without_content} stored in Drive only'
                    else:
                        message = f'Uploaded {len(documents)} documents to Drive only - no extractable text found for analysis'
                else:
                    message = f'Successfully uploaded and processed {len(documents)} documents'
                
                response_data = {
                    'documents_uploaded': len(documents),
                    'documents_with_content': docs_with_content,
                    'documents_without_content': docs_without_content,
                    'user_id': user_id,
                    'session_id': session_id
                }
                
                # Add warnings for documents without content
                if docs_without_content > 0:
                    warnings = []
                    for doc in documents:
                        if not doc.get('chunks') or len(doc['chunks']) == 0:
                            warning_msg = doc.get('processing_warning', f"{doc.get('filename', 'Unknown file')} could not be processed for text analysis")
                            warnings.append(warning_msg)
                    response_data['warnings'] = warnings
                
                response = jsonify({
                    'success': True,
                    'message': message,
                    'data': response_data
                })
                
                # Clean up temporary files after successful upload
                for doc in documents:
                    if 'file_path' in doc and os.path.exists(doc['file_path']):
                        try:
                            os.unlink(doc['file_path'])
                            logger.debug(f"Cleaned up temporary file: {doc['file_path']}")
                        except Exception as cleanup_error:
                            logger.warning(f"Failed to cleanup temp file {doc['file_path']}: {cleanup_error}")
                
                # Explicitly clear documents from memory
                del documents
                return response
            else:
                return jsonify({
                    'error': 'Failed to upload documents',
                    'error_code': 'UPLOAD_ERROR',
                    'message': 'Could not add documents to session'
                }), 500
        finally:
            # Ensure temp files are cleaned up even on error
            if 'documents' in locals():
                for doc in documents:
                    if 'file_path' in doc and os.path.exists(doc['file_path']):
                        try:
                            os.unlink(doc['file_path'])
                        except:
                            pass  # Ignore cleanup errors
                del documents
            # Force garbage collection for large document uploads
            import gc
            gc.collect()
            
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}", exception=e)
        return jsonify({
            'error': 'Document upload failed',
            'error_code': 'UPLOAD_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/search', methods=['POST'])
@require_authentication
def search_session_documents():
    """
    Search documents in the user's vector database session.
    
    Request body:
        SessionSearchRequest: Search parameters
        
    Returns:
        JSON response with search results
    """
    try:
        # Validate request data
        try:
            request_data = SessionSearchRequest(**request.get_json())
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': e.errors()
            }), 400
        
        user = g.current_user
        session = g.current_session
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        # Search user's documents
        search_response = session_aware_vector_service.search_user_documents(
            user_id=user_id,
            session_id=session_id,
            query_text=request_data.query_text,
            top_k=request_data.top_k,
            query_type=request_data.query_type,
            filters=request_data.filters
        )
        
        if not search_response:
            return jsonify({
                'error': 'No active session found',
                'error_code': 'SESSION_NOT_FOUND',
                'message': 'Please initialize a session first'
            }), 400
        
        # Convert search response to JSON-serializable format
        results = []
        for result in search_response.results:
            results.append({
                'text': result.original_result.text,
                'score': result.final_score,
                'metadata': result.original_result.metadata,
                'ranking_factors': result.ranking_factors,
                'explanation': result.explanation
            })
        
        return jsonify({
            'success': True,
            'message': f'Found {len(results)} results',
            'data': {
                'query': request_data.query_text,
                'results': results,
                'total_results': search_response.total_results,
                'search_time': search_response.search_time,
                'query_analysis': search_response.query_analysis
            }
        })
        
    except Exception as e:
        logger.error(f"Session search failed: {str(e)}", exception=e)
        return jsonify({
            'error': 'Search failed',
            'error_code': 'SEARCH_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/stats', methods=['GET'])
@require_authentication
def get_session_stats():
    """
    Get statistics for the user's current session.
    
    Returns:
        JSON response with session statistics
    """
    try:
        user = g.current_user
        session = g.current_session
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        # Get session statistics
        stats = session_aware_vector_service.get_user_session_stats(user_id, session_id)
        
        if not stats:
            return jsonify({
                'error': 'No active session found',
                'error_code': 'SESSION_NOT_FOUND',
                'message': 'Please initialize a session first'
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Session statistics retrieved',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get session stats: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to get session statistics',
            'error_code': 'STATS_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/backup', methods=['POST'])
@require_authentication
def backup_session():
    """
    Backup the user's session to Google Drive.
    
    Request body:
        SessionActionRequest: Optional parameters
        
    Returns:
        JSON response with backup status
    """
    try:
        # Validate request data
        force = False
        if request.is_json and request.json:
            try:
                request_data = SessionActionRequest(**request.json)
                force = request_data.force
            except ValidationError:
                pass
        
        user = g.current_user
        session = g.current_session
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        # Backup session
        success = session_aware_vector_service.backup_user_session(
            user_id, session_id, force
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session backed up successfully',
                'data': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'backed_up': True
                }
            })
        else:
            return jsonify({
                'error': 'Backup failed',
                'error_code': 'BACKUP_ERROR',
                'message': 'Could not backup session to Drive'
            }), 500
            
    except Exception as e:
        logger.error(f"Session backup failed: {str(e)}", exception=e)
        return jsonify({
            'error': 'Backup failed',
            'error_code': 'BACKUP_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/cleanup', methods=['POST'])
@require_authentication
def cleanup_session():
    """
    Cleanup the user's current session.
    
    Request body:
        SessionActionRequest: Optional parameters
        
    Returns:
        JSON response with cleanup status
    """
    try:
        # Validate request data
        backup_first = True
        if request.is_json and request.json:
            try:
                request_data = SessionActionRequest(**request.json)
                backup_first = not request_data.force  # If force=True, skip backup
            except ValidationError:
                pass
        
        user = g.current_user
        session = g.current_session
        
        user_id = str(user['id'])
        session_id = str(session['id'])
        
        # Cleanup session
        success = session_aware_vector_service.cleanup_user_session(
            user_id, session_id, backup_first
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session cleaned up successfully',
                'data': {
                    'user_id': user_id,
                    'session_id': session_id,
                    'cleaned_up': True
                }
            })
        else:
            return jsonify({
                'error': 'Cleanup failed',
                'error_code': 'CLEANUP_ERROR',
                'message': 'Could not cleanup session'
            }), 500
            
    except Exception as e:
        logger.error(f"Session cleanup failed: {str(e)}", exception=e)
        return jsonify({
            'error': 'Cleanup failed',
            'error_code': 'CLEANUP_ERROR',
            'message': str(e)
        }), 500


@session_analysis_bp.route('/drive/files', methods=['GET'])
@require_authentication
def list_drive_files():
    """
    List the user's files from Google Drive.
    
    Query parameters:
        file_type: Type of files to list (default: 'document')
        
    Returns:
        JSON response with file list
    """
    try:
        user = g.current_user
        user_id = str(user['id'])
        
        file_type = request.args.get('file_type', 'document')
        
        # Get user's Drive files
        files = session_aware_vector_service.get_user_drive_files(user_id, file_type)
        
        return jsonify({
            'success': True,
            'message': f'Retrieved {len(files)} {file_type} files',
            'data': {
                'files': files,
                'file_type': file_type,
                'count': len(files)
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to list Drive files: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to list files',
            'error_code': 'LIST_FILES_ERROR',
            'message': str(e)
        }), 500


# Health check endpoint for session-based services
@session_analysis_bp.route('/health', methods=['GET'])
def session_health():
    """
    Health check for session-based analysis services.
    
    Returns:
        JSON response with service status
    """
    try:
        # Get active sessions count
        active_sessions = session_aware_vector_service.list_user_active_sessions()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'data': {
                'active_sessions': len(active_sessions),
                'session_service': 'available',
                'timestamp': time.time()
            }
        })
        
    except Exception as e:
        logger.error(f"Session health check failed: {str(e)}", exception=e)
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': time.time()
        }), 500