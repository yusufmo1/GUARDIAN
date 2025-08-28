"""
Document Management Service

High-level service for managing pharmaceutical standards documents and other
reference documents. Handles document upload, storage, processing, and indexing
for the GUARDIAN compliance analysis system.

Features:
- Document upload and validation
- Text extraction from multiple formats
- Document chunking and metadata extraction
- Index creation and management
- Document storage and retrieval
- Processing status tracking
"""
import os
import uuid
import time
import shutil
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict

from ..config.settings import settings
from ..utils import logger, DocumentError, DocumentNotFoundError, UnsupportedFormatError
from ..core.processors import document_processor, embedding_processor

@dataclass
class DocumentInfo:
    """
    Information about a stored document.
    
    Attributes:
        document_id: Unique identifier for the document
        filename: Original filename
        file_path: Path to stored file
        file_size: Size in bytes
        file_type: File extension/type
        upload_time: When document was uploaded
        processed: Whether document has been processed
        processing_time: Time taken for processing (if completed)
        num_chunks: Number of chunks created (if processed)
        index_name: Name of associated vector index (if created)
        metadata: Additional document metadata
        error: Error message if processing failed
    """
    document_id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    upload_time: float
    processed: bool = False
    processing_time: float = 0.0
    num_chunks: int = 0
    index_name: str = ""
    metadata: Dict[str, Any] = None
    error: str = ""

