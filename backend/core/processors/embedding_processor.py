"""
Embedding Processing Pipeline

Orchestrates the complete workflow from document processing to vector index creation.
Combines document chunking, embedding generation, and vector database operations
into a unified pipeline for processing pharmaceutical standards documents.

Features:
- End-to-end document processing pipeline
- Batch embedding generation with progress tracking
- Vector index creation and persistence
- Protocol embedding and similarity search
- Error handling and recovery mechanisms
- Performance monitoring and optimization
"""
import time
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ...config.settings import settings
from ...utils import logger, EmbeddingError, DocumentError, VectorDBError
from ..processors.document_processor import DocumentProcessor, DocumentChunk
from ..ml.embedding_model import EmbeddingModelHandler
from ..ml.vector_db import VectorDatabase, SearchResult

@dataclass
class ProcessingResult:
    """
    Result from document processing pipeline.
    
    Attributes:
        success: Whether processing was successful
        document_path: Path to processed document
        num_chunks: Number of chunks created
        embedding_time: Time taken for embedding generation
        index_time: Time taken for index creation
        total_time: Total processing time
        index_name: Name of created index
        stats: Processing statistics
        error: Error message if processing failed
    """
    success: bool
    document_path: str = ""
    num_chunks: int = 0
    embedding_time: float = 0.0
    index_time: float = 0.0
    total_time: float = 0.0
    index_name: str = ""
    stats: Dict[str, Any] = None
    error: str = ""

