"""
Centralized Application Settings

Configuration management for the GUARDIAN backend application.
Uses dataclasses for type-safe configuration with defaults and
environment variable overrides.

Environment Variables:
- API_HOST: Server host (default: 0.0.0.0)
- API_PORT: Server port (default: 5051)
- API_DEBUG: Debug mode (default: True)
- LLM_API_URL: Local LLM API endpoint (default: http://localhost:1234/v1)
- LLM_MODEL_NAME: LLM model name (default: qwen3-30b-a3b@q4_M)

Configuration is loaded from:
1. Default values in dataclasses
2. .env file in backend directory
3. Environment variable overrides
"""
import os
from typing import Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Get the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
dotenv_path = os.path.join(BACKEND_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"Loaded environment variables from {dotenv_path}")
else:
    print(f"No .env file found at {dotenv_path}")

@dataclass
class APIConfig:
    """
    API server configuration.
    
    Attributes:
        host: Server bind address
        port: Server port number
        debug: Enable debug mode with hot reload
        max_file_size: Maximum upload file size in bytes
        upload_folder: Directory for temporary file uploads
    """
    host: str = '0.0.0.0'
    port: int = 5051
    debug: bool = True
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    upload_folder: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, 'storage', 'temp'))

@dataclass
class DatabaseConfig:
    """
    Database configuration.
    
    Configuration for PostgreSQL database connection and session management.
    
    Attributes:
        url: Database connection URL
        echo: Enable SQLAlchemy query logging
        pool_size: Database connection pool size
        max_overflow: Maximum connections beyond pool_size
        pool_timeout: Timeout for getting connection from pool
        pool_recycle: Recycle connections after this many seconds
    """
    url: str = "postgresql://guardian:guardian@localhost:5432/guardian"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour

@dataclass
class AuthConfig:
    """
    Authentication configuration.
    
    Configuration for Google OAuth and session management.
    
    Attributes:
        google_client_id: Google OAuth client ID
        google_client_secret: Google OAuth client secret
        google_redirect_uri: OAuth callback URL
        session_duration_hours: How long sessions last
        secret_key: Secret key for encryption
        session_secret: Secret for session signing
    """
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:5051/auth/google/callback"
    session_duration_hours: int = 24
    secret_key: str = ""
    session_secret: str = ""

@dataclass
class EmbeddingConfig:
    """
    Embedding model configuration.
    
    Controls which embedding model is used and how embeddings are generated
    for document chunks and protocols.
    
    Attributes:
        model_name: SentenceTransformer model name
        model_cache_dir: Directory to cache downloaded models
        batch_size: Batch size for embedding generation
        max_seq_length: Maximum sequence length for embeddings
        device: Device to use ('auto', 'cpu', 'cuda', 'mps')
    """
    model_name: str = "all-MiniLM-L6-v2"
    model_cache_dir: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, 'models', 'embeddings'))
    batch_size: int = 32
    max_seq_length: int = 384
    device: str = "auto"  # auto-detect best available device

@dataclass
class DocumentConfig:
    """
    Document processing configuration.
    
    Configuration for pharmaceutical standards document chunking,
    metadata extraction, and storage.
    
    Attributes:
        chunk_size: Approximate size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        storage_dir: Directory to store processed documents
        supported_formats: Supported document file formats
        max_chunks_per_document: Maximum chunks to generate per document
    """
    chunk_size: int = 10000
    chunk_overlap: int = 2000
    storage_dir: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, 'storage', 'documents'))
    supported_formats: list = field(default_factory=lambda: ['.txt', '.pdf', '.docx'])
    max_chunks_per_document: int = 50000

@dataclass
class VectorDBConfig:
    """
    Vector database configuration.
    
    Configuration for FAISS index creation, storage, and search.
    
    Attributes:
        index_type: FAISS index type ('IndexFlatIP', 'IndexHNSWFlat')
        storage_dir: Directory to store FAISS indices
        similarity_threshold: Minimum similarity score for search results
        max_search_results: Maximum number of search results to return
        hnsw_m: HNSW index parameter (connections per node)
        hnsw_ef_construction: HNSW index parameter (construction effort)
    """
    index_type: str = "IndexFlatIP"  # Exact inner product for cosine similarity
    storage_dir: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, 'storage', 'indices'))
    similarity_threshold: float = 0.3
    max_search_results: int = 20
    hnsw_m: int = 16
    hnsw_ef_construction: int = 200

