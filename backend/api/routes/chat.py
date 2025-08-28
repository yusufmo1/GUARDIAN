"""
Chat API Routes

Multi-tenant chat endpoints for the GUARDIAN system with Google Drive persistence.

Endpoints:
- POST /api/chat/send - Send a message and get AI response
- GET /api/chat/sessions - List user's chat sessions
- GET /api/chat/sessions/{session_id} - Get specific session with messages
- POST /api/chat/sessions - Create new chat session
- DELETE /api/chat/sessions/{session_id} - Delete chat session
- GET /api/chat/history/{session_id} - Get chat history from Drive
"""

from flask import Blueprint, request, jsonify, g
from pydantic import BaseModel, ValidationError
from typing import Optional
from datetime import datetime

from ...models import get_db_session, db_config
from ...services.chat_service import ChatService, ChatError
from ...api.middleware.auth_middleware import require_authentication
from ...api.middleware.rate_limit_middleware import rate_limit
from ...utils import logger

# Create blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')


# Pydantic models for request validation
class SendMessageRequest(BaseModel):
    session_id: str
    message: str
    search_context: Optional[bool] = True


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


@chat_bp.route('/send', methods=['POST'])
@require_authentication
@rate_limit('default')
def send_message():
    """
    Send a message in a chat session and get AI response.
    
    Request body:
        {
            "session_id": "uuid",
            "message": "User's message",
            "search_context": true  // Optional, default true
        }
    
    Returns:
        JSON response with user message and AI response
    """
    try:
        # Validate request
        try:
            request_data = SendMessageRequest(**request.get_json())
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': e.errors()
            }), 400
        
        # Get user context
        user = g.current_user
        user_id = str(user['id'])
        
        # Get database session
        if not db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = db_config.get_session()
        
        try:
            chat_service = ChatService(db_session)
            
            # Send message and get response
            response_data = chat_service.send_message(
                user_id=user_id,
                session_id=request_data.session_id,
                message=request_data.message,
                search_context=request_data.search_context
            )
            
            logger.info(f"Chat message processed for user {user_id}")
            
            return jsonify({
                'success': True,
                'data': response_data,
                'message': 'Message processed successfully'
            })
            
        finally:
            db_session.close()
            
    except ChatError as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({
            'error': 'Chat processing failed',
            'error_code': 'CHAT_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in chat: {str(e)}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'message': 'Failed to process chat message'
        }), 500


@chat_bp.route('/sessions', methods=['GET'])
@require_authentication
def list_chat_sessions():
    """
    List all chat sessions for the current user.
    
    Returns:
        JSON response with list of chat sessions
    """
    try:
        # Get user context
        user = g.current_user
        user_id = str(user['id'])
        
        # Get database session
        if not db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = db_config.get_session()
        
        try:
            chat_service = ChatService(db_session)
            sessions = chat_service.list_user_sessions(user_id)
            
            return jsonify({
                'success': True,
                'data': {
                    'sessions': sessions,
                    'total': len(sessions)
                },
                'message': 'Sessions retrieved successfully'
            })
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Failed to list chat sessions: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to list sessions',
            'error_code': 'LIST_ERROR',
            'message': 'Could not retrieve chat sessions'
        }), 500


@chat_bp.route('/sessions/<session_id>', methods=['GET'])
@require_authentication
def get_chat_session(session_id: str):
    """
    Get a specific chat session with messages.
    
    Args:
        session_id: Chat session identifier
        
    Query params:
        include_messages: Whether to include message history (default true)
    
    Returns:
        JSON response with session details and messages
    """
    try:
        # Get user context
        user = g.current_user
        user_id = str(user['id'])
        
        # Get query params
        include_messages = request.args.get('include_messages', 'true').lower() == 'true'
        
        # Get database session
        if not db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = db_config.get_session()
        
        try:
            chat_service = ChatService(db_session)
            session_data = chat_service.get_chat_session(
                user_id=user_id,
                session_id=session_id,
                include_messages=include_messages
            )
            
            return jsonify({
                'success': True,
                'data': session_data,
                'message': 'Session retrieved successfully'
            })
            
        finally:
            db_session.close()
            
    except ChatError as e:
        logger.error(f"Chat session error: {str(e)}")
        return jsonify({
            'error': 'Session not found',
            'error_code': 'NOT_FOUND',
            'message': str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to get chat session: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to get session',
            'error_code': 'GET_ERROR',
            'message': 'Could not retrieve chat session'
        }), 500


