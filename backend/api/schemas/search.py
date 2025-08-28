"""
Vector Search API Schemas

Pydantic models for vector search endpoints including query validation,
result formatting, and search analytics.

Features:
- Vector search request/response models
- Search result ranking and explanation schemas
- Multi-index search support models
- Search analytics and statistics schemas
- Document type filtering for targeted search
"""
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from .base import BaseResponse, SuccessResponse, PaginatedResponse
from ...models.document import DocumentType, DocumentCategory

class SearchQueryType(str, Enum):
    """Types of search queries."""
    SIMILARITY = "similarity"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"

class VectorSearchRequest(BaseModel):
    """
    Request model for vector search.
    
    Attributes:
        query_text: Text to search for
        query_type: Type of search (similarity, semantic, hybrid)
        top_k: Number of results to return
        similarity_threshold: Minimum similarity threshold
        filters: Optional result filters
        document_types: Filter by document types
        document_categories: Filter by document categories
        boost_keywords: Keywords to boost in ranking
        index_names: Specific indices to search
        include_explanations: Whether to include result explanations
    """
    query_text: str = Field(min_length=1, max_length=1000)
    query_type: SearchQueryType = SearchQueryType.SIMILARITY
    top_k: int = Field(10, ge=1, le=50)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    filters: Dict[str, Any] = Field(default_factory=dict)
    document_types: Optional[List[DocumentType]] = None
    document_categories: Optional[List[DocumentCategory]] = None
    boost_keywords: List[str] = Field(default_factory=list)
    index_names: Optional[List[str]] = None
    include_explanations: bool = True

class SearchResultRanking(BaseModel):
    """
    Search result ranking information.
    
    Attributes:
        final_score: Final ranking score after reranking
        ranking_factors: Factors that influenced ranking
        explanation: Human-readable explanation of ranking
    """
    final_score: float = Field(ge=0.0, le=1.0)
    ranking_factors: Dict[str, float] = Field(default_factory=dict)
    explanation: str = Field(max_length=500)

class VectorSearchResult(BaseModel):
    """
    Individual vector search result.
    
    Attributes:
        chunk_index: Index of the matching chunk
        similarity_score: Original similarity score
        text: Text content of the matching chunk
        metadata: Metadata of the matching chunk
        ranking: Ranking information (if reranking enabled)
        highlighted_text: Text with highlighted matching terms
        source_index: Index this result came from
    """
    chunk_index: int = Field(ge=0)
    similarity_score: float = Field(ge=0.0, le=1.0)
    text: str = Field(max_length=5000)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    ranking: Optional[SearchResultRanking] = None
    highlighted_text: Optional[str] = Field(None, max_length=5000)
    source_index: Optional[str] = Field(None, max_length=100)

class SearchQueryAnalysis(BaseModel):
    """
    Analysis of the search query.
    
    Attributes:
        query_length: Length of query text
        word_count: Number of words in query
        complexity: Query complexity assessment
        detected_topics: Detected topics or themes
        suggested_improvements: Suggestions for better results
    """
    query_length: int = Field(ge=0)
    word_count: int = Field(ge=0)
    complexity: str = Field(max_length=20)
    detected_topics: List[str] = Field(default_factory=list)
    suggested_improvements: List[str] = Field(default_factory=list)

class SearchAggregations(BaseModel):
    """
    Search result aggregations and statistics.
    
    Attributes:
        score_distribution: Distribution of similarity scores
        metadata_facets: Faceted search results by metadata
        source_distribution: Distribution by source index
        result_stats: Statistical information about results
    """
    score_distribution: Dict[str, int] = Field(default_factory=dict)
    metadata_facets: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    source_distribution: Dict[str, int] = Field(default_factory=dict)
    result_stats: Dict[str, Any] = Field(default_factory=dict)

class VectorSearchResponse(SuccessResponse):
    """
    Response for vector search request.
    
    Attributes:
        data: Search results
        query: Original search query
        total_results: Total number of results found
        search_time: Time taken for search in seconds
        indices_searched: List of indices that were searched
        query_analysis: Analysis of the search query
        suggestions: Suggested alternative queries
        aggregations: Result aggregations and statistics
    """
    data: List[VectorSearchResult]
    query: str
    total_results: int = Field(ge=0)
    search_time: float = Field(ge=0)
    indices_searched: List[str] = Field(default_factory=list)
    query_analysis: Optional[SearchQueryAnalysis] = None
    suggestions: List[str] = Field(default_factory=list)
    aggregations: Optional[SearchAggregations] = None

