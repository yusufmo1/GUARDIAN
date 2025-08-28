"""
Protocol Analysis Service

Core business logic orchestration for protocol compliance analysis against
pharmaceutical standards. Combines vector search, LLM integration,
and result processing into a unified analysis workflow.

Features:
- Protocol validation and preprocessing  
- Similarity search orchestration
- LLM prompt construction and execution
- Compliance analysis workflow
- Result aggregation and formatting
- Analysis history and caching
"""
import uuid
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from ..config.settings import settings
from ..utils import logger, ProtocolError, ProtocolValidationError, LLMError
from ..core.ml.embedding_model import EmbeddingModelHandler
from ..core.ml.vector_db import VectorDatabase, SearchResult
from ..services.document_service import document_service
from ..integrations.llm.services.compliance_service import compliance_service

@dataclass
class ProtocolInput:
    """
    Input protocol for compliance analysis.
    
    Attributes:
        protocol_text: Raw protocol text content
        protocol_title: Optional title/name for the protocol
        protocol_type: Type of protocol (e.g., 'analytical', 'manufacturing')
        metadata: Additional protocol metadata
    """
    protocol_text: str
    protocol_title: str = ""
    protocol_type: str = ""
    metadata: Dict[str, Any] = None

@dataclass
class SimilarSection:
    """
    Similar pharmaceutical standards section found via vector search.
    
    Attributes:
        section_text: Text content of the similar section
        similarity_score: Similarity score (0.0 to 1.0)
        section_metadata: Metadata about the section (page, chapter, etc.)
        chunk_index: Index in the vector database
    """
    section_text: str
    similarity_score: float
    section_metadata: Dict[str, Any]
    chunk_index: int

@dataclass
class ComplianceAnalysis:
    """
    LLM-generated compliance analysis results.
    
    Attributes:
        compliance_score: Overall compliance score (0-100)
        compliance_status: Status ('compliant', 'partial', 'non-compliant')
        issues: List of identified compliance issues
        recommendations: List of recommended improvements
        missing_elements: List of missing required elements
        terminology_corrections: List of terminology corrections
        confidence_score: Confidence in the analysis (0-100)
        analysis_text: Full LLM analysis text
    """
    compliance_score: int = 0
    compliance_status: str = "unknown"
    issues: List[str] = None
    recommendations: List[str] = None
    missing_elements: List[str] = None
    terminology_corrections: List[str] = None
    confidence_score: int = 0
    analysis_text: str = ""

@dataclass
class AnalysisResult:
    """
    Complete protocol analysis result.
    
    Attributes:
        analysis_id: Unique identifier for this analysis
        protocol_input: Original protocol input
        similar_sections: List of similar standards sections found
        compliance_analysis: LLM-generated compliance analysis
        processing_time: Total time taken for analysis
        timestamp: When analysis was performed
        index_name: Name of vector index used for search
        search_params: Parameters used for similarity search
        llm_params: Parameters used for LLM analysis
        error: Error message if analysis failed
    """
    analysis_id: str
    protocol_input: ProtocolInput
    similar_sections: List[SimilarSection] = None
    compliance_analysis: ComplianceAnalysis = None
    processing_time: float = 0.0
    timestamp: float = 0.0
    index_name: str = ""
    search_params: Dict[str, Any] = None
    llm_params: Dict[str, Any] = None
    error: str = ""

