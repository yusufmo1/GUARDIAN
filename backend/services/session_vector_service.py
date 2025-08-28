"""
Session-Based Vector Database Service

Manages user-specific vector databases with automatic loading from Google Drive,
session cleanup, and persistence back to Drive storage.

This service enables multi-tenant vector database management where each user
has their own isolated vector database that is loaded on-demand and cleaned up
automatically when sessions expire.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os
import shutil
import tempfile
import zipfile
import uuid
import asyncio
from threading import Lock

from ..models import VectorSession, get_db_session, db_config
from ..core.ml.vector_db import VectorDatabase
from ..core.ml.embedding_model import EmbeddingModelHandler
from ..integrations.google.drive_service import GoogleDriveService
from ..integrations.google.oauth_service import GoogleOAuthService
from ..utils import logger
from ..config.settings import settings


class SessionVectorService:
    """
    Session-based vector database management service.
    
    Handles the lifecycle of user-specific vector databases:
    1. Load VDB from Google Drive when user starts session
    2. Maintain VDB in memory during active session
    3. Persist VDB back to Drive periodically and on session end
    4. Clean up expired sessions and release memory
    """
    
    def __init__(self):
        """Initialize the session vector service."""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_lock = Lock()
        self.embedding_model = EmbeddingModelHandler()
        self.cleanup_interval = 300  # 5 minutes cleanup interval
        self.session_timeout = settings.auth.session_duration_hours * 3600  # Convert to seconds
        
        logger.info("Session Vector Service initialized")
    
    def initialize_user_session(self, user_id: str, session_id: str, drive_service: GoogleDriveService) -> bool:
        """
        Initialize a vector database session for a user.
        
        Args:
            user_id: User identifier
            session_id: Session identifier 
            drive_service: User's Google Drive service instance
            
        Returns:
            bool: True if session initialized successfully
        """
        try:
            # Import required modules
            import tempfile
            import zipfile
            
            with self.session_lock:
                session_key = f"{user_id}_{session_id}"
                
                if session_key in self.active_sessions:
                    logger.info(f"Session {session_key} already active")
                    return True
                
                # Create temporary directory for this session's VDB
                temp_dir = tempfile.mkdtemp(prefix=f"guardian_vdb_{session_key}_")
                vdb_path = os.path.join(temp_dir, "session")
                
                # Try to restore VDB from Google Drive
                # The backup is now a ZIP file, so download it and extract
                
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_temp:
                    zip_download_path = zip_temp.name
                
                vdb_restored = False
                try:
                    # Try to download backup from Drive (could be ZIP or old format)
                    if drive_service.restore_vector_database(session_id, zip_download_path):
                        # Check if it's a ZIP file or old format
                        try:
                            # Try to extract as ZIP (new format)
                            with zipfile.ZipFile(zip_download_path, 'r') as zipf:
                                zipf.extractall(temp_dir)
                            vdb_restored = True
                            logger.info(f"Extracted VDB backup (ZIP format) for session {session_key}")
                        except zipfile.BadZipFile:
                            # It's the old format - just a FAISS index file
                            # Move it to the correct location
                            old_index_path = vdb_path + ".index"
                            import shutil
                            shutil.move(zip_download_path, old_index_path)
                            vdb_restored = True
                            logger.info(f"Restored VDB backup (legacy format) for session {session_key}")
                    else:
                        logger.info(f"No VDB backup found for session {session_key}")
                except Exception as e:
                    logger.error(f"Failed to restore VDB backup: {str(e)}", exception=e)
                    vdb_restored = False
                finally:
                    # Clean up the temporary download file if it still exists
                    if os.path.exists(zip_download_path):
                        os.unlink(zip_download_path)
                
                # Initialize vector database
                vector_db = VectorDatabase(storage_dir=temp_dir)
                
                if vdb_restored and os.path.exists(vdb_path + ".index"):
                    try:
                        # Check if we have all required files for loading
                        metadata_path = vdb_path + "_metadata.json"
                        chunks_path = vdb_path + "_chunks.pkl"
                        
                        if os.path.exists(metadata_path) and os.path.exists(chunks_path):
                            # We have all files - load normally
                            vector_db.load_index("session")
                            logger.info(f"Restored complete VDB for session {session_key} from Drive")
                        else:
                            # We have only the index file (legacy format) - create minimal metadata and empty chunks
                            logger.info(f"Legacy VDB format detected for session {session_key} - creating minimal metadata")
                            
                            # Load just the FAISS index to get its properties
                            import faiss
                            index = faiss.read_index(vdb_path + ".index")
                            
                            # Create minimal metadata
                            metadata = {
                                'index_type': 'IndexFlatIP',
                                'dimension': index.d,
                                'num_vectors': index.ntotal,
                                'similarity_threshold': 0.7,
                                'metadata': {}
                            }
                            
                            with open(metadata_path, 'w') as f:
                                import json
                                json.dump(metadata, f, indent=2)
                            
                            # Create empty chunks file
                            with open(chunks_path, 'wb') as f:
                                import pickle
                                pickle.dump([], f)
                            
                            # Now try to load the index
                            vector_db.load_index("session")
                            logger.info(f"Restored legacy VDB for session {session_key} with reconstructed metadata")
                            
                    except Exception as e:
                        logger.error(f"Failed to load restored VDB: {str(e)}", exception=e)
                        # Fall back to creating a new empty VDB
                        vdb_restored = False
                else:
                    # Create new empty VDB by building with empty arrays
                    import numpy as np
                    dimension = self.embedding_model.get_embedding_dimension()
                    empty_embeddings = np.empty((0, dimension), dtype=np.float32)
                    empty_chunks = []
                    vector_db.build_index(empty_embeddings, empty_chunks)
                    logger.info(f"Created new empty VDB for session {session_key} with dimension {dimension}")
                
                # For restored sessions, estimate document count from existing vectors
                # Each document typically has multiple chunks, so this is an approximation
                vector_stats = vector_db.get_stats()
                estimated_doc_count = 0
                if vdb_restored and vector_stats.get('num_vectors', 0) > 0:
                    # Conservative estimate: assume 3-5 chunks per document on average
                    estimated_doc_count = max(1, vector_stats.get('num_vectors', 0) // 4)
                
                # Store session data
                session_data = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'vector_db': vector_db,
                    'drive_service': drive_service,
                    'temp_dir': temp_dir,
                    'vdb_path': vdb_path,
                    'last_activity': datetime.utcnow(),
                    'created_at': datetime.utcnow(),
                    'document_count': estimated_doc_count,  # For new sessions: 0, for restored sessions: estimated count
                    'needs_backup': False
                }
                
                self.active_sessions[session_key] = session_data
                
                # Update database record
                self._update_vector_session_record(user_id, session_id, 'active')
                
                logger.info(f"Initialized vector session for user {user_id}, session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize session for user {user_id}: {str(e)}", exception=e)
            return False
    
    def get_user_vector_db(self, user_id: str, session_id: str) -> Optional[VectorDatabase]:
        """
        Get the vector database for a user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            VectorDatabase instance or None if session not found
        """
        try:
            session_key = f"{user_id}_{session_id}"
            
            with self.session_lock:
                if session_key not in self.active_sessions:
                    logger.warning(f"No active vector session found for {session_key}")
                    return None
                
                session_data = self.active_sessions[session_key]
                
                # Update last activity
                session_data['last_activity'] = datetime.utcnow()
                
                return session_data['vector_db']
                
        except Exception as e:
            logger.error(f"Failed to get vector DB for user {user_id}: {str(e)}", exception=e)
            return None
    
    def add_documents_to_session(self, user_id: str, session_id: str, documents: List[Dict[str, Any]]) -> bool:
        """
        Add documents to a user's vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            documents: List of document data with 'chunks' containing DocumentChunk objects
            
        Returns:
            bool: True if documents added successfully
        """
        try:
            vector_db = self.get_user_vector_db(user_id, session_id)
            if not vector_db:
                return False
            
            session_key = f"{user_id}_{session_id}"
            
            # Get existing chunks and embeddings if any
            existing_chunks = []
            existing_embeddings = None
            
            if vector_db.is_ready():
                # Vector DB has existing data, we need to preserve it
                existing_chunks = vector_db._chunks
                # Get existing embeddings from the index
                if vector_db._index and vector_db._index.ntotal > 0:
                    import numpy as np
                    existing_embeddings = np.zeros((vector_db._index.ntotal, vector_db._dimension), dtype=np.float32)
                    vector_db._index.reconstruct_n(0, vector_db._index.ntotal, existing_embeddings)
            
            # Process new documents and extract chunks
            all_chunks = list(existing_chunks)  # Copy existing chunks
            new_texts = []
            docs_with_content = 0
            docs_without_content = 0
            
            for doc in documents:
                if 'chunks' in doc:
                    # Document already has chunks
                    doc_chunks = doc['chunks']
                    if doc_chunks:  # Only process if chunks exist
                        all_chunks.extend(doc_chunks)
                        new_texts.extend([chunk.text for chunk in doc_chunks])
                        docs_with_content += 1
                    else:
                        # Document has no extractable content but was still uploaded to Drive
                        docs_without_content += 1
                        logger.info(f"Document {doc.get('filename', 'unknown')} uploaded to Drive but has no extractable text - skipping vector processing")
                elif 'content' in doc:
                    # Document has raw content, need to chunk it
                    # This is a simplified version - in production you'd use document processor
                    from ..core.processors.document_processor import DocumentChunk, ChunkMetadata
                    chunk = DocumentChunk(
                        text=doc['content'],
                        metadata=ChunkMetadata(
                            section='Document',
                            section_title='Content',
                            page=1,
                            chunk_index=0,
                            char_count=len(doc['content']),
                            word_count=len(doc['content'].split())
                        )
                    )
                    all_chunks.append(chunk)
                    new_texts.append(chunk.text)
                    docs_with_content += 1
            
            # Only generate embeddings if we have new texts
            if new_texts:
                # Generate embeddings for new texts
                new_embeddings = self.embedding_model.generate_embeddings(new_texts)
            else:
                # No new content to process
                logger.info(f"No new texts to process - {docs_without_content} documents uploaded to Drive only")
                new_embeddings = None
            
            # Combine embeddings
            import numpy as np
            if new_embeddings is not None:
                if existing_embeddings is not None and len(existing_embeddings) > 0:
                    all_embeddings = np.vstack([existing_embeddings, new_embeddings])
                else:
                    all_embeddings = new_embeddings
                
                # Rebuild the index with all data
                vector_db.build_index(all_embeddings, all_chunks)
                
                # Clear temporary data from memory
                del new_embeddings
                if existing_embeddings is not None:
                    del existing_embeddings
            else:
                # No new embeddings to add, but we may still need to rebuild if chunks were added without content
                logger.info("No new embeddings generated - keeping existing vector database unchanged")
                all_embeddings = existing_embeddings
            
            # Clear temporary data from memory
            del new_texts
            
            # Update session metadata
            with self.session_lock:
                if session_key in self.active_sessions:
                    session_data = self.active_sessions[session_key]
                    # Increment document count by the number of documents with content
                    session_data['document_count'] = session_data.get('document_count', 0) + docs_with_content
                    session_data['last_activity'] = datetime.utcnow()
                    session_data['needs_backup'] = True
            
            logger.info(f"Added {len(documents)} documents to session {session_key}, total chunks: {len(all_chunks)}")
            
            # Force garbage collection for large document batches
            import gc
            gc.collect()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to session {user_id}_{session_id}: {str(e)}", exception=e)
            return False
    
    def search_user_vectors(self, user_id: str, session_id: str, query_text: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search vectors in a user's session database.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            query_text: Search query text
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        try:
            vector_db = self.get_user_vector_db(user_id, session_id)
            if not vector_db:
                return []
            
            # Generate query embedding
            query_embedding = self.embedding_model.generate_embeddings([query_text])[0]
            
            # Search vector database
            results = vector_db.search(query_embedding, top_k=top_k)
            
            logger.info(f"Vector search for user {user_id} returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search vectors for user {user_id}: {str(e)}", exception=e)
            return []
    
    def backup_session_to_drive(self, user_id: str, session_id: str, force: bool = False) -> bool:
        """
        Backup a session's vector database to Google Drive.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            force: Force backup even if not needed
            
        Returns:
            bool: True if backup successful
        """
        try:
            # Import required modules
            import zipfile
            import tempfile
            
            session_key = f"{user_id}_{session_id}"
            
            with self.session_lock:
                if session_key not in self.active_sessions:
                    logger.warning(f"No active session to backup: {session_key}")
                    return False
                
                session_data = self.active_sessions[session_key]
                
                if not force and not session_data.get('needs_backup', False):
                    logger.debug(f"Session {session_key} does not need backup")
                    return True
                
                vector_db = session_data['vector_db']
                vdb_path = session_data['vdb_path']
                drive_service = session_data['drive_service']
                
                # Save vector database to local file (save_index expects just the name without extension)
                vector_db.save_index("session")
                
                # Backup to Google Drive
                backup_metadata = {
                    'user_id': user_id,
                    'session_id': session_id,
                    'document_count': session_data['document_count'],
                    'created_at': session_data['created_at'].isoformat(),
                    'last_activity': session_data['last_activity'].isoformat()
                }
                
                # Create a ZIP file with all vector database files
                
                with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_temp:
                    zip_path = zip_temp.name
                
                try:
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        # Add the three vector database files to the ZIP
                        index_files = [
                            (vdb_path + ".index", "session.index"),
                            (vdb_path + "_metadata.json", "session_metadata.json"),
                            (vdb_path + "_chunks.pkl", "session_chunks.pkl")
                        ]
                        
                        for local_path, archive_name in index_files:
                            if os.path.exists(local_path):
                                zipf.write(local_path, archive_name)
                                logger.debug(f"Added {archive_name} to backup ZIP")
                            else:
                                logger.warning(f"Vector database file missing: {local_path}")
                    
                    # Backup the ZIP file to Google Drive
                    file_id = drive_service.backup_vector_database(zip_path, session_id, backup_metadata)
                    
                finally:
                    # Clean up the temporary ZIP file
                    if os.path.exists(zip_path):
                        os.unlink(zip_path)
                
                if file_id:
                    session_data['needs_backup'] = False
                    session_data['last_backup'] = datetime.utcnow()
                    
                    # Update database record
                    self._update_vector_session_record(user_id, session_id, 'backed_up', file_id)
                    
                    logger.info(f"Backed up session {session_key} to Drive (file: {file_id})")
                    return True
                else:
                    logger.error(f"Failed to backup session {session_key} to Drive")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to backup session {user_id}_{session_id}: {str(e)}", exception=e)
            return False
    
    def cleanup_session(self, user_id: str, session_id: str, backup_first: bool = True) -> bool:
        """
        Clean up a vector database session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            backup_first: Whether to backup before cleanup
            
        Returns:
            bool: True if cleanup successful
        """
        try:
            session_key = f"{user_id}_{session_id}"
            
            # Backup if requested and needed
            if backup_first:
                self.backup_session_to_drive(user_id, session_id, force=False)
            
            with self.session_lock:
                if session_key not in self.active_sessions:
                    logger.debug(f"Session {session_key} already cleaned up")
                    return True
                
                session_data = self.active_sessions[session_key]
                temp_dir = session_data['temp_dir']
                
                # Remove session from active sessions
                del self.active_sessions[session_key]
                
                # Clean up temporary directory
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                
                # Update database record
                self._update_vector_session_record(user_id, session_id, 'cleaned_up')
                
                logger.info(f"Cleaned up session {session_key}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to cleanup session {user_id}_{session_id}: {str(e)}", exception=e)
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions automatically.
        
        Returns:
            int: Number of sessions cleaned up
        """
        try:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            with self.session_lock:
                for session_key, session_data in self.active_sessions.items():
                    last_activity = session_data['last_activity']
                    time_since_activity = (current_time - last_activity).total_seconds()
                    
                    if time_since_activity > self.session_timeout:
                        expired_sessions.append((session_data['user_id'], session_data['session_id']))
            
            # Clean up expired sessions
            cleaned_count = 0
            for user_id, session_id in expired_sessions:
                if self.cleanup_session(user_id, session_id, backup_first=True):
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}", exception=e)
            return 0
    
    def get_session_stats(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a user session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dict with session statistics or None
        """
        try:
            session_key = f"{user_id}_{session_id}"
            
            with self.session_lock:
                if session_key not in self.active_sessions:
                    return None
                
                session_data = self.active_sessions[session_key]
                vector_db = session_data['vector_db']
                
                vector_stats = vector_db.get_stats()
                
                # Calculate session age in hours
                session_age_hours = (datetime.utcnow() - session_data['created_at']).total_seconds() / 3600
                
                stats = {
                    'session_id': session_id,
                    'user_id': user_id,
                    'created_at': session_data['created_at'].isoformat(),
                    'last_activity': session_data['last_activity'].isoformat(),
                    'session_age_hours': round(session_age_hours, 1),
                    # Frontend expects these specific field names
                    'total_documents': session_data['document_count'],
                    'total_chunks': vector_stats.get('chunks_loaded', 0),
                    'vector_count': vector_stats.get('num_vectors', 0),
                    # Keep original fields for backward compatibility
                    'document_count': session_data['document_count'],
                    'needs_backup': session_data.get('needs_backup', False),
                    'last_backup': session_data.get('last_backup', {}).isoformat() if session_data.get('last_backup') else None,
                    'vector_stats': vector_stats
                }
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get session stats for {user_id}_{session_id}: {str(e)}", exception=e)
            return None
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """
        List all active vector database sessions.
        
        Returns:
            List of session information dictionaries
        """
        try:
            sessions = []
            
            with self.session_lock:
                for session_key, session_data in self.active_sessions.items():
                    session_info = {
                        'session_key': session_key,
                        'user_id': session_data['user_id'],
                        'session_id': session_data['session_id'],
                        'created_at': session_data['created_at'].isoformat(),
                        'last_activity': session_data['last_activity'].isoformat(),
                        'document_count': session_data['document_count'],
                        'needs_backup': session_data.get('needs_backup', False)
                    }
                    sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list active sessions: {str(e)}", exception=e)
            return []
    
    def _update_vector_session_record(self, user_id: str, session_id: str, status: str, drive_file_id: str = None):
        """
        Update the vector session record in the database.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            status: Session status
            drive_file_id: Optional Drive file ID for backup
        """
        try:
            if not db_config:
                return
            
            db_session = db_config.get_session()
            
            try:
                # Find or create vector session record
                vector_session = db_session.query(VectorSession).filter_by(
                    user_id=user_id,
                    session_id=session_id
                ).first()
                
                if not vector_session:
                    vector_session = VectorSession(
                        user_id=user_id,
                        session_id=session_id,
                        status=status,
                        drive_file_id=drive_file_id
                    )
                    db_session.add(vector_session)
                else:
                    vector_session.status = status
                    if drive_file_id:
                        vector_session.drive_file_id = drive_file_id
                    vector_session.updated_at = datetime.utcnow()
                
                db_session.commit()
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to update vector session record: {str(e)}", exception=e)
    
    async def start_cleanup_task(self):
        """Start background task for cleaning up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}", exception=e)


# Global session vector service instance
session_vector_service = SessionVectorService()