@dataclass
class LLMConfig:
    """
    Large Language Model integration configuration.
    
    Configuration for local LLM API integration for compliance
    analysis and feedback generation.
    
    Attributes:
        api_url: Local LLM API endpoint
        model_name: Model name to use for analysis
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens in response
        timeout: Request timeout in seconds
        system_prompt: Default system prompt for compliance analysis
    """
    api_url: str = "http://localhost:1234/v1/chat/completions"
    model_name: str = "qwen3-30b-a3b@q4_M"
    temperature: float = 0.6
    max_tokens: int = 4000
    timeout: int = 300  # 5 minutes
    system_prompt: str = (
        "You are a pharmaceutical compliance assistant. Review laboratory protocols "
        "against pharmaceutical standards and provide specific feedback on "
        "compliance issues, terminology corrections, and missing elements."
    )

@dataclass
class ReportConfig:
    """
    Report generation configuration.
    
    Configuration for PDF and HTML report generation with
    styling and template options.
    
    Attributes:
        storage_dir: Directory to store generated reports
        template_dir: Directory containing report templates
        logo_dir: Directory containing logos for reports
        default_format: Default report format ('pdf', 'html', 'json')
        pdf_page_size: PDF page size ('A4', 'Letter')
        retention_days: Days to keep generated reports
    """
    storage_dir: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, 'storage', 'reports'))
    template_dir: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, 'templates'))
    logo_dir: str = field(default_factory=lambda: os.path.join(BACKEND_DIR, '..', 'guardian_old', 'assets'))
    default_format: str = "pdf"
    pdf_page_size: str = "A4"
    retention_days: int = 30

@dataclass
class AnalysisConfig:
    """
    Protocol analysis configuration.
    
    Configuration for protocol compliance analysis workflow,
    including search parameters and analysis options.
    
    Attributes:
        top_k_sections: Number of top similar sections to include in analysis
        enable_clustering: Enable clustering analysis for visualizations
        clustering_n_clusters: Number of clusters for k-means analysis
        enable_reference_extraction: Extract section references from LLM responses
        min_protocol_length: Minimum protocol length in characters
        max_protocol_length: Maximum protocol length in characters
    """
    top_k_sections: int = 15
    enable_clustering: bool = True
    clustering_n_clusters: int = 4
    enable_reference_extraction: bool = True
    min_protocol_length: int = 100
    max_protocol_length: int = 50000

@dataclass
class Settings:
    """
    Main application settings container.
    
    Aggregates all configuration sections and provides
    a unified interface for accessing settings throughout
    the GUARDIAN application.
    """
    api: APIConfig = field(default_factory=APIConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    @classmethod
    def load(cls) -> 'Settings':
        """
        Load settings from environment and config files.
        
        Loading order (later overrides earlier):
        1. Default values from dataclass definitions
        2. Values from .env file if present
        3. Environment variable overrides
        
        Returns:
            Settings instance with loaded configuration
        """
        settings = cls()
        
        # Override API settings with environment variables if present
        if os.getenv('API_HOST'):
            settings.api.host = os.getenv('API_HOST')
        if os.getenv('API_PORT'):
            settings.api.port = int(os.getenv('API_PORT'))
        if os.getenv('API_DEBUG'):
            settings.api.debug = os.getenv('API_DEBUG').lower() == 'true'
        
        # Override database settings
        if os.getenv('DATABASE_URL'):
            settings.database.url = os.getenv('DATABASE_URL')
        if os.getenv('DATABASE_ECHO'):
            settings.database.echo = os.getenv('DATABASE_ECHO').lower() == 'true'
        
        # Override authentication settings
        if os.getenv('GOOGLE_CLIENT_ID'):
            settings.auth.google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        if os.getenv('GOOGLE_CLIENT_SECRET'):
            settings.auth.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        if os.getenv('GOOGLE_REDIRECT_URI'):
            settings.auth.google_redirect_uri = os.getenv('GOOGLE_REDIRECT_URI')
        if os.getenv('SECRET_KEY'):
            settings.auth.secret_key = os.getenv('SECRET_KEY')
        if os.getenv('SESSION_SECRET'):
            settings.auth.session_secret = os.getenv('SESSION_SECRET')
        if os.getenv('SESSION_DURATION_HOURS'):
            settings.auth.session_duration_hours = int(os.getenv('SESSION_DURATION_HOURS'))
        
        # Override LLM settings with environment variables if present
        if os.getenv('LLM_API_URL'):
            settings.llm.api_url = os.getenv('LLM_API_URL')
        if os.getenv('LLM_MODEL_NAME'):
            settings.llm.model_name = os.getenv('LLM_MODEL_NAME')
        if os.getenv('LLM_TEMPERATURE'):
            settings.llm.temperature = float(os.getenv('LLM_TEMPERATURE'))
            
        # Override embedding settings
        if os.getenv('EMBEDDING_MODEL_NAME'):
            settings.embedding.model_name = os.getenv('EMBEDDING_MODEL_NAME')
        if os.getenv('EMBEDDING_DEVICE'):
            settings.embedding.device = os.getenv('EMBEDDING_DEVICE')
            
        return settings

# Global settings instance - import this in other modules
# Example: from config.settings import settings
settings = Settings.load()