class EmbeddingProcessor:
    """
    Orchestrates the complete embedding processing pipeline.
    
    Manages the workflow from document loading through vector index creation,
    providing a high-level interface for processing pharmaceutical standards
    documents and enabling similarity search for protocol analysis.
    
    Attributes:
        document_processor: Document chunking processor
        embedding_model: Embedding model handler
        vector_db: Vector database handler
        auto_save_index: Whether to auto-save indices after creation
        default_index_name: Default name for saved indices
    """
    
    def __init__(self,
                 document_processor: DocumentProcessor = None,
                 embedding_model: EmbeddingModelHandler = None,
                 vector_db: VectorDatabase = None,
                 auto_save_index: bool = True):
        """
        Initialize the embedding processor.
        
        Args:
            document_processor: Document processor instance (optional)
            embedding_model: Embedding model handler (optional)
            vector_db: Vector database handler (optional)
            auto_save_index: Whether to automatically save indices
        """
        self.document_processor = document_processor or DocumentProcessor()
        self.embedding_model = embedding_model or EmbeddingModelHandler()
        self.vector_db = vector_db or VectorDatabase()
        self.auto_save_index = auto_save_index
        self.default_index_name = "standards_index"
        
        logger.info(
            "Initialized EmbeddingProcessor",
            auto_save_index=auto_save_index,
            default_index_name=self.default_index_name
        )
    
    def process_document(self, 
                        document_path: str,
                        index_name: str = None,
                        show_progress: bool = True) -> ProcessingResult:
        """
        Process a document through the complete pipeline.
        
        Loads document, creates chunks, generates embeddings, builds vector index,
        and optionally saves the index for future use.
        
        Args:
            document_path: Path to the document file
            index_name: Name for the created index (optional)
            show_progress: Whether to show progress during processing
            
        Returns:
            ProcessingResult with success status and metrics
        """
        start_time = time.time()
        index_name = index_name or self.default_index_name
        
        logger.info(
            f"Starting document processing pipeline",
            document_path=document_path,
            index_name=index_name
        )
        
        try:
            # Step 1: Document chunking
            logger.info("Step 1: Processing document into chunks")
            chunk_start = time.time()
            
            chunks = self.document_processor.chunk_document(document_path)
            
            if not chunks:
                raise DocumentError("No chunks generated from document")
            
            chunk_time = time.time() - chunk_start
            
            logger.info(
                f"Document chunking completed",
                num_chunks=len(chunks),
                processing_time_seconds=chunk_time
            )
            
            # Step 2: Embedding generation
            logger.info("Step 2: Generating embeddings for chunks")
            embedding_start = time.time()
            
            # Extract text from chunks
            chunk_texts = [chunk.text for chunk in chunks]
            
            # Generate embeddings (with progress bar if requested)
            embeddings = self.embedding_model.generate_embeddings(
                chunk_texts,
                normalize=True,
                show_progress=show_progress
            )
            
            embedding_time = time.time() - embedding_start
            
            logger.info(
                f"Embedding generation completed",
                num_embeddings=len(embeddings),
                embedding_shape=embeddings.shape,
                generation_time_seconds=embedding_time
            )
            
            # Step 3: Vector index creation
            logger.info("Step 3: Building vector index")
            index_start = time.time()
            
            success = self.vector_db.build_index(embeddings, chunks)
            
            if not success:
                raise VectorDBError("Failed to build vector index")
            
            index_time = time.time() - index_start
            
            logger.info(
                f"Vector index built successfully",
                build_time_seconds=index_time,
                index_stats=self.vector_db.get_stats()
            )
            
            # Step 4: Save index if configured
            if self.auto_save_index:
                logger.info(f"Step 4: Saving index as '{index_name}'")
                save_success = self.vector_db.save_index(index_name)
                if save_success:
                    logger.info(f"Index saved successfully as '{index_name}'")
                else:
                    logger.warning(f"Failed to save index '{index_name}'")
            
            # Generate processing statistics
            total_time = time.time() - start_time
            stats = self.document_processor.get_processing_stats(chunks)
            stats.update({
                "embedding_dimension": embeddings.shape[1],
                "total_processing_time_seconds": total_time,
                "chunk_processing_time_seconds": chunk_time,
                "embedding_time_seconds": embedding_time,
                "index_build_time_seconds": index_time
            })
            
            result = ProcessingResult(
                success=True,
                document_path=document_path,
                num_chunks=len(chunks),
                embedding_time=embedding_time,
                index_time=index_time,
                total_time=total_time,
                index_name=index_name,
                stats=stats
            )
            
            logger.info(
                f"Document processing pipeline completed successfully",
                document_path=document_path,
                num_chunks=len(chunks),
                total_time_seconds=total_time,
                index_name=index_name
            )
            
            return result
            
        except Exception as e:
            total_time = time.time() - start_time
            error_msg = f"Document processing failed: {str(e)}"
            
            logger.error(
                error_msg,
                exception=e,
                document_path=document_path,
                processing_time_seconds=total_time
            )
            
            return ProcessingResult(
                success=False,
                document_path=document_path,
                total_time=total_time,
                error=error_msg
            )
    
    def embed_protocol(self, protocol_text: str) -> np.ndarray:
        """
        Generate embedding for a protocol text.
        
        Args:
            protocol_text: Protocol text to embed
            
        Returns:
            Normalized embedding vector
            
        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            logger.debug(f"Generating embedding for protocol text ({len(protocol_text)} characters)")
            
            embedding = self.embedding_model.embed_single_text(
                protocol_text,
                normalize=True
            )
            
            logger.debug(f"Protocol embedding generated", embedding_shape=embedding.shape)
            return embedding
            
        except Exception as e:
            error_msg = f"Failed to embed protocol: {str(e)}"
            logger.error(error_msg, exception=e)
            raise EmbeddingError(error_msg)
    
    def search_similar_chunks(self, 
                             protocol_text: str,
                             k: int = None,
                             similarity_threshold: float = None) -> List[SearchResult]:
        """
        Find chunks similar to a protocol text.
        
        Args:
            protocol_text: Protocol text to search for
            k: Number of results to return
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of SearchResult objects
            
        Raises:
            EmbeddingError: If protocol embedding fails
            VectorDBError: If search fails
        """
        # Update search parameters if provided
        if similarity_threshold is not None:
            original_threshold = self.vector_db.similarity_threshold
            self.vector_db.similarity_threshold = similarity_threshold
        
        try:
            # Generate embedding for protocol
            protocol_embedding = self.embed_protocol(protocol_text)
            
            # Search for similar chunks
            results = self.vector_db.search(
                protocol_embedding,
                k=k or settings.analysis.top_k_sections
            )
            
            logger.info(
                f"Similarity search completed",
                protocol_length=len(protocol_text),
                num_results=len(results),
                max_similarity=max([r.similarity_score for r in results]) if results else 0
            )
            
            return results
            
        except Exception as e:
            error_msg = f"Similarity search failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise
            
        finally:
            # Restore original threshold if it was changed
            if similarity_threshold is not None:
                self.vector_db.similarity_threshold = original_threshold
    
    def load_existing_index(self, index_name: str) -> bool:
        """
        Load a previously saved index.
        
        Args:
            index_name: Name of the index to load
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            success = self.vector_db.load_index(index_name)
            
            if success:
                logger.info(f"Loaded existing index '{index_name}'")
            else:
                logger.warning(f"Failed to load index '{index_name}'")
            
            return success
            
        except Exception as e:
            logger.error(f"Error loading index '{index_name}': {str(e)}", exception=e)
            return False
    
    def initialize_services(self) -> bool:
        """
        Initialize all required services (embedding model, etc.).
        
        Returns:
            bool: True if all services initialized successfully
        """
        try:
            logger.info("Initializing embedding processor services")
            
            # Initialize embedding model
            if not self.embedding_model.initialize():
                logger.error("Failed to initialize embedding model")
                return False
            
            logger.info("All embedding processor services initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}", exception=e)
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get status of all system components.
        
        Returns:
            Dictionary with component status information
        """
        return {
            "embedding_model": {
                "loaded": self.embedding_model.is_ready(),
                "info": self.embedding_model.get_model_info()
            },
            "vector_db": {
                "ready": self.vector_db.is_ready(),
                "stats": self.vector_db.get_stats()
            },
            "document_processor": {
                "chunk_size": self.document_processor.chunk_size,
                "chunk_overlap": self.document_processor.chunk_overlap,
                "storage_dir": self.document_processor.storage_dir
            }
        }
    
    def is_ready(self) -> bool:
        """
        Check if the processor is ready for operations.
        
        Returns:
            bool: True if all components are ready
        """
        return (self.embedding_model.is_ready() and 
                self.vector_db.is_ready())

# Global instance for use throughout the application
embedding_processor = EmbeddingProcessor()