@chat_bp.route('/sessions', methods=['POST'])
@require_authentication
def create_chat_session():
    """
    Create a new chat session.
    
    Request body:
        {
            "title": "Optional session title"
        }
    
    Returns:
        JSON response with new session details
    """
    try:
        # Validate request
        try:
            request_data = CreateSessionRequest(**request.get_json() or {})
        except ValidationError as e:
            return jsonify({
                'error': 'Invalid request data',
                'error_code': 'VALIDATION_ERROR',
                'details': e.errors()
            }), 400
        
        # Get user context
        user = g.current_user
        user_id = str(user['id'])
        
        # Get database session
        if not db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = db_config.get_session()
        
        try:
            chat_service = ChatService(db_session)
            session = chat_service.create_chat_session(
                user_id=user_id,
                session_title=request_data.title
            )
            
            logger.info(f"Created chat session for user {user_id}")
            
            return jsonify({
                'success': True,
                'data': session,
                'message': 'Chat session created successfully'
            })
            
        finally:
            db_session.close()
            
    except ChatError as e:
        logger.error(f"Failed to create chat session: {str(e)}")
        return jsonify({
            'error': 'Session creation failed',
            'error_code': 'CREATE_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error creating session: {str(e)}", exception=e)
        return jsonify({
            'error': 'Internal server error',
            'error_code': 'INTERNAL_ERROR',
            'message': 'Failed to create chat session'
        }), 500


@chat_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_authentication
def delete_chat_session(session_id: str):
    """
    Delete a chat session.
    
    Args:
        session_id: Chat session identifier
        
    Returns:
        JSON response confirming deletion
    """
    try:
        # Get user context
        user = g.current_user
        user_id = str(user['id'])
        
        # Get database session
        if not db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = db_config.get_session()
        
        try:
            chat_service = ChatService(db_session)
            success = chat_service.delete_chat_session(
                user_id=user_id,
                session_id=session_id
            )
            
            if success:
                logger.info(f"Deleted chat session {session_id} for user {user_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Chat session deleted successfully'
                })
            else:
                return jsonify({
                    'error': 'Deletion failed',
                    'error_code': 'DELETE_ERROR',
                    'message': 'Could not delete chat session'
                }), 400
                
        finally:
            db_session.close()
            
    except ChatError as e:
        logger.error(f"Chat deletion error: {str(e)}")
        return jsonify({
            'error': 'Session not found',
            'error_code': 'NOT_FOUND',
            'message': str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Failed to delete chat session: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to delete session',
            'error_code': 'DELETE_ERROR',
            'message': 'Could not delete chat session'
        }), 500


@chat_bp.route('/history/<session_id>', methods=['GET'])
@require_authentication
def get_chat_history(session_id: str):
    """
    Get chat history from Google Drive.
    
    Args:
        session_id: Chat session identifier
        
    Returns:
        JSON response with chat history from Drive
    """
    try:
        # Get user context
        user = g.current_user
        user_id = str(user['id'])
        
        # Get database session
        if not db_config:
            return jsonify({
                'error': 'Database not available',
                'error_code': 'DATABASE_ERROR'
            }), 500
        
        db_session = db_config.get_session()
        
        try:
            # Get Drive service
            from ...services.auth.auth_service import AuthService
            auth_service = AuthService(db_session)
            drive_service = auth_service.get_drive_service(user_id)
            
            if not drive_service:
                return jsonify({
                    'error': 'Drive service unavailable',
                    'error_code': 'DRIVE_ERROR',
                    'message': 'Could not access Google Drive'
                }), 503
            
            # Load chat history
            chat_data = drive_service.load_chat_history(session_id)
            
            if chat_data:
                return jsonify({
                    'success': True,
                    'data': chat_data,
                    'message': 'Chat history loaded from Drive'
                })
            else:
                return jsonify({
                    'error': 'History not found',
                    'error_code': 'NOT_FOUND',
                    'message': 'No chat history found in Drive'
                }), 404
                
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Failed to get chat history from Drive: {str(e)}", exception=e)
        return jsonify({
            'error': 'Failed to get history',
            'error_code': 'HISTORY_ERROR',
            'message': 'Could not retrieve chat history from Drive'
        }), 500


# Health check endpoint for chat system
@chat_bp.route('/health', methods=['GET'])
def chat_health():
    """
    Health check for chat system.
    
    Returns:
        JSON response with chat system status
    """
    try:
        # Check database connection
        db_available = bool(db_config)
        
        # Check if we can create chat service
        chat_service_available = False
        if db_available:
            try:
                db_session = db_config.get_session()
                chat_service = ChatService(db_session)
                chat_service_available = True
                db_session.close()
            except Exception:
                pass
        
        status = 'healthy' if db_available and chat_service_available else 'unhealthy'
        
        return jsonify({
            'success': True,
            'status': status,
            'components': {
                'database': 'available' if db_available else 'unavailable',
                'chat_service': 'available' if chat_service_available else 'unavailable'
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat health check error: {str(e)}", exception=e)
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500