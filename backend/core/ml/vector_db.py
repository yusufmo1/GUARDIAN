"""
Vector Database Handler

Manages FAISS index creation, storage, and similarity search operations.
Converted from notebook Cell 4 functionality with enhanced persistence,
configuration options, and error handling.

Features:
- FAISS index creation and management
- Persistent storage and loading of indices
- Similarity search with configurable parameters
- Support for different index types (Flat, HNSW)
- Metadata storage and retrieval
- Performance monitoring and logging
"""
import os
import pickle
import time
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Union, TYPE_CHECKING
from dataclasses import dataclass
import json

if TYPE_CHECKING:
    from ..processors.document_processor import DocumentChunk

try:
    import faiss
except ImportError:
    faiss = None

from ...config.settings import settings
from ...utils import logger, VectorDBError, IndexError, SearchError
# DocumentChunk imported dynamically to avoid circular imports

@dataclass
class SearchResult:
    """
    Result from a vector similarity search.
    
    Attributes:
        chunk_index: Index of the matching chunk
        similarity_score: Similarity score (higher is more similar)
        text: Text content of the matching chunk
        metadata: Metadata of the matching chunk
    """
    chunk_index: int
    similarity_score: float
    text: str
    metadata: Dict[str, Any]

class VectorDatabase:
    """
    Manages FAISS vector database for similarity search.
    
    Provides high-level interface for creating, storing, and querying
    vector indices built from document chunks and their embeddings.
    
    Attributes:
        index_type: Type of FAISS index to use
        storage_dir: Directory for storing indices and metadata
        similarity_threshold: Minimum similarity score for results
        max_results: Maximum number of search results to return
        _index: Loaded FAISS index
        _chunks: Stored document chunks
        _metadata: Chunk metadata for search results
        _dimension: Embedding dimension
        _num_vectors: Number of vectors in index
    """
    
    def __init__(self,
                 index_type: str = None,
                 storage_dir: str = None,
                 similarity_threshold: float = None,
                 max_results: int = None):
        """
        Initialize the vector database handler.
        
        Args:
            index_type: FAISS index type (defaults to config)
            storage_dir: Storage directory (defaults to config)
            similarity_threshold: Minimum similarity threshold (defaults to config)
            max_results: Maximum search results (defaults to config)
        """
        if faiss is None:
            raise VectorDBError("FAISS not available. Install with: pip install faiss-cpu")
        
        self.index_type = index_type or settings.vector_db.index_type
        self.storage_dir = storage_dir or settings.vector_db.storage_dir
        self.similarity_threshold = similarity_threshold or settings.vector_db.similarity_threshold
        self.max_results = max_results or settings.vector_db.max_search_results
        
        # HNSW parameters
        self.hnsw_m = settings.vector_db.hnsw_m
        self.hnsw_ef_construction = settings.vector_db.hnsw_ef_construction
        
        # Internal state
        self._index: Optional[faiss.Index] = None
        self._chunks: List["DocumentChunk"] = []
        self._metadata: List[Dict[str, Any]] = []
        self._dimension: Optional[int] = None
        self._num_vectors: int = 0
        
        # Create storage directory
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.info(
            f"Initialized VectorDatabase",
            index_type=self.index_type,
            storage_dir=self.storage_dir,
            similarity_threshold=self.similarity_threshold,
            max_results=self.max_results
        )
    
    def _create_index(self, dimension: int) -> faiss.Index:
        """
        Create a new FAISS index based on configuration.
        
        Args:
            dimension: Embedding dimension
            
        Returns:
            Initialized FAISS index
            
        Raises:
            VectorDBError: If index creation fails
        """
        try:
            logger.info(f"Creating {self.index_type} index with dimension {dimension}")
            
            if self.index_type == "IndexFlatIP":
                # Exact inner product search (good for cosine similarity with normalized vectors)
                index = faiss.IndexFlatIP(dimension)
                
            elif self.index_type == "IndexHNSWFlat":
                # HNSW (Hierarchical Navigable Small World) for faster approximate search
                index = faiss.IndexHNSWFlat(dimension, self.hnsw_m, faiss.METRIC_INNER_PRODUCT)
                index.hnsw.efConstruction = self.hnsw_ef_construction
                
            elif self.index_type == "IndexFlatL2":
                # Exact L2 (Euclidean) distance search
                index = faiss.IndexFlatL2(dimension)
                
            else:
                # Fallback to flat inner product
                logger.warning(f"Unknown index type {self.index_type}, using IndexFlatIP")
                index = faiss.IndexFlatIP(dimension)
            
            logger.info(f"Created {type(index).__name__} successfully")
            return index
            
        except Exception as e:
            raise VectorDBError(f"Failed to create FAISS index: {str(e)}")
    
    def build_index(self, 
                   embeddings: np.ndarray, 
                   chunks: List["DocumentChunk"]) -> bool:
        """
        Build a new vector index from embeddings and chunks.
        
        Args:
            embeddings: Normalized embeddings array [N, dimension]
            chunks: Corresponding document chunks
            
        Returns:
            bool: True if index built successfully
            
        Raises:
            VectorDBError: If index building fails
        """
        if len(embeddings) != len(chunks):
            raise VectorDBError(
                f"Embeddings count ({len(embeddings)}) doesn't match chunks count ({len(chunks)})"
            )
        
        try:
            start_time = time.time()
            
            # Get dimensions
            num_vectors, dimension = embeddings.shape
            self._dimension = dimension
            self._num_vectors = num_vectors
            
            logger.info(
                f"Building vector index",
                num_vectors=num_vectors,
                dimension=dimension,
                index_type=self.index_type
            )
            
            # Create index
            self._index = self._create_index(dimension)
            
            # Add vectors to index
            # Ensure embeddings are in float32 format for FAISS
            embeddings_float32 = embeddings.astype(np.float32)
            self._index.add(embeddings_float32)
            
            # Store chunks and extract metadata
            self._chunks = chunks
            self._metadata = []
            
            for chunk in chunks:
                metadata = {
                    'section': chunk.metadata.section,
                    'section_title': chunk.metadata.section_title,
                    'page': chunk.metadata.page,
                    'chunk_index': chunk.metadata.chunk_index,
                    'char_count': chunk.metadata.char_count,
                    'word_count': chunk.metadata.word_count
                }
                self._metadata.append(metadata)
            
            build_time = time.time() - start_time
            
            logger.info(
                f"Vector index built successfully",
                num_vectors=num_vectors,
                dimension=dimension,
                build_time_seconds=build_time,
                index_total_count=self._index.ntotal
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to build vector index: {str(e)}"
            logger.error(error_msg, exception=e)
            raise VectorDBError(error_msg)
    
    def search(self, 
              query_vector: np.ndarray, 
              k: int = None,
              return_similarities: bool = True) -> List[SearchResult]:
        """
        Search for similar vectors in the index.
        
        Args:
            query_vector: Query embedding vector [1, dimension] or [dimension]
            k: Number of results to return (defaults to max_results)
            return_similarities: Whether to return similarity scores
            
        Returns:
            List of SearchResult objects
            
        Raises:
            SearchError: If search fails or index not built
        """
        if self._index is None:
            raise SearchError("Index not built. Call build_index() first.")
        
        if k is None:
            k = self.max_results
        
        try:
            start_time = time.time()
            
            # Ensure query vector is in correct format
            if query_vector.ndim == 1:
                query_vector = query_vector.reshape(1, -1)
            
            # Ensure float32 format for FAISS
            query_vector = query_vector.astype(np.float32)
            
            logger.debug(
                f"Performing vector search",
                query_shape=query_vector.shape,
                k=k,
                index_total=self._index.ntotal
            )
            
            # Perform search
            similarities, indices = self._index.search(query_vector, k)
            
            # Flatten results (query_vector is batch of size 1)
            similarities = similarities[0]
            indices = indices[0]
            
            # Create search results
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities, indices)):
                # Check if result meets similarity threshold
                if similarity < self.similarity_threshold:
                    logger.debug(f"Skipping result {i} with similarity {similarity:.4f} below threshold {self.similarity_threshold}")
                    continue
                
                # Skip invalid indices (FAISS returns -1 for empty slots)
                if idx == -1 or idx >= len(self._chunks):
                    continue
                
                result = SearchResult(
                    chunk_index=int(idx),
                    similarity_score=float(similarity),
                    text=self._chunks[idx].text,
                    metadata=self._metadata[idx]
                )
                results.append(result)
            
            search_time = time.time() - start_time
            
            logger.log_vector_search(
                query_length=query_vector.shape[1],
                num_results=len(results),
                search_time=search_time,
                index_size=self._index.ntotal
            )
            
            logger.debug(
                f"Vector search completed",
                num_results=len(results),
                search_time_ms=search_time * 1000,
                max_similarity=max([r.similarity_score for r in results]) if results else 0,
                min_similarity=min([r.similarity_score for r in results]) if results else 0
            )
            
            return results
            
        except Exception as e:
            error_msg = f"Vector search failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise SearchError(error_msg)
    
    def save_index(self, index_name: str) -> bool:
        """
        Save the current index and metadata to disk.
        
        Args:
            index_name: Name for the saved index files
            
        Returns:
            bool: True if saved successfully
            
        Raises:
            VectorDBError: If saving fails
        """
        if self._index is None:
            raise VectorDBError("No index to save. Build index first.")
        
        try:
            # Define file paths
            index_path = os.path.join(self.storage_dir, f"{index_name}.index")
            metadata_path = os.path.join(self.storage_dir, f"{index_name}_metadata.json")
            chunks_path = os.path.join(self.storage_dir, f"{index_name}_chunks.pkl")
            
            logger.info(f"Saving index to {index_path}")
            
            # Save FAISS index
            faiss.write_index(self._index, index_path)
            
            # Save metadata
            index_info = {
                'index_type': self.index_type,
                'dimension': self._dimension,
                'num_vectors': self._num_vectors,
                'similarity_threshold': self.similarity_threshold,
                'metadata': self._metadata
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(index_info, f, indent=2)
            
            # Save chunks (for full text retrieval)
            with open(chunks_path, 'wb') as f:
                pickle.dump(self._chunks, f)
            
            logger.info(
                f"Index saved successfully",
                index_path=index_path,
                num_vectors=self._num_vectors,
                dimension=self._dimension
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to save index: {str(e)}"
            logger.error(error_msg, exception=e)
            raise VectorDBError(error_msg)
    
    def load_index(self, index_name: str) -> bool:
        """
        Load a previously saved index and metadata from disk.
        
        Args:
            index_name: Name of the saved index files
            
        Returns:
            bool: True if loaded successfully
            
        Raises:
            VectorDBError: If loading fails
        """
        try:
            # Define file paths
            index_path = os.path.join(self.storage_dir, f"{index_name}.index")
            metadata_path = os.path.join(self.storage_dir, f"{index_name}_metadata.json")
            chunks_path = os.path.join(self.storage_dir, f"{index_name}_chunks.pkl")
            
            # Check if files exist
            if not all(os.path.exists(p) for p in [index_path, metadata_path, chunks_path]):
                raise VectorDBError(f"Index files not found for {index_name}")
            
            logger.info(f"Loading index from {index_path}")
            
            # Load FAISS index
            self._index = faiss.read_index(index_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                index_info = json.load(f)
            
            self._dimension = index_info['dimension']
            self._num_vectors = index_info['num_vectors']
            self._metadata = index_info['metadata']
            
            # Load chunks
            with open(chunks_path, 'rb') as f:
                self._chunks = pickle.load(f)
            
            logger.info(
                f"Index loaded successfully",
                index_name=index_name,
                num_vectors=self._num_vectors,
                dimension=self._dimension,
                index_type=type(self._index).__name__
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load index {index_name}: {str(e)}"
            logger.error(error_msg, exception=e)
            raise VectorDBError(error_msg)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current index.
        
        Returns:
            Dictionary with index statistics
        """
        if self._index is None:
            return {"status": "no_index_loaded"}
        
        return {
            "status": "loaded",
            "index_type": type(self._index).__name__,
            "dimension": self._dimension,
            "num_vectors": self._num_vectors,
            "index_total": self._index.ntotal,
            "similarity_threshold": self.similarity_threshold,
            "max_results": self.max_results,
            "storage_dir": self.storage_dir,
            "chunks_loaded": len(self._chunks),
            "metadata_loaded": len(self._metadata)
        }
    
    def is_ready(self) -> bool:
        """
        Check if the vector database is ready for searches.
        
        Returns:
            bool: True if index is loaded and ready
        """
        return self._index is not None and len(self._chunks) > 0

# Global instance for use throughout the application
vector_db = VectorDatabase()