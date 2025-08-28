"""
Session-Aware Vector Search Service

Integrates session-based vector database management with high-level search capabilities.
Provides multi-tenant vector operations with user isolation and Google Drive persistence.

This service acts as a bridge between the session vector service and the existing
vector search service, enabling user-specific vector databases with advanced search features.
"""

from typing import Dict, List, Any, Optional
from google.oauth2.credentials import Credentials

from .session_vector_service import session_vector_service, SessionVectorService
from .vector_service import VectorSearchService, SearchQuery, SearchResponse, RankedResult
from ..integrations.google.drive_service import GoogleDriveService
from ..integrations.google.oauth_service import GoogleOAuthService
from ..models import User, get_db_session
from ..models.document import DocumentType, DocumentCategory
import backend.models.base as models_base
from ..utils import logger
from ..config.settings import settings


class SessionAwareVectorService:
    """
    Session-aware vector search service with multi-tenant support.
    
    Manages user-specific vector databases with automatic session management,
    Google Drive persistence, and advanced search capabilities.
    """
    
    def __init__(self):
        """Initialize the session-aware vector service."""
        self.session_vector_service = session_vector_service
        self.oauth_service = GoogleOAuthService()
        
        logger.info("Session-aware vector service initialized")
    
    def initialize_user_session(self, user_id: str, session_id: str) -> bool:
        """
        Initialize a vector database session for a user.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            bool: True if session initialized successfully
        """
        try:
            # Get user's Google Drive credentials
            drive_service = self._get_user_drive_service(user_id)
            if not drive_service:
                logger.error(f"Could not get Drive service for user {user_id}")
                return False
            
            # Initialize session with the session vector service
            success = self.session_vector_service.initialize_user_session(
                user_id, session_id, drive_service
            )
            
            if success:
                logger.info(f"Initialized session-aware vector session for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize session for user {user_id}: {str(e)}", exception=e)
            return False
    
    def search_user_documents(self, user_id: str, session_id: str, query_text: str, 
                            top_k: int = 10, document_types: Optional[List[DocumentType]] = None,
                            document_categories: Optional[List[DocumentCategory]] = None, 
                            **search_kwargs) -> Optional[SearchResponse]:
        """
        Search documents in a user's vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query_text: Search query text
            top_k: Number of results to return
            document_types: Filter by document types
            document_categories: Filter by document categories
            **search_kwargs: Additional search parameters
            
        Returns:
            SearchResponse with user-specific results or None if session not found
        """
        try:
            # Get user's vector database
            user_vector_db = self.session_vector_service.get_user_vector_db(user_id, session_id)
            if not user_vector_db:
                logger.warning(f"No active vector session for user {user_id}, session {session_id}")
                return None
            
            # Create a vector search service for this user's database
            search_service = VectorSearchService(vector_db=user_vector_db)
            
            # Add document type filters to search kwargs
            if document_types or document_categories:
                type_filters = {}
                if document_types:
                    type_filters['document_type'] = [dt.value for dt in document_types]
                if document_categories:
                    type_filters['document_category'] = [dc.value for dc in document_categories]
                
                # Merge with existing filters
                existing_filters = search_kwargs.get('filters', {})
                search_kwargs['filters'] = {**existing_filters, **type_filters}
            
            # Perform search
            search_response = search_service.search(
                query_text=query_text,
                top_k=top_k,
                **search_kwargs
            )
            
            logger.info(f"Performed search for user {user_id}: {len(search_response.results)} results")
            return search_response
            
        except Exception as e:
            logger.error(f"Failed to search for user {user_id}: {str(e)}", exception=e)
            return None
    
    def search_ground_truth_documents(self, user_id: str, session_id: str, query_text: str,
                                    top_k: int = 10, categories: Optional[List[DocumentCategory]] = None,
                                    **search_kwargs) -> Optional[SearchResponse]:
        """
        Search only ground truth documents in a user's vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query_text: Search query text
            top_k: Number of results to return
            categories: Specific ground truth categories to search
            **search_kwargs: Additional search parameters
            
        Returns:
            SearchResponse with ground truth results or None if session not found
        """
        return self.search_user_documents(
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            top_k=top_k,
            document_types=[DocumentType.GROUND_TRUTH],
            document_categories=categories,
            **search_kwargs
        )
    
    def search_protocol_documents(self, user_id: str, session_id: str, query_text: str,
                                top_k: int = 10, categories: Optional[List[DocumentCategory]] = None,
                                **search_kwargs) -> Optional[SearchResponse]:
        """
        Search only protocol documents in a user's vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query_text: Search query text
            top_k: Number of results to return
            categories: Specific protocol categories to search
            **search_kwargs: Additional search parameters
            
        Returns:
            SearchResponse with protocol results or None if session not found
        """
        return self.search_user_documents(
            user_id=user_id,
            session_id=session_id,
            query_text=query_text,
            top_k=top_k,
            document_types=[DocumentType.PROTOCOL],
            document_categories=categories,
            **search_kwargs
        )
    
    def add_documents_to_user_session(self, user_id: str, session_id: str, 
                                    documents: List[Dict[str, Any]], 
                                    document_type: DocumentType = DocumentType.PROTOCOL,
                                    document_category: DocumentCategory = DocumentCategory.OTHER) -> bool:
        """
        Add documents to a user's vector database session with type classification.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            documents: List of document data with 'content', 'metadata', etc.
            document_type: Type of documents being added
            document_category: Category of documents being added
            
        Returns:
            bool: True if documents added successfully
        """
        try:
            # Enrich documents with type information
            enriched_documents = []
            for doc in documents:
                enriched_doc = dict(doc)
                
                # Add document type and category to metadata
                if 'metadata' not in enriched_doc:
                    enriched_doc['metadata'] = {}
                
                enriched_doc['metadata']['document_type'] = document_type.value
                enriched_doc['metadata']['document_category'] = document_category.value
                enriched_doc['metadata']['document_type_display'] = document_type.name.replace('_', ' ').title()
                enriched_doc['metadata']['document_category_display'] = document_category.name.replace('_', ' ').title()
                
                enriched_documents.append(enriched_doc)
            
            # Also upload documents to Google Drive with type-based organization
            drive_service = self._get_user_drive_service(user_id)
            if drive_service:
                for doc in enriched_documents:
                    if 'file_path' in doc:
                        # Upload document file to Drive with type-based folder organization
                        drive_file_id = drive_service.upload_document(
                            doc['file_path'], 
                            doc.get('filename', f"document_{doc.get('id', 'unknown')}.txt"),
                            doc.get('metadata', {}),
                            folder_type=document_type.value  # Organize by document type
                        )
                        
                        # Store Drive file ID in document metadata
                        doc['metadata']['drive_file_id'] = drive_file_id
            
            # Add to session vector database
            success = self.session_vector_service.add_documents_to_session(
                user_id, session_id, enriched_documents
            )
            
            if success:
                # Trigger backup to Drive
                self.backup_user_session(user_id, session_id)
                logger.info(f"Added {len(enriched_documents)} {document_type.value} documents to user {user_id} session")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add documents for user {user_id}: {str(e)}", exception=e)
            return False
    
    def backup_user_session(self, user_id: str, session_id: str, force: bool = False) -> bool:
        """
        Backup a user's vector database session to Google Drive.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            force: Force backup even if not needed
            
        Returns:
            bool: True if backup successful
        """
        try:
            success = self.session_vector_service.backup_session_to_drive(
                user_id, session_id, force
            )
            
            if success:
                logger.info(f"Backed up session for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to backup session for user {user_id}: {str(e)}", exception=e)
            return False
    
    def cleanup_user_session(self, user_id: str, session_id: str, backup_first: bool = True) -> bool:
        """
        Clean up a user's vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            backup_first: Whether to backup before cleanup
            
        Returns:
            bool: True if cleanup successful
        """
        try:
            success = self.session_vector_service.cleanup_session(
                user_id, session_id, backup_first
            )
            
            if success:
                logger.info(f"Cleaned up session for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to cleanup session for user {user_id}: {str(e)}", exception=e)
            return False
    
    def get_user_session_stats(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a user's vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dict with session statistics or None
        """
        try:
            stats = self.session_vector_service.get_session_stats(user_id, session_id)
            
            if stats:
                # Add Drive-specific stats
                drive_service = self._get_user_drive_service(user_id)
                if drive_service:
                    drive_files = drive_service.list_user_files_by_type('vector_database')
                    stats['drive_backups'] = len(drive_files)
                    stats['drive_files'] = len(drive_service.list_user_files_by_type('document'))
                
                # Add document type statistics
                doc_type_stats = self.get_user_document_type_stats(user_id, session_id)
                if doc_type_stats:
                    stats['document_types'] = doc_type_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session stats for user {user_id}: {str(e)}", exception=e)
            return None
    
    def get_user_document_type_stats(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document type statistics for a user's session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dict with document type statistics or None
        """
        try:
            # Get user's vector database
            user_vector_db = self.session_vector_service.get_user_vector_db(user_id, session_id)
            if not user_vector_db:
                return None
            
            # Get all documents and analyze their types
            all_metadata = user_vector_db.get_all_metadata() if hasattr(user_vector_db, 'get_all_metadata') else []
            
            type_counts = {}
            category_counts = {}
            
            for metadata in all_metadata:
                doc_type = metadata.get('document_type', 'unknown')
                doc_category = metadata.get('document_category', 'unknown')
                
                type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                category_counts[doc_category] = category_counts.get(doc_category, 0) + 1
            
            return {
                'total_documents': len(all_metadata),
                'by_type': type_counts,
                'by_category': category_counts,
                'ground_truth_count': type_counts.get('ground_truth', 0),
                'protocol_count': type_counts.get('protocol', 0),
                'reference_count': type_counts.get('reference', 0),
                'analysis_result_count': type_counts.get('analysis_result', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get document type stats for user {user_id}: {str(e)}", exception=e)
            return None
    
    def list_user_active_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active vector database sessions across all users.
        
        Returns:
            List of session information dictionaries
        """
        try:
            return self.session_vector_service.list_active_sessions()
            
        except Exception as e:
            logger.error(f"Failed to list active sessions: {str(e)}", exception=e)
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions for all users.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            return self.session_vector_service.cleanup_expired_sessions()
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}", exception=e)
            return 0
    
    def get_user_drive_files(self, user_id: str, file_type: str = 'document') -> List[Dict[str, Any]]:
        """
        Get a user's files from Google Drive by type.
        
        Args:
            user_id: User identifier
            file_type: Type of files to list
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            drive_service = self._get_user_drive_service(user_id)
            if not drive_service:
                return []
            
            files = drive_service.list_user_files_by_type(file_type)
            logger.info(f"Retrieved {len(files)} {file_type} files for user {user_id}")
            return files
            
        except Exception as e:
            logger.error(f"Failed to get Drive files for user {user_id}: {str(e)}", exception=e)
            return []
    
    def save_user_chat_history(self, user_id: str, session_id: str, chat_data: Dict[str, Any]) -> bool:
        """
        Save chat history to user's Google Drive.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            chat_data: Chat session data to save
            
        Returns:
            bool: True if save successful
        """
        try:
            drive_service = self._get_user_drive_service(user_id)
            if not drive_service:
                return False
            
            file_id = drive_service.save_chat_history(session_id, chat_data)
            
            if file_id:
                logger.info(f"Saved chat history for user {user_id} to Drive")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to save chat history for user {user_id}: {str(e)}", exception=e)
            return False
    
    def load_user_chat_history(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load chat history from user's Google Drive.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dict with chat history or None if not found
        """
        try:
            drive_service = self._get_user_drive_service(user_id)
            if not drive_service:
                return None
            
            chat_data = drive_service.load_chat_history(session_id)
            
            if chat_data:
                logger.info(f"Loaded chat history for user {user_id} from Drive")
            
            return chat_data
            
        except Exception as e:
            logger.error(f"Failed to load chat history for user {user_id}: {str(e)}", exception=e)
            return None
    
    def _get_user_drive_service(self, user_id: str) -> Optional[GoogleDriveService]:
        """
        Get Google Drive service for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            GoogleDriveService instance or None if not available
        """
        try:
            if not models_base.db_config:
                logger.warning("Database not available for Drive service")
                return None
            
            db_session = models_base.db_config.get_session()
            
            try:
                # Get user from database
                user = db_session.query(User).filter_by(id=user_id).first()
                if not user:
                    logger.warning(f"User {user_id} not found")
                    return None
                
                # Check if user has Drive tokens
                if not user.drive_access_token or not user.drive_refresh_token:
                    logger.warning(f"User {user_id} has no Drive tokens")
                    return None
                
                # Decrypt tokens and create credentials
                decrypted_access_token = user.decrypt_drive_access_token()
                decrypted_refresh_token = user.decrypt_drive_refresh_token()
                
                if not decrypted_access_token or not decrypted_refresh_token:
                    logger.warning(f"Failed to decrypt Drive tokens for user {user_id}")
                    return None
                
                # Create Google credentials
                credentials = Credentials(
                    token=decrypted_access_token,
                    refresh_token=decrypted_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.auth.google_client_id,
                    client_secret=settings.auth.google_client_secret
                )
                
                # Create and return Drive service
                drive_service = GoogleDriveService(credentials)
                
                # Setup folder structure if needed
                drive_service.setup_folder_structure()
                
                return drive_service
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to get Drive service for user {user_id}: {str(e)}", exception=e)
            return None
    
    async def start_background_tasks(self):
        """Start background tasks for session management."""
        try:
            # Start the session cleanup task
            await self.session_vector_service.start_cleanup_task()
            
        except Exception as e:
            logger.error(f"Failed to start background tasks: {str(e)}", exception=e)


# Global session-aware vector service instance
session_aware_vector_service = SessionAwareVectorService()