class MultiIndexSearchRequest(BaseModel):
    """
    Request model for multi-index search.
    
    Attributes:
        query_text: Text to search for
        index_weights: Weights for different indices
        search_options: Additional search options
    """
    query_text: str = Field(min_length=1, max_length=1000)
    index_weights: Dict[str, float] = Field(default_factory=dict)
    search_options: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('index_weights')
    def validate_weights(cls, v):
        for weight in v.values():
            if weight < 0 or weight > 10:
                raise ValueError('Index weights must be between 0 and 10')
        return v

class ProtocolAnalysisSearchRequest(BaseModel):
    """
    Request model for protocol analysis against ground truth documents.
    
    Attributes:
        protocol_text: Protocol text to analyze
        search_ground_truth_only: Only search ground truth documents
        top_k: Number of results to return
        similarity_threshold: Minimum similarity threshold
        ground_truth_categories: Specific ground truth categories to search
        include_explanations: Whether to include result explanations
    """
    protocol_text: str = Field(min_length=1, max_length=5000)
    search_ground_truth_only: bool = True
    top_k: int = Field(10, ge=1, le=50)
    similarity_threshold: float = Field(0.3, ge=0.0, le=1.0)
    ground_truth_categories: Optional[List[DocumentCategory]] = None
    include_explanations: bool = True

class SearchSuggestionRequest(BaseModel):
    """
    Request model for search suggestions.
    
    Attributes:
        partial_query: Partial query text
        max_suggestions: Maximum number of suggestions
        include_popular: Whether to include popular queries
    """
    partial_query: str = Field(min_length=1, max_length=100)
    max_suggestions: int = Field(10, ge=1, le=20)
    include_popular: bool = True

class SearchSuggestion(BaseModel):
    """
    Search suggestion item.
    
    Attributes:
        suggestion: Suggested query text
        score: Relevance score for suggestion
        type: Type of suggestion (completion, popular, related)
        metadata: Additional suggestion metadata
    """
    suggestion: str = Field(max_length=200)
    score: float = Field(ge=0.0, le=1.0)
    type: str = Field(max_length=20)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SearchSuggestionResponse(SuccessResponse):
    """
    Response for search suggestions.
    
    Attributes:
        data: List of search suggestions
        partial_query: Original partial query
    """
    data: List[SearchSuggestion]
    partial_query: str

class SearchAnalyticsRequest(BaseModel):
    """
    Request model for search analytics.
    
    Attributes:
        date_range: Date range for analytics (days)
        include_details: Whether to include detailed analytics
    """
    date_range: int = Field(30, ge=1, le=365)
    include_details: bool = False

class SearchAnalyticsData(BaseModel):
    """
    Search analytics data.
    
    Attributes:
        total_searches: Total number of searches
        unique_queries: Number of unique queries
        avg_search_time: Average search time in seconds
        popular_queries: Most popular search queries
        query_success_rate: Rate of queries returning results
        cache_hit_rate: Cache hit rate percentage
        search_trends: Search trends over time
    """
    total_searches: int = Field(ge=0)
    unique_queries: int = Field(ge=0)
    avg_search_time: float = Field(ge=0)
    popular_queries: List[Dict[str, Any]] = Field(default_factory=list)
    query_success_rate: float = Field(ge=0, le=100)
    cache_hit_rate: float = Field(ge=0, le=100)
    search_trends: List[Dict[str, Any]] = Field(default_factory=list)

class SearchAnalyticsResponse(SuccessResponse):
    """
    Response for search analytics.
    
    Attributes:
        data: Search analytics data
        date_range: Date range for the analytics
        generated_at: When analytics were generated
    """
    data: SearchAnalyticsData
    date_range: int
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class IndexInfoSchema(BaseModel):
    """
    Information about a vector index.
    
    Attributes:
        index_name: Name of the index
        document_count: Number of documents in index
        vector_count: Number of vectors in index
        index_size_mb: Size of index in MB
        created_at: When index was created
        last_updated: When index was last updated
        metadata: Additional index metadata
    """
    index_name: str = Field(max_length=100)
    document_count: int = Field(ge=0)
    vector_count: int = Field(ge=0)
    index_size_mb: float = Field(ge=0)
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AvailableIndicesResponse(SuccessResponse):
    """
    Response for available indices request.
    
    Attributes:
        data: List of available indices
    """
    data: List[IndexInfoSchema]