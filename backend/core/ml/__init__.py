"""
Machine Learning Package

Contains ML-related components including embedding models and vector databases.
"""

from .embedding_model import EmbeddingModelHandler, embedding_model
from .vector_db import VectorDatabase, SearchResult, vector_db

__all__ = [
    'EmbeddingModelHandler',
    'embedding_model',
    'VectorDatabase', 
    'SearchResult',
    'vector_db'
]