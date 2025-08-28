"""
Vector Search Service

High-level interface for vector search operations, providing optimization,
caching, result ranking, and search analytics for the GUARDIAN system.
Wraps the low-level vector database with advanced search capabilities.

Features:
- High-level search interface with multiple query types
- Query optimization and caching
- Result ranking and filtering
- Search analytics and monitoring
- Multi-index search support
- Search result explanations and similarity analysis
"""
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict

from ..config.settings import settings
from ..utils import logger, VectorDBError, SearchError, ProtocolValidationError
from ..core.ml.vector_db import VectorDatabase, SearchResult
from ..core.ml.embedding_model import EmbeddingModelHandler
from ..services.document_service import document_service

@dataclass
class SearchQuery:
    """
    Vector search query specification.
    
    Attributes:
        query_text: Text query to search for
        query_type: Type of query ('similarity', 'semantic', 'hybrid')
        top_k: Number of results to return
        similarity_threshold: Minimum similarity threshold
        filters: Optional filters to apply
        boost_keywords: Keywords to boost in ranking
        index_names: Specific indices to search (None for all available)
    """
    query_text: str
    query_type: str = "similarity"
    top_k: int = 10
    similarity_threshold: float = 0.3
    filters: Dict[str, Any] = None
    boost_keywords: List[str] = None
    index_names: List[str] = None

@dataclass
class RankedResult:
    """
    Search result with additional ranking information.
    
    Attributes:
        original_result: Original SearchResult from vector database
        final_score: Final ranking score after reranking
        ranking_factors: Factors that influenced ranking
        explanation: Human-readable explanation of why this result matched
        highlighted_text: Text with highlighted matching terms
        source_index: Index this result came from
        metadata_score: Score based on metadata matching
    """
    original_result: SearchResult
    final_score: float
    ranking_factors: Dict[str, float]
    explanation: str = ""
    highlighted_text: str = ""
    source_index: str = ""
    metadata_score: float = 0.0

@dataclass
class SearchResponse:
    """
    Complete search response with results and metadata.
    
    Attributes:
        query: Original search query
        results: List of ranked search results
        total_results: Total number of results before limiting
        search_time: Time taken for search
        indices_searched: List of indices that were searched
        query_analysis: Analysis of the query and search strategy
        suggestions: Suggested alternative queries
        aggregations: Result aggregations and statistics
    """
    query: SearchQuery
    results: List[RankedResult]
    total_results: int
    search_time: float
    indices_searched: List[str]
    query_analysis: Dict[str, Any] = None
    suggestions: List[str] = None
    aggregations: Dict[str, Any] = None

