"""
Embedding Model Handler

Manages SentenceTransformer model loading, caching, and embedding generation
with GPU acceleration support. Converted from notebook Cell 1 and Cell 3
functionality.

Features:
- Automatic device selection (CPU, CUDA, MPS)
- Model caching and lazy loading
- Batch processing for memory efficiency
- Error handling and fallback options
- Performance monitoring and logging
"""
import os
import time
import torch
import numpy as np
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from ...config.settings import settings
from ...utils import logger, EmbeddingError, ModelLoadError, EmbeddingGenerationError

class EmbeddingModelHandler:
    """
    Handles SentenceTransformer model operations for the GUARDIAN system.
    
    Provides a clean interface for loading embedding models, generating
    embeddings for text chunks and protocols, and managing GPU acceleration.
    
    Attributes:
        model_name: Name of the SentenceTransformer model
        device: Device to use for computation ('auto', 'cpu', 'cuda', 'mps')
        model_cache_dir: Directory to cache downloaded models
        batch_size: Batch size for embedding generation
        max_seq_length: Maximum sequence length for embeddings
        _model: Loaded SentenceTransformer model instance
        _device: Resolved device string
        _initialized: Whether the model has been loaded
    """
    
    def __init__(self, 
                 model_name: str = None,
                 device: str = None,
                 batch_size: int = None,
                 model_cache_dir: str = None):
        """
        Initialize the embedding model handler.
        
        Args:
            model_name: SentenceTransformer model name (defaults to config)
            device: Device to use (defaults to config)
            batch_size: Batch size for processing (defaults to config)
            model_cache_dir: Model cache directory (defaults to config)
        """
        self.model_name = model_name or settings.embedding.model_name
        self.device = device or settings.embedding.device
        self.batch_size = batch_size or settings.embedding.batch_size
        self.model_cache_dir = model_cache_dir or settings.embedding.model_cache_dir
        self.max_seq_length = settings.embedding.max_seq_length
        
        self._model: Optional[SentenceTransformer] = None
        self._device: Optional[str] = None
        self._initialized = False
        
        # Create model cache directory if it doesn't exist
        os.makedirs(self.model_cache_dir, exist_ok=True)
        
        logger.info(
            f"Initialized EmbeddingModelHandler",
            model_name=self.model_name,
            device=self.device,
            batch_size=self.batch_size,
            cache_dir=self.model_cache_dir
        )
    
    def _detect_device(self) -> str:
        """
        Detect the best available device for computation.
        
        Returns:
            Device string ('cpu', 'cuda', 'mps')
        """
        if self.device.lower() != 'auto':
            return self.device.lower()
        
        # Auto-detect best available device
        if torch.backends.mps.is_available():
            detected_device = 'mps'
            logger.info("MPS GPU acceleration detected and available")
        elif torch.cuda.is_available():
            detected_device = 'cuda'
            logger.info("CUDA GPU acceleration detected and available")
        else:
            detected_device = 'cpu'
            logger.info("Using CPU for embedding computation")
        
        return detected_device
    
    def initialize(self) -> bool:
        """
        Load the SentenceTransformer model.
        
        Loads the model from cache or downloads it if not available.
        Configures the model for the detected device.
        
        Returns:
            bool: True if initialization successful, False otherwise
            
        Raises:
            ModelLoadError: If model loading fails
        """
        if self._initialized and self._model is not None:
            logger.debug("Model already initialized")
            return True
        
        try:
            start_time = time.time()
            
            # Detect best device
            self._device = self._detect_device()
            
            logger.info(
                f"Loading SentenceTransformer model: {self.model_name}",
                device=self._device,
                cache_dir=self.model_cache_dir
            )
            
            # Load the model with caching
            self._model = SentenceTransformer(
                self.model_name,
                cache_folder=self.model_cache_dir,
                device=self._device
            )
            
            # Configure model settings
            if hasattr(self._model, 'max_seq_length'):
                if self._model.max_seq_length > self.max_seq_length:
                    self._model.max_seq_length = self.max_seq_length
                    logger.info(f"Set max_seq_length to {self.max_seq_length}")
            
            # Move model to device if needed
            if self._device != 'cpu':
                self._model.to(self._device)
                logger.info(f"Model moved to device: {self._device}")
            
            load_time = time.time() - start_time
            self._initialized = True
            
            logger.info(
                f"Successfully loaded {self.model_name}",
                device=self._device,
                load_time_seconds=load_time,
                model_max_seq_length=getattr(self._model, 'max_seq_length', 'unknown')
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load embedding model {self.model_name}: {str(e)}"
            logger.error(error_msg, exception=e)
            raise ModelLoadError(error_msg, details={
                "model_name": self.model_name,
                "device": self._device,
                "cache_dir": self.model_cache_dir
            })
    
    def generate_embeddings(self, 
                          texts: Union[str, List[str]], 
                          normalize: bool = True,
                          show_progress: bool = False) -> np.ndarray:
        """
        Generate embeddings for input texts.
        
        Args:
            texts: Single text string or list of text strings
            normalize: Whether to normalize embeddings for cosine similarity
            show_progress: Whether to show progress bar for batch processing
            
        Returns:
            numpy array of embeddings with shape [N, embedding_dim]
            
        Raises:
            EmbeddingGenerationError: If embedding generation fails
        """
        if not self._initialized:
            if not self.initialize():
                raise EmbeddingGenerationError("Model not initialized")
        
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            raise EmbeddingGenerationError("No texts provided for embedding")
        
        try:
            start_time = time.time()
            
            logger.debug(
                f"Generating embeddings for {len(texts)} texts",
                num_texts=len(texts),
                batch_size=self.batch_size,
                device=self._device,
                normalize=normalize
            )
            
            # Process in batches to avoid memory issues
            all_embeddings = []
            
            # Add progress bar for large batches
            iterator = range(0, len(texts), self.batch_size)
            if show_progress and len(texts) > self.batch_size:
                iterator = tqdm(
                    iterator, 
                    desc="Generating embeddings",
                    total=(len(texts) + self.batch_size - 1) // self.batch_size
                )
            
            for i in iterator:
                batch = texts[i:i + self.batch_size]
                
                # Generate embeddings for this batch
                batch_embeddings = self._model.encode(
                    batch,
                    device=self._device,
                    show_progress_bar=False,  # We handle progress ourselves
                    convert_to_numpy=True
                )
                
                all_embeddings.append(batch_embeddings)
            
            # Concatenate all batch embeddings
            embeddings = np.vstack(all_embeddings)
            
            # Normalize embeddings for cosine similarity if requested
            if normalize:
                embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
                logger.debug("Embeddings normalized for cosine similarity")
            
            generation_time = time.time() - start_time
            
            logger.log_embedding_generation(
                text_length=sum(len(text) for text in texts),
                num_chunks=len(texts),
                embedding_time=generation_time,
                model_name=self.model_name
            )
            
            logger.info(
                f"Generated embeddings successfully",
                num_texts=len(texts),
                embedding_shape=embeddings.shape,
                generation_time_seconds=generation_time,
                normalized=normalize
            )
            
            return embeddings
            
        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            logger.error(error_msg, exception=e)
            raise EmbeddingGenerationError(error_msg, details={
                "num_texts": len(texts),
                "model_name": self.model_name,
                "device": self._device
            })
    
    def embed_single_text(self, text: str, normalize: bool = True) -> np.ndarray:
        """
        Generate embedding for a single text string.
        
        Convenience method for single text embedding.
        
        Args:
            text: Input text string
            normalize: Whether to normalize the embedding
            
        Returns:
            numpy array with shape [1, embedding_dim]
        """
        return self.generate_embeddings([text], normalize=normalize)
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the model.
        
        Returns:
            int: Embedding dimension
        """
        if not self._initialized:
            if not self.initialize():
                raise EmbeddingGenerationError("Model not initialized")
        
        return self._model.get_sentence_embedding_dimension()
    
    def is_loaded(self) -> bool:
        """
        Check if the model is loaded and ready.
        
        Returns:
            bool: True if model is loaded and ready
        """
        return self._initialized and self._model is not None
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            dict: Model information including name, device, and capabilities
        """
        return {
            "model_name": self.model_name,
            "device": self._device,
            "initialized": self._initialized,
            "batch_size": self.batch_size,
            "max_seq_length": self.max_seq_length,
            "embedding_dimension": self.get_embedding_dimension() if self.is_ready() else None,
            "cache_dir": self.model_cache_dir
        }

# Global instance - can be imported and used throughout the application
embedding_model = EmbeddingModelHandler()