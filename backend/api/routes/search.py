"""
Vector Search API Endpoints

REST API endpoints for searching pharmaceutical standards content using
vector similarity search with advanced ranking and filtering capabilities.

Features:
- POST /api/search - Vector similarity search
- POST /api/search/multi-index - Multi-index search
- GET /api/search/suggestions - Search suggestions
- GET /api/search/analytics - Search analytics
- GET /api/search/indices - Available indices
"""
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify

from ...config.settings import settings
from ...utils import logger, SearchError, ProtocolValidationError
from ...services.vector_service import vector_search_service
from ..schemas import (
    VectorSearchRequest,
    VectorSearchResponse,
    MultiIndexSearchRequest,
    SearchSuggestionRequest,
    SearchSuggestionResponse,
    SearchAnalyticsRequest,
    SearchAnalyticsResponse,
    AvailableIndicesResponse,
    ErrorResponse,
    ErrorDetail
)
from ..middleware.validation import validate_json

# Create blueprint
search_bp = Blueprint('search', __name__, url_prefix='/api/search')

@search_bp.route('', methods=['POST'])
@validate_json(VectorSearchRequest)
def vector_search():
    """
    Perform vector similarity search across Pharmacopoeia content.
    
    Request Body:
        VectorSearchRequest: Search query and parameters
        
    Returns:
        VectorSearchResponse: Search results with ranking and metadata
        
    Raises:
        400: Invalid search request
        500: Search processing error
    """
    try:
        # Get validated request data
        search_request = request.validated_json
        
        logger.info(
            "Starting vector search",
            query_length=len(search_request.query_text),
            query_type=search_request.query_type,
            top_k=search_request.top_k,
            include_explanations=search_request.include_explanations
        )
        
        # Perform search using vector service
        search_response = vector_search_service.search(
            query_text=search_request.query_text,
            query_type=search_request.query_type,
            top_k=search_request.top_k,
            similarity_threshold=search_request.similarity_threshold,
            filters=search_request.filters,
            boost_keywords=search_request.boost_keywords,
            index_names=search_request.index_names,
            enable_reranking=search_request.include_explanations
        )
        
        # Convert to API response format
        api_response = _convert_search_response_to_schema(search_response)
        
        logger.info(
            "Vector search completed",
            num_results=len(api_response.data),
            search_time=api_response.search_time,
            total_results=api_response.total_results
        )
        
        return jsonify(api_response.dict()), 200
        
    except ProtocolValidationError as e:
        logger.error(f"Search validation error: {str(e)}")
        error_response = ErrorResponse(
            message="Invalid search request",
            errors=[ErrorDetail(
                error_code="VALIDATION_ERROR",
                error_type="validation",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 400
        
    except SearchError as e:
        logger.error(f"Search processing error: {str(e)}")
        error_response = ErrorResponse(
            message="Search processing failed",
            errors=[ErrorDetail(
                error_code="SEARCH_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500
        
    except Exception as e:
        logger.error(f"Unexpected error in vector search: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Search failed",
            errors=[ErrorDetail(
                error_code="INTERNAL_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@search_bp.route('/multi-index', methods=['POST'])
@validate_json(MultiIndexSearchRequest)
def multi_index_search():
    """
    Perform search across multiple indices with weighted combination.
    
    Request Body:
        MultiIndexSearchRequest: Multi-index search request
        
    Returns:
        VectorSearchResponse: Combined search results
        
    Raises:
        400: Invalid search request
        500: Search processing error
    """
    try:
        # Get validated request data
        search_request = request.validated_json
        
        logger.info(
            "Starting multi-index search",
            query_length=len(search_request.query_text),
            num_indices=len(search_request.index_weights),
            index_weights=search_request.index_weights
        )
        
        # Perform multi-index search
        search_response = vector_search_service.multi_index_search(
            query_text=search_request.query_text,
            index_weights=search_request.index_weights,
            **search_request.search_options
        )
        
        # Convert to API response format
        api_response = _convert_search_response_to_schema(search_response)
        
        logger.info(
            "Multi-index search completed",
            num_results=len(api_response.data),
            search_time=api_response.search_time,
            indices_searched=len(api_response.indices_searched)
        )
        
        return jsonify(api_response.dict()), 200
        
    except Exception as e:
        logger.error(f"Multi-index search failed: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Multi-index search failed",
            errors=[ErrorDetail(
                error_code="MULTI_INDEX_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@search_bp.route('/suggestions', methods=['GET'])
def get_search_suggestions():
    """
    Get search suggestions based on partial query.
    
    Query Parameters:
        partial_query: Partial query text
        max_suggestions: Maximum number of suggestions (default: 10)
        include_popular: Include popular queries (default: true)
        
    Returns:
        SearchSuggestionResponse: Search suggestions
        
    Raises:
        400: Invalid query parameters
        500: Suggestion generation error
    """
    try:
        # Get query parameters
        partial_query = request.args.get('partial_query', '')
        max_suggestions = request.args.get('max_suggestions', 10, type=int)
        include_popular = request.args.get('include_popular', True, type=bool)
        
        if not partial_query:
            error_response = ErrorResponse(
                message="Partial query is required",
                errors=[ErrorDetail(
                    error_code="MISSING_QUERY",
                    error_type="validation",
                    details={"message": "partial_query parameter is required"}
                )]
            )
            return jsonify(error_response.dict()), 400
        
        logger.info(
            "Generating search suggestions",
            partial_query=partial_query,
            max_suggestions=max_suggestions,
            include_popular=include_popular
        )
        
        # Generate suggestions (simplified implementation)
        suggestions = _generate_search_suggestions(
            partial_query, max_suggestions, include_popular
        )
        
        response = SearchSuggestionResponse(
            message="Search suggestions generated successfully",
            data=suggestions,
            partial_query=partial_query
        )
        
        logger.info(f"Generated {len(suggestions)} search suggestions")
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to generate search suggestions: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to generate suggestions",
            errors=[ErrorDetail(
                error_code="SUGGESTION_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@search_bp.route('/analytics', methods=['GET'])
def get_search_analytics():
    """
    Get search analytics and statistics.
    
    Query Parameters:
        date_range: Date range in days (default: 30)
        include_details: Include detailed analytics (default: false)
        
    Returns:
        SearchAnalyticsResponse: Search analytics data
        
    Raises:
        500: Analytics retrieval error
    """
    try:
        # Get query parameters
        date_range = request.args.get('date_range', 30, type=int)
        include_details = request.args.get('include_details', False, type=bool)
        
        logger.info(
            "Retrieving search analytics",
            date_range=date_range,
            include_details=include_details
        )
        
        # Get analytics from vector service
        analytics = vector_search_service.get_search_analytics()
        
        # Convert to schema format
        from ..schemas.search import SearchAnalyticsData
        
        analytics_data = SearchAnalyticsData(
            total_searches=analytics.get('total_searches', 0),
            unique_queries=len(analytics.get('popular_queries', {})),
            avg_search_time=analytics.get('avg_search_time', 0.0),
            popular_queries=[
                {"query": query, "count": count}
                for query, count in analytics.get('popular_queries', {}).items()
            ],
            query_success_rate=95.0,  # TODO: Calculate actual success rate
            cache_hit_rate=analytics.get('cache_hit_rate', 0.0),
            search_trends=[]  # TODO: Implement search trends
        )
        
        response = SearchAnalyticsResponse(
            message="Search analytics retrieved successfully",
            data=analytics_data,
            date_range=date_range
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve search analytics: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve search analytics",
            errors=[ErrorDetail(
                error_code="ANALYTICS_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

@search_bp.route('/indices', methods=['GET'])
def get_available_indices():
    """
    Get information about available vector indices.
    
    Returns:
        AvailableIndicesResponse: List of available indices
        
    Raises:
        500: Index retrieval error
    """
    try:
        logger.info("Retrieving available indices")
        
        # Get available indices from vector service
        analytics = vector_search_service.get_search_analytics()
        available_indices = analytics.get('available_indices', [])
        
        # Convert to schema format
        from ..schemas.search import IndexInfoSchema
        from datetime import datetime
        
        index_schemas = []
        for index_name in available_indices:
            # Create index info (simplified - in production would get real metadata)
            index_info = IndexInfoSchema(
                index_name=index_name,
                document_count=0,  # TODO: Get actual document count
                vector_count=0,    # TODO: Get actual vector count
                index_size_mb=0.0, # TODO: Get actual size
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                metadata={}
            )
            index_schemas.append(index_info)
        
        response = AvailableIndicesResponse(
            message=f"Retrieved {len(index_schemas)} available indices",
            data=index_schemas
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Failed to retrieve available indices: {str(e)}", exception=e)
        error_response = ErrorResponse(
            message="Failed to retrieve available indices",
            errors=[ErrorDetail(
                error_code="INDICES_ERROR",
                error_type="processing",
                details={"message": str(e)}
            )]
        )
        return jsonify(error_response.dict()), 500

def _convert_search_response_to_schema(search_response) -> VectorSearchResponse:
    """
    Convert internal SearchResponse to API schema format.
    
    Args:
        search_response: Internal SearchResponse object
        
    Returns:
        VectorSearchResponse: API schema format
    """
    from ..schemas.search import VectorSearchResult, SearchResultRanking, SearchQueryAnalysis, SearchAggregations
    
    # Convert search results
    result_schemas = []
    for result in search_response.results:
        # Create ranking info if available
        ranking = None
        if result.ranking_factors:
            ranking = SearchResultRanking(
                final_score=result.final_score,
                ranking_factors=result.ranking_factors,
                explanation=result.explanation
            )
        
        # Create result schema
        result_schema = VectorSearchResult(
            chunk_index=result.original_result.chunk_index,
            similarity_score=result.original_result.similarity_score,
            text=result.original_result.text,
            metadata=result.original_result.metadata,
            ranking=ranking,
            highlighted_text=result.highlighted_text,
            source_index=result.source_index
        )
        result_schemas.append(result_schema)
    
    # Convert query analysis
    query_analysis = None
    if search_response.query_analysis:
        query_analysis = SearchQueryAnalysis(
            query_length=search_response.query_analysis.get('query_length', 0),
            word_count=search_response.query_analysis.get('word_count', 0),
            complexity=search_response.query_analysis.get('complexity', 'simple'),
            detected_topics=search_response.query_analysis.get('detected_topics', []),
            suggested_improvements=[]
        )
    
    # Convert aggregations
    aggregations = None
    if search_response.aggregations:
        aggregations = SearchAggregations(
            score_distribution=search_response.aggregations.get('score_stats', {}),
            metadata_facets={
                'document_types': search_response.aggregations.get('document_types', {}),
                'sections': search_response.aggregations.get('sections', {})
            },
            source_distribution={},
            result_stats=search_response.aggregations
        )
    
    # Create API response
    api_response = VectorSearchResponse(
        message=f"Found {len(result_schemas)} results in {search_response.search_time:.3f}s",
        data=result_schemas,
        query=search_response.query.query_text,
        total_results=search_response.total_results,
        search_time=search_response.search_time,
        indices_searched=search_response.indices_searched,
        query_analysis=query_analysis,
        suggestions=search_response.suggestions or [],
        aggregations=aggregations
    )
    
    return api_response

def _generate_search_suggestions(partial_query: str, max_suggestions: int, include_popular: bool) -> List:
    """
    Generate search suggestions based on partial query.
    
    Args:
        partial_query: Partial query text
        max_suggestions: Maximum suggestions to return
        include_popular: Whether to include popular queries
        
    Returns:
        List of search suggestions
    """
    from ..schemas.search import SearchSuggestion
    
    suggestions = []
    
    # Common pharmaceutical terms and phrases
    common_terms = [
        "analytical method",
        "analytical procedure", 
        "test method",
        "identification test",
        "purity test",
        "assay method",
        "dissolution test",
        "content uniformity",
        "related substances",
        "heavy metals",
        "microbiological test",
        "stability testing",
        "pharmacopoeia standard",
        "pharmaceutical standards",
        "reference standard",
        "chromatography",
        "spectroscopy",
        "titration method"
    ]
    
    partial_lower = partial_query.lower()
    
    # Generate completion suggestions
    for term in common_terms:
        if term.startswith(partial_lower) and term != partial_lower:
            suggestion = SearchSuggestion(
                suggestion=term,
                score=0.9,
                type="completion",
                metadata={"category": "pharmaceutical"}
            )
            suggestions.append(suggestion)
    
    # Generate related suggestions
    if "test" in partial_lower:
        related_terms = ["analytical test", "identification test", "purity test"]
        for term in related_terms:
            if term != partial_query.lower():
                suggestion = SearchSuggestion(
                    suggestion=term,
                    score=0.7,
                    type="related",
                    metadata={"category": "testing"}
                )
                suggestions.append(suggestion)
    
    # Add popular suggestions if requested
    if include_popular:
        popular_terms = [
            "chromatography method",
            "dissolution test procedure",
            "identification of active ingredient"
        ]
        for term in popular_terms:
            suggestion = SearchSuggestion(
                suggestion=term,
                score=0.8,
                type="popular",
                metadata={"category": "popular"}
            )
            suggestions.append(suggestion)
    
    # Sort by score and limit results
    suggestions.sort(key=lambda x: x.score, reverse=True)
    return suggestions[:max_suggestions]