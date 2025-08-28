"""
Google Drive Service

Handles Google Drive API operations for the GUARDIAN system.
Manages file uploads, downloads, and folder organization for user data persistence.
"""

from typing import Dict, Any, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import os
from datetime import datetime

from ...utils import logger

class GoogleDriveService:
    """
    Google Drive API service for file and folder operations.
    
    Manages the GUARDIAN application's data storage in users' Google Drive,
    including document uploads, vector database persistence, and chat history.
    """
    
    GUARDIAN_FOLDER_NAME = 'GUARDIAN_Data'
    
    # Subfolder structure for organized data storage
    SUBFOLDER_STRUCTURE = {
        'documents': 'Documents',
        'vector_db': 'Vector_Database',
        'chat_history': 'Chat_History',
        'analysis_results': 'Analysis_Results',
        'reports': 'Reports',
        'sessions': 'Session_Data'
    }
    
    # Document type subfolder structure within Documents folder
    DOCUMENT_TYPE_FOLDERS = {
        'ground_truth': 'Ground_Truth_Standards',
        'protocol': 'User_Protocols',
        'reference': 'Reference_Materials',
        'analysis_result': 'Analysis_Results'
    }
    
    def __init__(self, credentials: Credentials):
        """
        Initialize the Drive service with user credentials.
        
        Args:
            credentials: Google OAuth2 credentials
        """
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)
        self._folder_cache = {}  # Cache for folder IDs to avoid repeated API calls
        
        logger.info("Google Drive service initialized")
    
    def create_guardian_folder(self) -> str:
        """
        Create or find the main GUARDIAN folder in user's Drive.
        
        Returns:
            str: Folder ID of the GUARDIAN folder
        """
        try:
            # Check if folder already exists
            query = f"name='{self.GUARDIAN_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, pageSize=1).execute()
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                logger.info(f"Found existing GUARDIAN folder: {folder_id}")
                return folder_id
            
            # Create new folder
            folder_metadata = {
                'name': self.GUARDIAN_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder',
                'description': 'GUARDIAN AI Assistant Data Storage'
            }
            
            folder = self.service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
            
            logger.info(f"Created GUARDIAN folder: {folder_id}")
            return folder_id
            
        except HttpError as e:
            logger.error(f"Failed to create GUARDIAN folder: {str(e)}", exception=e)
            raise
    
    def upload_file(self, file_path: str, filename: str, parent_folder_id: str = None) -> str:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local path to the file
            filename: Name for the file in Drive
            parent_folder_id: Optional parent folder ID
            
        Returns:
            str: File ID of the uploaded file
        """
        try:
            file_metadata = {'name': filename}
            
            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Uploaded file to Drive: {filename} (ID: {file_id})")
            return file_id
            
        except HttpError as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}", exception=e)
            raise
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: Drive file ID
            local_path: Local path to save the file
            
        Returns:
            bool: True if download successful
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            with io.FileIO(local_path, 'wb') as local_file:
                downloader = MediaIoBaseDownload(local_file, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.info(f"Downloaded file from Drive: {file_id} -> {local_path}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to download file {file_id}: {str(e)}", exception=e)
            return False
    
    def list_files(self, parent_folder_id: str = None, name_contains: str = None) -> List[Dict[str, Any]]:
        """
        List files in a folder or matching criteria.
        
        Args:
            parent_folder_id: Optional parent folder to search in
            name_contains: Optional string that filename must contain
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            query_parts = ["trashed=false"]
            
            if parent_folder_id:
                query_parts.append(f"'{parent_folder_id}' in parents")
            
            if name_contains:
                query_parts.append(f"name contains '{name_contains}'")
            
            query = " and ".join(query_parts)
            
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="files(id,name,size,createdTime,modifiedTime,mimeType)"
            ).execute()
            
            files = results.get('files', [])
            logger.debug(f"Listed {len(files)} files from Drive")
            return files
            
        except HttpError as e:
            logger.error(f"Failed to list files: {str(e)}", exception=e)
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive.
        
        Args:
            file_id: Drive file ID to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            logger.info(f"Deleted file from Drive: {file_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Failed to delete file {file_id}: {str(e)}", exception=e)
            return False
    
    def setup_folder_structure(self) -> Dict[str, str]:
        """
        Create the complete GUARDIAN folder structure in user's Drive.
        
        Returns:
            Dict mapping subfolder names to their Drive IDs
        """
        try:
            # Create or get main GUARDIAN folder
            main_folder_id = self.create_guardian_folder()
            folder_ids = {'main': main_folder_id}
            
            # Create subfolders
            for key, folder_name in self.SUBFOLDER_STRUCTURE.items():
                folder_id = self._create_subfolder(folder_name, main_folder_id)
                folder_ids[key] = folder_id
                self._folder_cache[key] = folder_id
            
            logger.info(f"GUARDIAN folder structure created with {len(folder_ids)} folders")
            return folder_ids
            
        except Exception as e:
            logger.error(f"Failed to setup folder structure: {str(e)}", exception=e)
            raise
    
    def _create_subfolder(self, folder_name: str, parent_id: str) -> str:
        """
        Create a subfolder within a parent folder.
        
        Args:
            folder_name: Name of the subfolder
            parent_id: Parent folder ID
            
        Returns:
            str: Created folder ID
        """
        try:
            # Check if subfolder already exists
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, pageSize=1).execute()
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                logger.debug(f"Found existing subfolder: {folder_name} (ID: {folder_id})")
                return folder_id
            
            # Create new subfolder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id],
                'description': f'GUARDIAN {folder_name} storage'
            }
            
            folder = self.service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
            
            logger.info(f"Created subfolder: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except HttpError as e:
            logger.error(f"Failed to create subfolder {folder_name}: {str(e)}", exception=e)
            raise
    
    def get_folder_id(self, folder_type: str) -> str:
        """
        Get folder ID for a specific data type.
        
        Args:
            folder_type: Type of folder ('documents', 'vector_db', 'chat_history', etc.)
            
        Returns:
            str: Folder ID
        """
        if folder_type in self._folder_cache:
            return self._folder_cache[folder_type]
        
        # If not cached, setup folder structure
        folder_ids = self.setup_folder_structure()
        return folder_ids.get(folder_type)
    
    def get_document_type_folder_id(self, document_type: str) -> str:
        """
        Get folder ID for a specific document type within the Documents folder.
        
        Args:
            document_type: Type of document ('ground_truth', 'protocol', 'reference', 'analysis_result')
            
        Returns:
            str: Folder ID for the document type
        """
        cache_key = f"doc_type_{document_type}"
        
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        
        try:
            # Get the main Documents folder ID
            documents_folder_id = self.get_folder_id('documents')
            
            # Get the folder name for this document type
            folder_name = self.DOCUMENT_TYPE_FOLDERS.get(document_type, 'Other_Documents')
            
            # Check if document type folder already exists
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and parents in '{documents_folder_id}' and trashed=false"
            results = self.service.files().list(q=query, pageSize=1).execute()
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
                logger.info(f"Found existing document type folder: {folder_name} (ID: {folder_id})")
            else:
                # Create the document type folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [documents_folder_id],
                    'description': f'GUARDIAN {document_type.replace("_", " ").title()} Documents'
                }
                
                folder = self.service.files().create(body=folder_metadata).execute()
                folder_id = folder.get('id')
                logger.info(f"Created document type folder: {folder_name} (ID: {folder_id})")
            
            # Cache the folder ID
            self._folder_cache[cache_key] = folder_id
            return folder_id
            
        except HttpError as e:
            logger.error(f"Failed to get/create document type folder {document_type}: {str(e)}", exception=e)
            # Fall back to main Documents folder
            return self.get_folder_id('documents')
    
    def upload_document(self, file_path: str, filename: str, document_metadata: Dict[str, Any] = None, 
                       folder_type: str = None) -> str:
        """
        Upload a document to the appropriate folder based on document type with metadata.
        
        Args:
            file_path: Local path to the file
            filename: Name for the file in Drive
            document_metadata: Additional metadata to store
            folder_type: Document type for folder organization (ground_truth, protocol, etc.)
            
        Returns:
            str: File ID of the uploaded document
        """
        try:
            # Determine target folder based on document type
            if folder_type:
                target_folder_id = self.get_document_type_folder_id(folder_type)
            else:
                target_folder_id = self.get_folder_id('documents')
            
            # Extract document type information from metadata
            doc_type = document_metadata.get('document_type', 'unknown') if document_metadata else 'unknown'
            doc_category = document_metadata.get('document_category', 'other') if document_metadata else 'other'
            
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [target_folder_id],
                'description': f'GUARDIAN {doc_type} document upload'
            }
            
            # Add custom metadata as properties if provided
            if document_metadata:
                # Keep properties under 124-byte limit by storing minimal essential info
                file_metadata['properties'] = {
                    'file_type': 'document',
                    'guardian': 'true',
                    'doc_type': doc_type[:20],  # Truncate to avoid limit
                    'category': doc_category[:20]  # Truncate to avoid limit
                }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime,properties'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Uploaded {doc_type} document to Drive: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to upload document {filename}: {str(e)}", exception=e)
            raise
    
    def backup_vector_database(self, vdb_file_path: str, session_id: str, metadata: Dict[str, Any] = None) -> str:
        """
        Backup vector database to Google Drive.
        
        Args:
            vdb_file_path: Local path to vector database file
            session_id: Session identifier
            metadata: Additional metadata about the VDB
            
        Returns:
            str: File ID of the backed up VDB
        """
        try:
            vector_db_folder_id = self.get_folder_id('vector_db')
            
            # Create filename with timestamp and session ID
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat()
            filename = f"vdb_{session_id}_{timestamp}.faiss"
            
            file_metadata = {
                'name': filename,
                'parents': [vector_db_folder_id],
                'description': f'Vector database backup for session {session_id}',
                'properties': {
                    # Shorten session_id to last 8 characters to avoid Google Drive's 124-byte limit
                    'session': session_id[-8:] if len(session_id) > 8 else session_id,
                    'type': 'vdb'
                }
            }
            
            media = MediaFileUpload(vdb_file_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,size,createdTime,properties'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"Backed up vector database to Drive: {filename} (ID: {file_id})")
            return file_id
            
        except Exception as e:
            logger.error(f"Failed to backup vector database: {str(e)}", exception=e)
            raise
    
    def restore_vector_database(self, session_id: str, local_path: str) -> bool:
        """
        Restore vector database from Google Drive.
        
        Args:
            session_id: Session identifier
            local_path: Local path to restore the VDB file
            
        Returns:
            bool: True if restore successful
        """
        try:
            # Find the most recent VDB backup for this session
            vector_db_folder_id = self.get_folder_id('vector_db')
            
            query = f"'{vector_db_folder_id}' in parents and name contains 'vdb_{session_id}' and trashed=false"
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=1,
                fields="files(id,name,createdTime,properties)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                logger.warning(f"No vector database backup found for session {session_id}")
                return False
            
            file_info = files[0]
            file_id = file_info['id']
            
            # Download the file
            success = self.download_file(file_id, local_path)
            
            if success:
                logger.info(f"Restored vector database for session {session_id} from Drive")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to restore vector database for session {session_id}: {str(e)}", exception=e)
            return False
    
    def save_chat_history(self, session_id: str, chat_data: Dict[str, Any]) -> str:
        """
        Save chat history to Google Drive.
        
        Args:
            session_id: Chat session identifier
            chat_data: Chat session data to save
            
        Returns:
            str: File ID of the saved chat history
        """
        try:
            chat_history_folder_id = self.get_folder_id('chat_history')
            
            # Create filename with timestamp and session ID
            timestamp = datetime.utcnow().isoformat()
            filename = f"chat_{session_id}_{timestamp}.json"
            
            # Create temporary file with chat data
            import json
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(chat_data, temp_file, indent=2)
                temp_path = temp_file.name
            
            try:
                file_metadata = {
                    'name': filename,
                    'parents': [chat_history_folder_id],
                    'description': f'Chat history for session {session_id}',
                    'properties': {
                        'session_id': session_id,
                        'save_timestamp': timestamp,
                        'file_type': 'chat_history',
                        'message_count': str(len(chat_data.get('messages', [])))
                    }
                }
                
                media = MediaFileUpload(temp_path, resumable=True)
                
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size,createdTime,properties'
                ).execute()
                
                file_id = file.get('id')
                logger.info(f"Saved chat history to Drive: {filename} (ID: {file_id})")
                return file_id
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Failed to save chat history for session {session_id}: {str(e)}", exception=e)
            raise
    
    def load_chat_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load chat history from Google Drive.
        
        Args:
            session_id: Chat session identifier
            
        Returns:
            Dict with chat history data or None if not found
        """
        try:
            # Find the most recent chat history for this session
            chat_history_folder_id = self.get_folder_id('chat_history')
            
            query = f"'{chat_history_folder_id}' in parents and name contains 'chat_{session_id}' and trashed=false"
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=1,
                fields="files(id,name,createdTime,properties)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                logger.debug(f"No chat history found for session {session_id}")
                return None
            
            file_info = files[0]
            file_id = file_info['id']
            
            # Download and parse the file
            import json
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                success = self.download_file(file_id, temp_path)
                
                if success:
                    with open(temp_path, 'r') as f:
                        chat_data = json.load(f)
                    
                    logger.info(f"Loaded chat history for session {session_id} from Drive")
                    return chat_data
                else:
                    return None
                    
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Failed to load chat history for session {session_id}: {str(e)}", exception=e)
            return None
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metadata for a file.
        
        Args:
            file_id: Drive file ID
            
        Returns:
            Dict with file metadata or None if not found
        """
        try:
            file_info = self.service.files().get(
                fileId=file_id,
                fields="id,name,size,createdTime,modifiedTime,mimeType,properties,description"
            ).execute()
            
            logger.debug(f"Retrieved metadata for file {file_id}")
            return file_info
            
        except HttpError as e:
            logger.error(f"Failed to get metadata for file {file_id}: {str(e)}", exception=e)
            return None
    
    def list_user_files_by_type(self, file_type: str) -> List[Dict[str, Any]]:
        """
        List all files of a specific type for the user.
        
        Args:
            file_type: Type of files to list ('document', 'vector_database', 'chat_history')
            
        Returns:
            List of file metadata dictionaries
        """
        try:
            # Map file types to folder types
            folder_mapping = {
                'document': 'documents',
                'vector_database': 'vector_db', 
                'chat_history': 'chat_history',
                'analysis_result': 'analysis_results',
                'report': 'reports'
            }
            
            folder_type = folder_mapping.get(file_type)
            if not folder_type:
                logger.warning(f"Unknown file type: {file_type}")
                return []
            
            all_files = []
            
            # Special handling for documents - search both main folder and subfolders
            if file_type == 'document':
                # Get main documents folder
                documents_folder_id = self.get_folder_id('documents')
                
                # Search main documents folder
                query = f"'{documents_folder_id}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    pageSize=100,
                    fields="files(id,name,size,createdTime,modifiedTime,properties)",
                    orderBy='createdTime desc'
                ).execute()
                main_folder_files = results.get('files', [])
                all_files.extend(main_folder_files)
                
                # Search document type subfolders
                for doc_type in self.DOCUMENT_TYPE_FOLDERS.keys():
                    try:
                        doc_type_folder_id = self.get_document_type_folder_id(doc_type)
                        subfolder_query = f"'{doc_type_folder_id}' in parents and trashed=false"
                        subfolder_results = self.service.files().list(
                            q=subfolder_query,
                            pageSize=100,
                            fields="files(id,name,size,createdTime,modifiedTime,properties)",
                            orderBy='createdTime desc'
                        ).execute()
                        subfolder_files = subfolder_results.get('files', [])
                        all_files.extend(subfolder_files)
                        
                        if subfolder_files:
                            logger.debug(f"Found {len(subfolder_files)} files in {doc_type} subfolder")
                            
                    except Exception as subfolder_error:
                        logger.warning(f"Failed to search {doc_type} subfolder: {str(subfolder_error)}")
                        continue
                
                # Remove duplicates by file ID (in case of overlap)
                seen_ids = set()
                unique_files = []
                for file in all_files:
                    if file['id'] not in seen_ids:
                        seen_ids.add(file['id'])
                        unique_files.append(file)
                
                all_files = unique_files
                
            else:
                # For non-document types, use original logic
                folder_id = self.get_folder_id(folder_type)
                
                query = f"'{folder_id}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    pageSize=100,
                    fields="files(id,name,size,createdTime,modifiedTime,properties)",
                    orderBy='createdTime desc'
                ).execute()
                
                all_files = results.get('files', [])
            
            logger.info(f"Listed {len(all_files)} {file_type} files from Drive (including subfolders)")
            return all_files
            
        except Exception as e:
            logger.error(f"Failed to list {file_type} files: {str(e)}", exception=e)
            return []
    
    def save_analysis_results(self, analysis_id: str, analysis_data: Dict[str, Any]) -> str:
        """
        Save analysis results to Google Drive.
        
        Args:
            analysis_id: Analysis identifier
            analysis_data: Analysis results data to save
            
        Returns:
            str: File ID of the saved analysis results
        """
        try:
            analysis_results_folder_id = self.get_folder_id('analysis_results')
            
            # Create filename with timestamp and analysis ID
            timestamp = datetime.utcnow().isoformat()
            filename = f"analysis_{analysis_id}_{timestamp}.json"
            
            # Create temporary file with analysis data
            import json
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(analysis_data, temp_file, indent=2)
                temp_path = temp_file.name
            
            try:
                file_metadata = {
                    'name': filename,
                    'parents': [analysis_results_folder_id],
                    'description': f'Analysis results for {analysis_data.get("protocol_title", "Unknown Protocol")}',
                    'properties': {
                        'analysis_id': analysis_id,
                        'save_timestamp': timestamp,
                        'file_type': 'analysis_results',
                        'protocol_title': analysis_data.get('protocol_title', ''),
                        'protocol_type': analysis_data.get('protocol_type', ''),
                        'user_id': analysis_data.get('user_id', ''),
                        'session_id': analysis_data.get('session_id', '')
                    }
                }
                
                media = MediaFileUpload(temp_path, resumable=True)
                
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,size,createdTime,properties'
                ).execute()
                
                file_id = file.get('id')
                logger.info(f"Saved analysis results to Drive: {filename} (ID: {file_id})")
                return file_id
                
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Failed to save analysis results for {analysis_id}: {str(e)}", exception=e)
            raise
    
    def load_analysis_results(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Load analysis results from Google Drive.
        
        Args:
            analysis_id: Analysis identifier
            
        Returns:
            Dict with analysis results data or None if not found
        """
        try:
            # Find the most recent analysis results for this ID
            analysis_results_folder_id = self.get_folder_id('analysis_results')
            
            query = f"'{analysis_results_folder_id}' in parents and name contains 'analysis_{analysis_id}' and trashed=false"
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=1,
                fields="files(id,name,createdTime,properties)"
            ).execute()
            
            files = results.get('files', [])
            if not files:
                logger.warning(f"No analysis results found for ID {analysis_id}")
                return None
            
            file_info = files[0]
            file_id = file_info['id']
            
            # Download and parse the JSON file
            import json
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
                temp_path = temp_file.name
            
            try:
                if self.download_file(file_id, temp_path):
                    with open(temp_path, 'r') as f:
                        analysis_data = json.load(f)
                    logger.info(f"Loaded analysis results for ID {analysis_id} from Drive")
                    return analysis_data
                else:
                    return None
                    
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Failed to load analysis results for ID {analysis_id}: {str(e)}", exception=e)
            return None