"""
Chat Service

Multi-tenant chat service with Google Drive persistence for the GUARDIAN system.
Integrates with vector databases for context-aware pharmaceutical compliance conversations.

Features:
- Session-based chat management
- Google Drive persistence for chat history
- Context search from user's vector database
- LLM integration for compliance-focused responses
- Complete user isolation
"""

import uuid
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..models import ChatSession, ChatMessage, User
from ..integrations.google import GoogleDriveService
from ..integrations.llm import LLMClient
from ..services.session_aware_vector_service import session_aware_vector_service
from ..utils import logger
from ..config.settings import settings


class ChatError(Exception):
    """Base exception for chat service errors."""
    pass


class ChatService:
    """
    Multi-tenant chat service with Drive persistence.
    
    Manages pharmaceutical compliance chat sessions with:
    - Complete user isolation
    - Google Drive persistence
    - Context-aware responses
    - Session management
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize chat service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.llm_client = LLMClient()
        
        logger.info("Chat service initialized")
    
    def create_chat_session(self, user_id: str, session_title: str = None) -> Dict[str, Any]:
        """
        Create a new chat session for a user.
        
        Args:
            user_id: User identifier
            session_title: Optional session title
            
        Returns:
            Dict with session information
        """
        try:
            # Create database record
            chat_session = ChatSession(
                user_id=user_id,
                title=session_title or f"Chat Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
                metadata={}
            )
            
            self.db.add(chat_session)
            self.db.commit()
            
            session_dict = chat_session.to_dict()
            
            logger.info(f"Created chat session {chat_session.id} for user {user_id}")
            
            return session_dict
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create chat session: {str(e)}", exception=e)
            raise ChatError(f"Failed to create chat session: {str(e)}")
    
    def send_message(self, user_id: str, session_id: str, message: str, 
                     search_context: bool = True) -> Dict[str, Any]:
        """
        Send a message in a chat session and get AI response.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            message: User's message
            search_context: Whether to search vector DB for context
            
        Returns:
            Dict with user message and AI response
        """
        try:
            # Verify session belongs to user
            chat_session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not chat_session:
                raise ChatError("Chat session not found or access denied")
            
            # Create user message
            user_message = ChatMessage(
                chat_session_id=session_id,
                role='user',
                content=message,
                metadata={}
            )
            self.db.add(user_message)
            self.db.flush()
            
            # Load chat history from Drive
            chat_history = self._load_chat_history(user_id, session_id)
            
            # Search for relevant context if requested
            context_chunks = []
            if search_context:
                try:
                    # Search user's vector database for relevant information
                    search_results = session_aware_vector_service.search_documents(
                        user_id=user_id,
                        session_id=session_id,  # Use auth session ID
                        query=message,
                        top_k=5
                    )
                    
                    if search_results and search_results.results:
                        context_chunks = [
                            {
                                'text': result.text,
                                'source': result.metadata.get('source', 'Unknown'),
                                'section': result.metadata.get('section', 'Unknown')
                            }
                            for result in search_results.results
                        ]
                        logger.info(f"Found {len(context_chunks)} relevant context chunks")
                        
                except Exception as e:
                    logger.warning(f"Context search failed: {str(e)}")
                    # Continue without context
            
            # Build prompt with context and history
            prompt = self._build_contextual_prompt(
                message=message,
                chat_history=chat_history,
                context_chunks=context_chunks
            )
            
            # Get AI response
            start_time = time.time()
            ai_response = self.llm_client.generate_response(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000
            )
            response_time = time.time() - start_time
            
            # Create AI message
            ai_message = ChatMessage(
                chat_session_id=session_id,
                role='assistant',
                content=ai_response,
                metadata={
                    'response_time': response_time,
                    'context_used': len(context_chunks) > 0,
                    'context_chunks': len(context_chunks)
                }
            )
            self.db.add(ai_message)
            
            # Update session activity
            chat_session.last_message_at = datetime.utcnow()
            chat_session.message_count = chat_session.message_count + 2  # User + AI
            
            self.db.commit()
            
            # Save updated chat history to Drive
            self._save_chat_history_to_drive(user_id, session_id)
            
            response_data = {
                'user_message': user_message.to_dict(),
                'ai_response': ai_message.to_dict(),
                'context_used': context_chunks,
                'response_time': response_time
            }
            
            logger.info(f"Chat message processed for session {session_id}")
            
            return response_data
            
        except ChatError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process chat message: {str(e)}", exception=e)
            raise ChatError(f"Failed to process message: {str(e)}")
    
    def get_chat_session(self, user_id: str, session_id: str, 
                        include_messages: bool = True) -> Dict[str, Any]:
        """
        Get a chat session with optional message history.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            include_messages: Whether to include message history
            
        Returns:
            Dict with session and optionally messages
        """
        try:
            # Get session from database
            chat_session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).first()
            
            if not chat_session:
                raise ChatError("Chat session not found or access denied")
            
            session_dict = chat_session.to_dict()
            
            if include_messages:
                # Load messages from Drive if available
                drive_history = self._load_chat_history(user_id, session_id)
                
                if drive_history and 'messages' in drive_history:
                    session_dict['messages'] = drive_history['messages']
                else:
                    # Fallback to database messages
                    messages = self.db.query(ChatMessage).filter(
                        ChatMessage.chat_session_id == session_id
                    ).order_by(ChatMessage.created_at).all()
                    
                    session_dict['messages'] = [msg.to_dict() for msg in messages]
            
            return session_dict
            
        except ChatError:
            raise
        except Exception as e:
            logger.error(f"Failed to get chat session: {str(e)}", exception=e)
            raise ChatError(f"Failed to get chat session: {str(e)}")
    
    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all chat sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of chat session dictionaries
        """
        try:
            sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id
            ).order_by(ChatSession.last_message_at.desc()).all()
            
            return [session.to_dict() for session in sessions]
            
        except Exception as e:
            logger.error(f"Failed to list chat sessions: {str(e)}", exception=e)
            raise ChatError(f"Failed to list sessions: {str(e)}")
    
    def delete_chat_session(self, user_id: str, session_id: str) -> bool:
        """
        Delete a chat session.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Verify ownership and delete
            result = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            ).delete()
            
            if result == 0:
                raise ChatError("Chat session not found or access denied")
            
            self.db.commit()
            
            logger.info(f"Deleted chat session {session_id} for user {user_id}")
            
            return True
            
        except ChatError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete chat session: {str(e)}", exception=e)
            raise ChatError(f"Failed to delete session: {str(e)}")
    
    def _load_chat_history(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load chat history from Google Drive.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            Dict with chat history or None
        """
        try:
            # Get Drive service for user
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Import here to avoid circular imports
            from ..services.auth.auth_service import AuthService
            auth_service = AuthService(self.db)
            drive_service = auth_service.get_drive_service(user_id)
            
            if drive_service:
                return drive_service.load_chat_history(session_id)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to load chat history from Drive: {str(e)}")
            return None
    
    def _save_chat_history_to_drive(self, user_id: str, session_id: str) -> Optional[str]:
        """
        Save chat history to Google Drive.
        
        Args:
            user_id: User identifier
            session_id: Chat session identifier
            
        Returns:
            Drive file ID or None
        """
        try:
            # Get all messages for session
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.chat_session_id == session_id
            ).order_by(ChatMessage.created_at).all()
            
            # Get session info
            chat_session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id
            ).first()
            
            if not chat_session:
                return None
            
            # Prepare chat data
            chat_data = {
                'session_id': str(session_id),
                'user_id': str(user_id),
                'title': chat_session.title,
                'created_at': chat_session.created_at.isoformat(),
                'last_message_at': chat_session.last_message_at.isoformat() if chat_session.last_message_at else None,
                'message_count': len(messages),
                'messages': [
                    {
                        'id': str(msg.id),
                        'role': msg.role,
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat(),
                        'metadata': msg.metadata
                    }
                    for msg in messages
                ]
            }
            
            # Get Drive service
            from ..services.auth.auth_service import AuthService
            auth_service = AuthService(self.db)
            drive_service = auth_service.get_drive_service(user_id)
            
            if drive_service:
                # Update Drive backup ID in session
                drive_file_id = drive_service.save_chat_history(session_id, chat_data)
                chat_session.drive_backup_id = drive_file_id
                self.db.commit()
                
                return drive_file_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to save chat history to Drive: {str(e)}", exception=e)
            return None
    
    def _build_contextual_prompt(self, message: str, chat_history: Optional[Dict[str, Any]], 
                                context_chunks: List[Dict[str, Any]]) -> str:
        """
        Build a contextual prompt for the LLM.
        
        Args:
            message: User's message
            chat_history: Previous chat history
            context_chunks: Relevant context from vector DB
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # System prompt
        prompt_parts.append(
            "You are a pharmaceutical compliance expert AI assistant for the GUARDIAN system. "
            "You help users understand and ensure compliance with European Pharmacopoeia standards. "
            "Provide accurate, helpful, and compliance-focused responses."
        )
        
        # Add context if available
        if context_chunks:
            prompt_parts.append("\nRelevant compliance information from the knowledge base:")
            for chunk in context_chunks[:3]:  # Limit to top 3 chunks
                prompt_parts.append(f"\n- From {chunk['source']} ({chunk['section']}): {chunk['text'][:500]}...")
        
        # Add recent chat history
        if chat_history and 'messages' in chat_history:
            recent_messages = chat_history['messages'][-6:]  # Last 3 exchanges
            if recent_messages:
                prompt_parts.append("\nRecent conversation:")
                for msg in recent_messages:
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    prompt_parts.append(f"\n{role}: {msg['content']}")
        
        # Add current message
        prompt_parts.append(f"\nUser: {message}")
        prompt_parts.append("\nAssistant:")
        
        return "\n".join(prompt_parts)