class VectorSearchService:
    """
    High-level vector search service with advanced capabilities.
    
    Provides an optimized interface for searching vector indices with
    result ranking, caching, analytics, and multi-index support.
    
    Attributes:
        vector_db: Vector database handler
        embedding_model: Embedding model for query vectorization
        enable_caching: Whether to enable search result caching
        search_cache: Cache of search results
        search_analytics: Analytics tracking search patterns
        available_indices: Registry of available vector indices
    """
    
    def __init__(self,
                 vector_db: VectorDatabase = None,
                 embedding_model: EmbeddingModelHandler = None,
                 enable_caching: bool = True,
                 cache_ttl: int = 3600):
        """
        Initialize the vector search service.
        
        Args:
            vector_db: Vector database handler (optional)
            embedding_model: Embedding model handler (optional)
            enable_caching: Whether to enable result caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.vector_db = vector_db or VectorDatabase()
        self.embedding_model = embedding_model or EmbeddingModelHandler()
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        
        # Search result cache with timestamps
        self.search_cache: Dict[str, Tuple[SearchResponse, float]] = {}
        
        # Search analytics
        self.search_analytics = {
            "total_searches": 0,
            "cache_hits": 0,
            "avg_search_time": 0.0,
            "popular_queries": defaultdict(  int),
            "result_click_tracking": defaultdict(int),
            "query_types": defaultdict(int)
        }
        
        # Registry of available indices
        self.available_indices: Dict[str, Dict[str, Any]] = {}
        
        logger.info(
            "Initialized VectorSearchService",
            enable_caching=enable_caching,
            cache_ttl=cache_ttl
        )
    
    def search(self,
               query_text: str,
               query_type: str = "similarity",
               top_k: int = None,
               similarity_threshold: float = None,
               filters: Dict[str, Any] = None,
               boost_keywords: List[str] = None,
               index_names: List[str] = None,
               enable_reranking: bool = True) -> SearchResponse:
        """
        Perform enhanced vector search with ranking and optimization.
        
        Args:
            query_text: Text to search for
            query_type: Type of search ('similarity', 'semantic', 'hybrid')
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            filters: Optional result filters
            boost_keywords: Keywords to boost in ranking
            index_names: Specific indices to search
            enable_reranking: Whether to apply result reranking
            
        Returns:
            SearchResponse: Enhanced search results
            
        Raises:
            SearchError: If search fails
            ProtocolValidationError: If query validation fails
        """
        start_time = time.time()
        
        try:
            # Create search query object
            query = SearchQuery(
                query_text=query_text,
                query_type=query_type,
                top_k=top_k or settings.vector_db.max_search_results,
                similarity_threshold=similarity_threshold or settings.vector_db.similarity_threshold,
                filters=filters,
                boost_keywords=boost_keywords,
                index_names=index_names
            )
            
            # Validate query
            self._validate_search_query(query)
            
            # Check cache first
            cache_key = self._generate_cache_key(query)
            if self.enable_caching:
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    self.search_analytics["cache_hits"] += 1
                    logger.debug("Returning cached search result", cache_key=cache_key[:8])
                    return cached_result
            
            logger.info(
                "Executing vector search",
                query_type=query_type,
                query_length=len(query_text),
                top_k=query.top_k
            )
            
            # Analyze query
            query_analysis = self._analyze_query(query)
            
            # Execute search
            raw_results = self._execute_vector_search(query)
            
            # Apply reranking if enabled
            if enable_reranking and raw_results:
                ranked_results = self._rerank_results(query, raw_results)
            else:
                ranked_results = self._convert_to_ranked_results(raw_results, query)
            
            # Generate suggestions
            suggestions = self._generate_search_suggestions(query, len(ranked_results))
            
            # Create search response
            response = SearchResponse(
                query=query,
                results=ranked_results,
                total_results=len(raw_results),
                search_time=time.time() - start_time,
                indices_searched=index_names or ["default"],
                query_analysis=query_analysis,
                suggestions=suggestions,
                aggregations=self._generate_result_aggregations(ranked_results)
            )
            
            # Cache result
            if self.enable_caching:
                self._cache_result(cache_key, response)
            
            # Update analytics
            self._update_search_analytics(query, response)
            
            logger.info(
                "Vector search completed",
                num_results=len(ranked_results),
                search_time=response.search_time,
                query_type=query_type
            )
            
            return response
            
        except (SearchError, ProtocolValidationError):
            raise
        except Exception as e:
            error_msg = f"Vector search failed: {str(e)}"
            logger.error(error_msg, query_text=query_text, exception=e)
            raise SearchError(error_msg)
    
    def multi_index_search(self,
                          query_text: str,
                          index_weights: Dict[str, float] = None,
                          **kwargs) -> SearchResponse:
        """
        Search across multiple indices with weighted result combination.
        
        Args:
            query_text: Text to search for
            index_weights: Weights for different indices
            **kwargs: Additional search parameters
            
        Returns:
            Combined search response from multiple indices
        """
        try:
            # Get available indices
            available_indices = list(self.available_indices.keys()) if self.available_indices else ["default"]
            index_weights = index_weights or {idx: 1.0 for idx in available_indices}
            
            all_results = []
            total_time = 0
            indices_searched = []
            
            # Search each index
            for index_name, weight in index_weights.items():
                try:
                    index_response = self.search(
                        query_text=query_text,
                        index_names=[index_name],
                        **kwargs
                    )
                    
                    # Apply index weight to results
                    for result in index_response.results:
                        result.final_score *= weight
                        result.source_index = index_name
                    
                    all_results.extend(index_response.results)
                    total_time += index_response.search_time
                    indices_searched.append(index_name)
                    
                except Exception as e:
                    logger.warning(f"Search failed for index {index_name}: {str(e)}")
                    continue
            
            # Sort combined results by final score
            all_results.sort(key=lambda x: x.final_score, reverse=True)
            
            # Limit to top_k
            top_k = kwargs.get('top_k', settings.vector_db.max_search_results)
            final_results = all_results[:top_k]
            
            # Create combined response
            query = SearchQuery(query_text=query_text, **kwargs)
            response = SearchResponse(
                query=query,
                results=final_results,
                total_results=len(all_results),
                search_time=total_time,
                indices_searched=indices_searched,
                aggregations=self._generate_result_aggregations(final_results)
            )
            
            logger.info(
                "Multi-index search completed",
                num_indices=len(indices_searched),
                total_results=len(final_results),
                total_time=total_time
            )
            
            return response
            
        except Exception as e:
            error_msg = f"Multi-index search failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise SearchError(error_msg)
    
    def _validate_search_query(self, query: SearchQuery):
        """
        Validate search query parameters.
        
        Args:
            query: Search query to validate
            
        Raises:
            ProtocolValidationError: If validation fails
        """
        if not query.query_text or not query.query_text.strip():
            raise ProtocolValidationError("Query text cannot be empty")
        
        if len(query.query_text) > 10000:
            raise ProtocolValidationError("Query text too long (max 10000 characters)")
        
        if query.top_k < 1 or query.top_k > 100:
            raise ProtocolValidationError("top_k must be between 1 and 100")
        
        if query.similarity_threshold < 0 or query.similarity_threshold > 1:
            raise ProtocolValidationError("similarity_threshold must be between 0 and 1")
        
        valid_types = ["similarity", "semantic", "hybrid"]
        if query.query_type not in valid_types:
            raise ProtocolValidationError(f"query_type must be one of: {valid_types}")
    
    def _execute_vector_search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Execute the core vector search operation.
        
        Args:
            query: Search query
            
        Returns:
            List of raw search results
            
        Raises:
            SearchError: If search execution fails
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.generate_embeddings([query.query_text])
            if not query_embedding or len(query_embedding) == 0:
                raise SearchError("Failed to generate query embedding")
            
            # Determine which index to use
            if query.index_names:
                index_name = query.index_names[0]  # Use first specified index
            else:
                index_name = "doc_86ce091b-ad62-423f-af06-a6a4b8b945dc"  # Default index
            
            # Load index if not already loaded
            if not self.vector_db.is_ready() or self.vector_db._current_index_name != index_name:
                if not self.vector_db.load_index(index_name):
                    raise SearchError(f"Failed to load index: {index_name}")
            
            # Execute search
            results = self.vector_db.search(
                query_vector=query_embedding[0],
                k=min(query.top_k * 2, 50),  # Retrieve more for reranking
                threshold=query.similarity_threshold
            )
            
            # Apply filters if specified
            if query.filters:
                results = self._apply_result_filters(results, query.filters)
            
            return results
            
        except Exception as e:
            error_msg = f"Vector search execution failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise SearchError(error_msg)
    
    def _rerank_results(self, query: SearchQuery, results: List[SearchResult]) -> List[RankedResult]:
        """
        Rerank search results using multiple ranking factors.
        
        Args:
            query: Original search query
            results: Raw search results
            
        Returns:
            List of reranked results
        """
        ranked_results = []
        
        for result in results:
            # Initialize ranking factors
            factors = {
                "semantic_similarity": result.similarity_score,
                "text_length_score": self._calculate_text_length_score(result.text),
                "keyword_boost": self._calculate_keyword_boost(result.text, query.boost_keywords or []),
                "metadata_relevance": self._calculate_metadata_score(result.metadata, query),
                "freshness_score": self._calculate_freshness_score(result.metadata)
            }
            
            # Calculate final score (weighted combination)
            weights = {
                "semantic_similarity": 0.5,
                "text_length_score": 0.1,
                "keyword_boost": 0.2,
                "metadata_relevance": 0.15,
                "freshness_score": 0.05
            }
            
            final_score = sum(factors[factor] * weights[factor] for factor in factors)
            
            # Generate explanation
            explanation = self._generate_result_explanation(result, factors, query)
            
            # Highlight matching text
            highlighted_text = self._highlight_matching_text(result.text, query.query_text)
            
            ranked_result = RankedResult(
                original_result=result,
                final_score=final_score,
                ranking_factors=factors,
                explanation=explanation,
                highlighted_text=highlighted_text,
                metadata_score=factors["metadata_relevance"]
            )
            
            ranked_results.append(ranked_result)
        
        # Sort by final score
        ranked_results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Limit to requested number
        return ranked_results[:query.top_k]
    
    def _convert_to_ranked_results(self, results: List[SearchResult], query: SearchQuery) -> List[RankedResult]:
        """
        Convert raw results to ranked results without reranking.
        
        Args:
            results: Raw search results
            query: Search query
            
        Returns:
            List of converted ranked results
        """
        ranked_results = []
        
        for result in results[:query.top_k]:
            ranked_result = RankedResult(
                original_result=result,
                final_score=result.similarity_score,
                ranking_factors={"semantic_similarity": result.similarity_score},
                explanation=f"Similarity score: {result.similarity_score:.3f}",
                highlighted_text=result.text
            )
            ranked_results.append(ranked_result)
        
        return ranked_results
    
    def _calculate_text_length_score(self, text: str) -> float:
        """Calculate score based on text length (prefer medium-length texts)."""
        length = len(text)
        if 500 <= length <= 2000:
            return 1.0
        elif 200 <= length <= 500 or 2000 <= length <= 5000:
            return 0.8
        elif length < 200:
            return 0.5
        else:
            return 0.3
    
    def _calculate_keyword_boost(self, text: str, boost_keywords: List[str]) -> float:
        """Calculate boost score based on keyword presence."""
        if not boost_keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for keyword in boost_keywords if keyword.lower() in text_lower)
        return min(matches / len(boost_keywords), 1.0)
    
    def _calculate_metadata_score(self, metadata: Dict[str, Any], query: SearchQuery) -> float:
        """Calculate score based on metadata relevance including document type priority."""
        if not metadata:
            return 0.0
        
        score = 0.0
        
        # Boost based on document type with enhanced categorization
        doc_type = metadata.get('document_type', '').lower()
        doc_category = metadata.get('document_category', '').lower()
        
        # Ground truth documents get highest priority
        if doc_type == 'ground_truth':
            score += 0.6
            # Extra boost for European Pharmacopoeia
            if 'european_pharmacopoeia' in doc_category:
                score += 0.3
            elif any(category in doc_category for category in ['usp_standard', 'ich_guideline', 'fda_guidance', 'ema_guideline']):
                score += 0.2
        # Protocol documents get moderate priority
        elif doc_type == 'protocol':
            score += 0.4
            # Boost analytical methods
            if 'analytical_method' in doc_category:
                score += 0.2
        # Reference documents get lower priority
        elif doc_type == 'reference':
            score += 0.2
        
        # Legacy support for old metadata format
        elif 'pharmacopoeia' in doc_type:
            score += 0.5
        
        # Boost based on section importance
        section = metadata.get('section', '').lower()
        if any(term in section for term in ['analytical', 'test', 'procedure', 'method']):
            score += 0.3
        
        # Additional boost for query-specific document type filtering
        if query.filters:
            requested_types = query.filters.get('document_type', [])
            if isinstance(requested_types, list) and doc_type in requested_types:
                score += 0.2
            
            requested_categories = query.filters.get('document_category', [])
            if isinstance(requested_categories, list) and doc_category in requested_categories:
                score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_freshness_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate score based on document freshness."""
        # For pharmaceutical standards, newer editions are generally better
        # This is a simplified implementation
        edition = metadata.get('edition', '')
        if edition:
            try:
                # Extract year or edition number
                year_match = re.search(r'(\d{4})', str(edition))
                if year_match:
                    year = int(year_match.group(1))
                    if year >= 2020:
                        return 1.0
                    elif year >= 2015:
                        return 0.8
                    elif year >= 2010:
                        return 0.6
                    else:
                        return 0.4
            except:
                pass
        
        return 0.5  # Default for unknown freshness
    
    def _generate_result_explanation(self,
                                   result: SearchResult,
                                   factors: Dict[str, float],
                                   query: SearchQuery) -> str:
        """Generate human-readable explanation for why result matched."""
        explanations = []
        
        if factors["semantic_similarity"] > 0.8:
            explanations.append("High semantic similarity to query")
        elif factors["semantic_similarity"] > 0.6:
            explanations.append("Good semantic similarity to query")
        else:
            explanations.append("Moderate semantic similarity to query")
        
        if factors["keyword_boost"] > 0.5:
            explanations.append("Contains important keywords")
        
        if factors["metadata_relevance"] > 0.5:
            explanations.append("Relevant document type and section")
        
        return "; ".join(explanations)
    
    def _highlight_matching_text(self, text: str, query: str) -> str:
        """Highlight matching terms in text (simplified implementation)."""
        # This is a basic implementation - could be enhanced with proper NLP
        words = query.lower().split()
        highlighted = text
        
        for word in words:
            if len(word) > 3:  # Only highlight longer words
                highlighted = highlighted.replace(
                    word, f"**{word}**"
                )
        
        return highlighted
    
    def _apply_result_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """Apply filters to search results with support for document type filtering."""
        if not filters:
            return results
        
        filtered = []
        
        for result in results:
            # Check each filter
            include = True
            
            for filter_key, filter_value in filters.items():
                metadata_value = result.metadata.get(filter_key)
                
                # Handle list-based filters (for document types and categories)
                if isinstance(filter_value, list):
                    if metadata_value not in filter_value:
                        include = False
                        break
                # Handle single value filters
                elif metadata_value != filter_value:
                    include = False
                    break
            
            if include:
                filtered.append(result)
        
        return filtered
    
    def _analyze_query(self, query: SearchQuery) -> Dict[str, Any]:
        """Analyze the search query and return insights."""
        analysis = {
            "query_length": len(query.query_text),
            "word_count": len(query.query_text.split()),
            "has_technical_terms": any(term in query.query_text.lower() 
                                     for term in ["analytical", "procedure", "test", "method"]),
            "complexity": "simple" if len(query.query_text.split()) < 5 else "complex"
        }
        
        return analysis
    
    def _generate_search_suggestions(self, query: SearchQuery, result_count: int) -> List[str]:
        """Generate alternative search suggestions."""
        suggestions = []
        
        if result_count == 0:
            suggestions.extend([
                "Try broader search terms",
                "Check spelling of technical terms",
                "Use synonyms or alternative terminology"
            ])
        elif result_count < 3:
            suggestions.extend([
                "Try related terms or synonyms",
                "Broaden your search criteria"
            ])
        
        return suggestions
    
    def _generate_result_aggregations(self, results: List[RankedResult]) -> Dict[str, Any]:
        """Generate aggregations and statistics from search results with enhanced document type analysis."""
        if not results:
            return {}
        
        # Calculate score distribution
        scores = [r.final_score for r in results]
        
        # Count by metadata categories
        doc_types = defaultdict(int)
        doc_categories = defaultdict(int)
        sections = defaultdict(int)
        source_indices = defaultdict(int)
        
        for result in results:
            metadata = result.original_result.metadata
            doc_types[metadata.get('document_type', 'unknown')] += 1
            doc_categories[metadata.get('document_category', 'unknown')] += 1
            sections[metadata.get('section', 'unknown')] += 1
            source_indices[result.source_index or 'default'] += 1
        
        return {
            "score_stats": {
                "min": min(scores),
                "max": max(scores),
                "avg": sum(scores) / len(scores)
            },
            "document_types": dict(doc_types),
            "document_categories": dict(doc_categories),
            "sections": dict(sections),
            "source_indices": dict(source_indices),
            "total_results": len(results),
            "ground_truth_results": doc_types.get('ground_truth', 0),
            "protocol_results": doc_types.get('protocol', 0),
            "reference_results": doc_types.get('reference', 0)
        }
    
    def _generate_cache_key(self, query: SearchQuery) -> str:
        """Generate cache key for search query."""
        query_str = f"{query.query_text}|{query.query_type}|{query.top_k}|{query.similarity_threshold}"
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[SearchResponse]:
        """Get cached search result if still valid."""
        if cache_key in self.search_cache:
            result, timestamp = self.search_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
            else:
                # Remove expired cache entry
                del self.search_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, response: SearchResponse):
        """Cache search result."""
        self.search_cache[cache_key] = (response, time.time())
        
        # Clean up old cache entries if cache is getting large
        if len(self.search_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Clean up expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.search_cache.items()
            if current_time - timestamp > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.search_cache[key]
        
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _update_search_analytics(self, query: SearchQuery, response: SearchResponse):
        """Update search analytics with query and response data."""
        self.search_analytics["total_searches"] += 1
        self.search_analytics["popular_queries"][query.query_text] += 1
        self.search_analytics["query_types"][query.query_type] += 1
        
        # Update average search time
        total_time = (self.search_analytics["avg_search_time"] * 
                     (self.search_analytics["total_searches"] - 1) + response.search_time)
        self.search_analytics["avg_search_time"] = total_time / self.search_analytics["total_searches"]
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics and statistics."""
        # Convert defaultdict to regular dict for JSON serialization
        return {
            "total_searches": self.search_analytics["total_searches"],
            "cache_hits": self.search_analytics["cache_hits"],
            "cache_hit_rate": (self.search_analytics["cache_hits"] / 
                              max(self.search_analytics["total_searches"], 1) * 100),
            "avg_search_time": self.search_analytics["avg_search_time"],
            "popular_queries": dict(sorted(self.search_analytics["popular_queries"].items(), 
                                             key=lambda x: x[1], reverse=True)[:10]),
            "query_types": dict(self.search_analytics["query_types"]),
            "cache_size": len(self.search_cache),
            "available_indices": list(self.available_indices.keys())
        }
    
    def register_index(self, index_name: str, metadata: Dict[str, Any] = None):
        """Register an available vector index."""
        self.available_indices[index_name] = metadata or {}
        logger.info(f"Registered vector index: {index_name}")
    
    def clear_cache(self) -> int:
        """Clear the search cache."""
        count = len(self.search_cache)
        self.search_cache.clear()
        logger.info(f"Cleared vector search cache", cleared_count=count)
        return count

# Global instance for use throughout the application
vector_search_service = VectorSearchService()