class DocumentService:
    """
    High-level document management service.
    
    Provides document lifecycle management from upload through processing
    and indexing. Integrates with the document processor and embedding
    processor to create searchable document indices.
    
    Attributes:
        storage_dir: Directory for storing uploaded documents
        temp_dir: Directory for temporary files during processing
        supported_formats: Supported file formats
        max_file_size: Maximum file size for uploads
        documents: Registry of stored documents
    """
    
    def __init__(self):
        """Initialize the document service."""
        self.storage_dir = settings.document.storage_dir
        self.temp_dir = os.path.join(self.storage_dir, 'temp')
        self.supported_formats = set(settings.document.supported_formats)
        self.max_file_size = settings.api.max_file_size
        
        # In-memory document registry (in production, use database)
        self.documents: Dict[str, DocumentInfo] = {}
        
        # Create directories
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(
            "Initialized DocumentService",
            storage_dir=self.storage_dir,
            supported_formats=list(self.supported_formats),
            max_file_size_mb=self.max_file_size / (1024 * 1024)
        )
    
    def upload_document(self, 
                       file_content: bytes,
                       filename: str,
                       file_type: str = None) -> str:
        """
        Upload and store a document.
        
        Args:
            file_content: Raw file content as bytes
            filename: Original filename
            file_type: File type/extension (auto-detected if not provided)
            
        Returns:
            str: Document ID for the uploaded document
            
        Raises:
            DocumentError: If upload fails
            UnsupportedFormatError: If file format not supported
        """
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Extract file type from filename if not provided
            if file_type is None:
                file_type = Path(filename).suffix.lower()
            
            # Validate file type
            if file_type not in self.supported_formats:
                raise UnsupportedFormatError(
                    f"File type '{file_type}' not supported",
                    details={"supported_formats": list(self.supported_formats)}
                )
            
            # Validate file size
            file_size = len(file_content)
            if file_size > self.max_file_size:
                raise DocumentError(
                    f"File size ({file_size} bytes) exceeds maximum ({self.max_file_size} bytes)"
                )
            
            # Generate storage path
            safe_filename = f"{document_id}_{Path(filename).name}"
            file_path = os.path.join(self.storage_dir, safe_filename)
            
            # Write file to storage
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Create document info
            doc_info = DocumentInfo(
                document_id=document_id,
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                upload_time=time.time(),
                metadata={}
            )
            
            # Store in registry
            self.documents[document_id] = doc_info
            
            logger.info(
                f"Document uploaded successfully",
                document_id=document_id,
                filename=filename,
                file_size=file_size,
                file_type=file_type
            )
            
            return document_id
            
        except (UnsupportedFormatError, DocumentError):
            raise
        except Exception as e:
            error_msg = f"Failed to upload document '{filename}': {str(e)}"
            logger.error(error_msg, exception=e)
            raise DocumentError(error_msg)
    
    def process_document(self, 
                        document_id: str,
                        create_index: bool = True,
                        index_name: str = None) -> bool:
        """
        Process a document through the embedding pipeline.
        
        Args:
            document_id: ID of the document to process
            create_index: Whether to create a vector index
            index_name: Custom name for the index (optional)
            
        Returns:
            bool: True if processing successful
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        doc_info = self.documents[document_id]
        
        if doc_info.processed:
            logger.info(f"Document {document_id} already processed")
            return True
        
        try:
            logger.info(
                f"Starting document processing",
                document_id=document_id,
                filename=doc_info.filename,
                create_index=create_index
            )
            
            # Generate index name if not provided
            if create_index and not index_name:
                index_name = f"doc_{document_id}"
            
            # Process through embedding pipeline
            result = embedding_processor.process_document(
                doc_info.file_path,
                index_name=index_name,
                show_progress=False  # Don't show progress in service layer
            )
            
            if result.success:
                # Update document info
                doc_info.processed = True
                doc_info.processing_time = result.total_time
                doc_info.num_chunks = result.num_chunks
                doc_info.index_name = result.index_name
                doc_info.metadata = result.stats or {}
                
                logger.info(
                    f"Document processing completed successfully",
                    document_id=document_id,
                    num_chunks=result.num_chunks,
                    processing_time_seconds=result.total_time,
                    index_name=result.index_name
                )
                
                return True
            else:
                # Update error info
                doc_info.error = result.error
                
                logger.error(
                    f"Document processing failed",
                    document_id=document_id,
                    error=result.error
                )
                
                return False
                
        except Exception as e:
            error_msg = f"Error processing document {document_id}: {str(e)}"
            doc_info.error = error_msg
            
            logger.error(error_msg, exception=e)
            return False
    
    def get_document_info(self, document_id: str) -> DocumentInfo:
        """
        Get information about a stored document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            DocumentInfo object
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        return self.documents[document_id]
    
    def list_documents(self, 
                      processed_only: bool = False,
                      file_type: str = None) -> List[DocumentInfo]:
        """
        List stored documents with optional filtering.
        
        Args:
            processed_only: Only return processed documents
            file_type: Filter by file type
            
        Returns:
            List of DocumentInfo objects
        """
        documents = list(self.documents.values())
        
        if processed_only:
            documents = [doc for doc in documents if doc.processed]
        
        if file_type:
            documents = [doc for doc in documents if doc.file_type == file_type]
        
        # Sort by upload time (newest first)
        documents.sort(key=lambda x: x.upload_time, reverse=True)
        
        return documents
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its associated files.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        doc_info = self.documents[document_id]
        
        try:
            # Remove file from storage
            if os.path.exists(doc_info.file_path):
                os.remove(doc_info.file_path)
                logger.debug(f"Deleted file: {doc_info.file_path}")
            
            # TODO: Remove associated vector index if exists
            # This would require integration with vector_db service
            
            # Remove from registry
            del self.documents[document_id]
            
            logger.info(
                f"Document deleted successfully",
                document_id=document_id,
                filename=doc_info.filename
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete document {document_id}: {str(e)}"
            logger.error(error_msg, exception=e)
            return False
    
    def get_document_content(self, document_id: str) -> bytes:
        """
        Retrieve the raw content of a document.
        
        Args:
            document_id: ID of the document
            
        Returns:
            Raw file content as bytes
            
        Raises:
            DocumentNotFoundError: If document not found
        """
        if document_id not in self.documents:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        
        doc_info = self.documents[document_id]
        
        try:
            with open(doc_info.file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            error_msg = f"Failed to read document {document_id}: {str(e)}"
            logger.error(error_msg, exception=e)
            raise DocumentError(error_msg)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about document processing.
        
        Returns:
            Dictionary with processing statistics
        """
        total_docs = len(self.documents)
        processed_docs = sum(1 for doc in self.documents.values() if doc.processed)
        failed_docs = sum(1 for doc in self.documents.values() if doc.error)
        
        if total_docs == 0:
            return {"message": "No documents uploaded"}
        
        total_size = sum(doc.file_size for doc in self.documents.values())
        avg_processing_time = (
            sum(doc.processing_time for doc in self.documents.values() if doc.processed) /
            max(processed_docs, 1)
        )
        
        file_types = {}
        for doc in self.documents.values():
            file_types[doc.file_type] = file_types.get(doc.file_type, 0) + 1
        
        return {
            "total_documents": total_docs,
            "processed_documents": processed_docs,
            "failed_documents": failed_docs,
            "processing_rate": f"{processed_docs/total_docs*100:.1f}%" if total_docs > 0 else "0%",
            "total_storage_mb": total_size / (1024 * 1024),
            "avg_processing_time_seconds": avg_processing_time,
            "file_types": file_types,
            "storage_directory": self.storage_dir
        }
    
    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary files from the temp directory.
        
        Returns:
            int: Number of files cleaned up
        """
        try:
            temp_files = [f for f in os.listdir(self.temp_dir) if os.path.isfile(os.path.join(self.temp_dir, f))]
            
            for temp_file in temp_files:
                temp_path = os.path.join(self.temp_dir, temp_file)
                os.remove(temp_path)
            
            logger.info(f"Cleaned up {len(temp_files)} temporary files")
            return len(temp_files)
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}", exception=e)
            return 0

# Global instance for use throughout the application
document_service = DocumentService()