class ProtocolAnalysisService:
    """
    Core service for protocol compliance analysis.
    
    Orchestrates the complete analysis workflow from protocol input
    through vector search, LLM analysis, and result formatting.
    Provides caching and history management for analysis results.
    
    Attributes:
        embedding_model: Embedding model for protocol vectorization
        vector_db: Vector database for similarity search
        analysis_cache: Cache of completed analyses
        default_index_name: Default Pharmacopoeia index to search
        enable_caching: Whether to cache analysis results
    """
    
    def __init__(self,
                 embedding_model: EmbeddingModelHandler = None,
                 vector_db: VectorDatabase = None,
                 enable_caching: bool = True):
        """
        Initialize the protocol analysis service.
        
        Args:
            embedding_model: Embedding model handler (optional)
            vector_db: Vector database handler (optional)
            enable_caching: Whether to enable result caching
        """
        self.embedding_model = embedding_model or EmbeddingModelHandler()
        self.vector_db = vector_db or VectorDatabase()
        self.enable_caching = enable_caching
        self.default_index_name = "doc_86ce091b-ad62-423f-af06-a6a4b8b945dc"
        
        # Analysis cache and history (in production, use database)
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        self.analysis_history: List[str] = []  # List of analysis IDs
        
        logger.info(
            "Initialized ProtocolAnalysisService",
            enable_caching=enable_caching,
            default_index_name=self.default_index_name
        )
    
    def analyze_protocol(self,
                        protocol_text: str,
                        protocol_title: str = "",
                        protocol_type: str = "",
                        index_name: str = None,
                        top_k_sections: int = None,
                        metadata: Dict[str, Any] = None) -> AnalysisResult:
        """
        Analyze a protocol for compliance with pharmaceutical standards.
        
        Args:
            protocol_text: Raw protocol text to analyze
            protocol_title: Optional title for the protocol
            protocol_type: Type of protocol (analytical, manufacturing, etc.)
            index_name: Name of vector index to search (uses default if not provided)
            top_k_sections: Number of similar sections to retrieve
            metadata: Additional protocol metadata
            
        Returns:
            AnalysisResult: Complete analysis results
            
        Raises:
            ProtocolError: If analysis fails
            ProtocolValidationError: If protocol input is invalid
        """
        start_time = time.time()
        analysis_id = self._generate_analysis_id(protocol_text)
        
        try:
            # Check cache first
            if self.enable_caching and analysis_id in self.analysis_cache:
                logger.info(f"Returning cached analysis result", analysis_id=analysis_id)
                return self.analysis_cache[analysis_id]
            
            logger.info(
                "Starting protocol analysis",
                analysis_id=analysis_id,
                protocol_title=protocol_title,
                protocol_length=len(protocol_text)
            )
            
            # Validate protocol input
            protocol_input = self._validate_protocol_input(
                protocol_text, protocol_title, protocol_type, metadata
            )
            
            # Set default parameters
            index_name = index_name or self.default_index_name
            top_k_sections = top_k_sections or settings.analysis.top_k_sections
            
            # Create analysis result container
            result = AnalysisResult(
                analysis_id=analysis_id,
                protocol_input=protocol_input,
                timestamp=start_time,
                index_name=index_name,
                search_params={"top_k": top_k_sections},
                similar_sections=[],
                compliance_analysis=ComplianceAnalysis()
            )
            
            # Step 1: Find similar Pharmacopoeia sections
            logger.info("Searching for similar sections", analysis_id=analysis_id)
            similar_sections = self._find_similar_sections(
                protocol_text, index_name, top_k_sections
            )
            result.similar_sections = similar_sections
            
            if not similar_sections:
                logger.warning("No similar sections found", analysis_id=analysis_id)
                result.error = "No similar pharmaceutical standards sections found"
                return result
            
            # Step 2: Generate compliance analysis using LLM
            logger.info("Generating compliance analysis", analysis_id=analysis_id)
            compliance_analysis = self._generate_compliance_analysis(
                protocol_input, similar_sections
            )
            result.compliance_analysis = compliance_analysis
            
            # Calculate total processing time
            result.processing_time = time.time() - start_time
            
            # Cache and store result
            if self.enable_caching:
                self.analysis_cache[analysis_id] = result
                self.analysis_history.append(analysis_id)
            
            logger.info(
                "Protocol analysis completed successfully",
                analysis_id=analysis_id,
                processing_time_seconds=result.processing_time,
                compliance_score=compliance_analysis.compliance_score,
                num_similar_sections=len(similar_sections)
            )
            
            return result
            
        except (ProtocolValidationError, ProtocolError):
            raise
        except Exception as e:
            error_msg = f"Protocol analysis failed: {str(e)}"
            logger.error(error_msg, analysis_id=analysis_id, exception=e)
            raise ProtocolError(error_msg)
    
    def _validate_protocol_input(self,
                                protocol_text: str,
                                protocol_title: str,
                                protocol_type: str,
                                metadata: Dict[str, Any]) -> ProtocolInput:
        """
        Validate and clean protocol input.
        
        Args:
            protocol_text: Raw protocol text
            protocol_title: Protocol title
            protocol_type: Protocol type
            metadata: Additional metadata
            
        Returns:
            ProtocolInput: Validated protocol input
            
        Raises:
            ProtocolValidationError: If validation fails
        """
        if not protocol_text or not protocol_text.strip():
            raise ProtocolValidationError("Protocol text cannot be empty")
        
        protocol_text = protocol_text.strip()
        
        # Check length constraints
        if len(protocol_text) < settings.analysis.min_protocol_length:
            raise ProtocolValidationError(
                f"Protocol too short (minimum {settings.analysis.min_protocol_length} characters)"
            )
        
        if len(protocol_text) > settings.analysis.max_protocol_length:
            raise ProtocolValidationError(
                f"Protocol too long (maximum {settings.analysis.max_protocol_length} characters)"
            )
        
        return ProtocolInput(
            protocol_text=protocol_text,
            protocol_title=protocol_title.strip() if protocol_title else "",
            protocol_type=protocol_type.strip() if protocol_type else "",
            metadata=metadata or {}
        )
    
    def _find_similar_sections(self,
                              protocol_text: str,
                              index_name: str,
                              top_k: int) -> List[SimilarSection]:
        """
        Find similar pharmaceutical standards sections using vector search.
        
        Args:
            protocol_text: Protocol text to search for
            index_name: Name of vector index to search
            top_k: Number of top results to return
            
        Returns:
            List of SimilarSection objects
            
        Raises:
            ProtocolError: If search fails
        """
        try:
            # Load the vector index if not already loaded
            if not self.vector_db.is_ready():
                if not self.vector_db.load_index(index_name):
                    raise ProtocolError(f"Failed to load vector index: {index_name}")
            
            # Generate embedding for the protocol
            protocol_embedding = self.embedding_model.generate_embeddings([protocol_text])
            if protocol_embedding is None or len(protocol_embedding) == 0:
                raise ProtocolError("Failed to generate protocol embedding")
            
            # Search for similar sections
            search_results = self.vector_db.search(
                query_vector=protocol_embedding[0],
                k=top_k
            )
            
            # Convert search results to SimilarSection objects
            similar_sections = []
            for result in search_results:
                similar_section = SimilarSection(
                    section_text=result.text,
                    similarity_score=result.similarity_score,
                    section_metadata=result.metadata,
                    chunk_index=result.chunk_index
                )
                similar_sections.append(similar_section)
            
            logger.debug(
                f"Found {len(similar_sections)} similar sections",
                top_similarity=similar_sections[0].similarity_score if similar_sections else 0
            )
            
            return similar_sections
            
        except Exception as e:
            error_msg = f"Vector search failed: {str(e)}"
            logger.error(error_msg, exception=e)
            raise ProtocolError(error_msg)
    
    def _generate_compliance_analysis(self,
                                    protocol_input: ProtocolInput,
                                    similar_sections: List[SimilarSection]) -> ComplianceAnalysis:
        """
        Generate compliance analysis using LLM integration.
        
        Args:
            protocol_input: Protocol to analyze
            similar_sections: Similar standards sections for context
            
        Returns:
            ComplianceAnalysis: LLM-generated analysis results
            
        Raises:
            ProtocolError: If LLM analysis fails
        """
        try:
            # Convert similar sections to text format for LLM
            reference_sections = [section.section_text for section in similar_sections]
            
            # Use the compliance service for LLM-powered analysis
            llm_assessment = compliance_service.analyze_compliance(
                protocol_text=protocol_input.protocol_text,
                reference_sections=reference_sections,
                protocol_title=protocol_input.protocol_title
            )
            
            # Convert LLM assessment to our ComplianceAnalysis format
            analysis = ComplianceAnalysis(
                compliance_score=llm_assessment.overall_score,
                compliance_status=llm_assessment.compliance_status,
                issues=[issue.description for issue in llm_assessment.issues or []],
                recommendations=llm_assessment.recommendations or [],
                missing_elements=llm_assessment.missing_elements or [],
                terminology_corrections=llm_assessment.terminology_corrections or [],
                confidence_score=llm_assessment.confidence_score,
                analysis_text=llm_assessment.detailed_analysis
            )
            
            logger.info(
                "Generated LLM compliance analysis",
                compliance_score=analysis.compliance_score,
                status=analysis.compliance_status,
                num_issues=len(analysis.issues),
                confidence_score=analysis.confidence_score,
                num_sections=len(similar_sections)
            )
            
            return analysis
            
        except Exception as e:
            error_msg = f"LLM compliance analysis failed: {str(e)}"
            logger.error(error_msg, exception=e)
            
            # Fallback to similarity-based analysis if LLM fails
            logger.warning("Falling back to similarity-based analysis")
            
            if similar_sections:
                avg_similarity = sum(s.similarity_score for s in similar_sections) / len(similar_sections)
                compliance_score = min(100, int(avg_similarity * 100))
            else:
                compliance_score = 0
            
            # Determine compliance status based on score
            if compliance_score >= 80:
                status = "compliant"
            elif compliance_score >= 60:
                status = "partial"
            else:
                status = "non-compliant"
            
            # Generate fallback analysis
            return ComplianceAnalysis(
                compliance_score=compliance_score,
                compliance_status=status,
                issues=[f"LLM analysis failed: {error_msg}"],
                recommendations=["Manual review recommended due to analysis failure"],
                missing_elements=["LLM analysis unavailable"],
                terminology_corrections=[],
                confidence_score=30,  # Low confidence for fallback
                analysis_text=f"Fallback analysis based on {len(similar_sections)} similar sections. "
                             f"Average similarity: {avg_similarity:.2f}. "
                             f"LLM analysis failed: {error_msg}"
            )
    
    def _generate_analysis_id(self, protocol_text: str) -> str:
        """
        Generate a unique analysis ID based on protocol content.
        
        Args:
            protocol_text: Protocol text content
            
        Returns:
            Unique analysis ID string
        """
        # Create hash of protocol text for caching
        text_hash = hashlib.md5(protocol_text.encode()).hexdigest()[:8]
        timestamp = int(time.time() * 1000)  # Millisecond timestamp
        return f"analysis_{timestamp}_{text_hash}"
    
    def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """
        Retrieve a cached analysis result by ID.
        
        Args:
            analysis_id: Analysis ID to retrieve
            
        Returns:
            AnalysisResult if found, None otherwise
        """
        return self.analysis_cache.get(analysis_id)
    
    def list_analysis_history(self, limit: int = 50) -> List[str]:
        """
        Get list of recent analysis IDs.
        
        Args:
            limit: Maximum number of analysis IDs to return
            
        Returns:
            List of analysis IDs (most recent first)
        """
        return list(reversed(self.analysis_history[-limit:]))
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """
        Get statistics about performed analyses.
        
        Returns:
            Dictionary with analysis statistics
        """
        if not self.analysis_cache:
            return {"message": "No analyses performed yet"}
        
        analyses = list(self.analysis_cache.values())
        
        # Calculate statistics
        total_analyses = len(analyses)
        avg_processing_time = sum(a.processing_time for a in analyses) / total_analyses
        
        compliance_scores = [a.compliance_analysis.compliance_score for a in analyses 
                           if a.compliance_analysis]
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        status_counts = {}
        for analysis in analyses:
            if analysis.compliance_analysis:
                status = analysis.compliance_analysis.compliance_status
                status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_analyses": total_analyses,
            "avg_processing_time_seconds": avg_processing_time,
            "avg_compliance_score": avg_compliance,
            "compliance_status_distribution": status_counts,
            "cache_enabled": self.enable_caching,
            "default_index": self.default_index_name
        }
    
    def clear_cache(self) -> int:
        """
        Clear the analysis cache.
        
        Returns:
            Number of cached analyses cleared
        """
        count = len(self.analysis_cache)
        self.analysis_cache.clear()
        self.analysis_history.clear()
        
        logger.info(f"Cleared analysis cache", cleared_count=count)
        return count

# Global instance for use throughout the application
analysis_service = ProtocolAnalysisService()