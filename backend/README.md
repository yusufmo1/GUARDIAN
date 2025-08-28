# GUARDIAN Backend - Personal Reference Documentation

GUARDIAN is a pharmaceutical compliance analysis system that analyzes laboratory protocols against pharmaceutical standards using vector similarity search and LLM-powered compliance feedback.

## Table of Contents

- [Project Overview](#project-overview)
- [Quick Setup](#quick-setup)
- [Architecture Overview](#architecture-overview)
- [Directory Structure](#directory-structure)
- [Core Components](#core-components)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)

## Project Overview

### What is GUARDIAN?

GUARDIAN is a pharmaceutical compliance analysis system that helps ensure laboratory protocols comply with pharmaceutical standards. It uses machine learning for intelligent, automated compliance analysis.

### Key Features

- **Document Processing**: Upload and process pharmaceutical standards documents with intelligent text chunking
- **Vector Search**: FAISS-powered similarity search with SentenceTransformer embeddings  
- **LLM Integration**: Local LLM API integration for sophisticated compliance analysis
- **Analytics**: Comprehensive search analytics and performance monitoring
- **RESTful API**: Complete REST API with OpenAPI/Swagger documentation
- **Performance**: GPU acceleration support and intelligent caching

### Technology Stack

- **Framework**: Flask 2.3+ with Blueprint architecture
- **ML/AI**: SentenceTransformers, FAISS, PyTorch
- **Vector Database**: FAISS with IndexFlatIP for cosine similarity
- **LLM Integration**: OpenAI-compatible API (local LLM servers)
- **Document Processing**: Custom chunking with metadata extraction
- **Validation**: Pydantic for request/response validation
- **Logging**: Structured JSON logging with correlation IDs
- **Storage**: File-based storage with JSON metadata

## Quick Setup

### Prerequisites
- **Python**: 3.8+ (recommended: 3.9+)
- **System Memory**: Minimum 8GB RAM (16GB+ recommended for large documents)
- **GPU**: Optional but recommended for faster embedding generation
- **Storage**: At least 5GB free space for models and indices

### Installation

1. **Navigate to backend directory**
   ```bash
   cd guardian/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file** (optional - uses defaults if not present)
   ```bash
   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=5051
   API_DEBUG=true
   
   # ML Configuration
   EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
   EMBEDDING_DEVICE=auto  # auto, cpu, cuda, mps
   
   # LLM Configuration
   LLM_API_URL=http://localhost:1234/v1/chat/completions
   LLM_MODEL_NAME=qwen3-30b-a3b@q4_M
   ```

5. **Start the server**
   ```bash
   python main.py
   
   # Server runs on http://127.0.0.1:5051
   # API documentation: http://127.0.0.1:5051/docs/
   # Health check: http://127.0.0.1:5051/health
   ```

## Architecture Overview

GUARDIAN follows a layered architecture with clear separation of concerns:

### Application Layers

```
┌─────────────────────────────────────────┐
│              API Layer                  │
│  Routes, Schemas, Middleware, Docs      │
├─────────────────────────────────────────┤
│            Services Layer               │
│   Business Logic & Orchestration       │
├─────────────────────────────────────────┤
│              Core Layer                 │
│     ML Models, Vector DB, Processors    │
├─────────────────────────────────────────┤
│           Integration Layer             │
│          LLM, External APIs             │
├─────────────────────────────────────────┤
│            Storage Layer                │
│    Documents, Indices, Configuration    │
└─────────────────────────────────────────┘
```

### Data Flow

1. **Document Upload** → Validation → Storage → Processing → Embedding → Indexing
2. **Protocol Analysis** → Validation → Embedding → Vector Search → LLM Analysis → Response
3. **Search Request** → Query Processing → Vector Search → Result Ranking → Response

## Directory Structure

```
backend/
├── api/                          # API layer components
│   ├── docs/                     # API documentation (Swagger/OpenAPI)
│   ├── middleware/               # Request/response middleware
│   ├── routes/                   # API route handlers
│   │   ├── analysis.py           # Protocol analysis endpoints
│   │   ├── health.py             # Health check endpoints
│   │   ├── reports.py            # Report generation endpoints
│   │   ├── search.py             # Search and analytics endpoints
│   │   └── upload.py             # Document upload endpoints
│   └── schemas/                  # Pydantic validation schemas
├── config/                       # Configuration management
│   └── settings.py               # Centralized settings with dataclasses
├── core/                         # Core ML and processing components
│   ├── ml/                       # Machine learning components
│   │   ├── embedding_model.py    # SentenceTransformer wrapper
│   │   └── vector_db.py          # FAISS vector database handler
│   └── processors/               # Document processing
│       ├── document_processor.py # Text chunking and metadata extraction
│       └── embedding_processor.py# End-to-end processing pipeline
├── integrations/                 # External service integrations
│   └── llm/                      # LLM integration components
├── services/                     # Business logic services
│   ├── analysis_service.py       # Protocol analysis orchestration
│   ├── document_service.py       # Document management service
│   ├── report_service.py         # Report generation service
│   ├── vector_service.py         # High-level vector search service
│   └── visualization_service.py  # Data visualization service
├── static/                       # Static assets (CSS, images, branding)
├── storage/                      # Data storage directories
│   ├── documents/                # Uploaded documents
│   ├── indices/                  # Vector index files
│   └── reports/                  # Generated reports
├── templates/                    # HTML templates for reports
├── utils/                        # Utility modules
│   ├── branding.py               # Brand management utilities
│   ├── errors.py                 # Custom exception hierarchy
│   └── logging.py                # Structured logging configuration
├── main.py                       # Application entry point
├── requirements.txt              # Python dependencies
└── wsgi.py                       # WSGI application for production
```

## Core Components

### ML/AI Components

#### Embedding Model Handler (`core/ml/embedding_model.py`)
- **Purpose**: Manages SentenceTransformer models for text embeddings
- **Features**: GPU acceleration, batch processing, model caching
- **Model**: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **Performance**: ~500 texts/second on GPU, ~50 texts/second on CPU

```python
# Usage example
from core.ml.embedding_model import EmbeddingModelHandler

model = EmbeddingModelHandler()
embeddings = model.generate_embeddings(["text1", "text2"])
```

#### Vector Database (`core/ml/vector_db.py`)
- **Purpose**: FAISS-based vector similarity search
- **Index Type**: IndexFlatIP (cosine similarity)
- **Features**: Index persistence, batch search, similarity thresholding
- **Scalability**: Handles millions of vectors efficiently

```python
# Usage example
from core.ml.vector_db import VectorDatabase

db = VectorDatabase()
db.create_index(embeddings, metadata)
results = db.search(query_vector, k=10)
```

### Document Processing

#### Document Processor (`core/processors/document_processor.py`)
- **Purpose**: Pharmaceutical standards text chunking and metadata extraction
- **Features**: Section detection, overlapping chunks, metadata preservation
- **Chunk Size**: 500-2000 characters with 200-character overlap
- **Section Recognition**: Automatic detection of standards document sections

#### Embedding Processor (`core/processors/embedding_processor.py`)
- **Purpose**: End-to-end document processing pipeline
- **Workflow**: Upload → Chunk → Embed → Index → Store
- **Progress Tracking**: Real-time processing progress updates
- **Error Recovery**: Robust error handling with partial processing support

### Services Layer

#### Analysis Service (`services/analysis_service.py`)
- **Purpose**: Core protocol compliance analysis orchestration
- **Features**: Vector search, LLM integration, result caching
- **Analysis Types**: Compliance checking, terminology review, missing elements
- **Caching**: Intelligent result caching based on protocol content hash

#### Document Service (`services/document_service.py`)
- **Purpose**: Document lifecycle management
- **Features**: Upload, processing, deletion, metadata management
- **File Support**: `.txt`, `.pdf`, `.docx` (50MB max)
- **Storage**: File-based with JSON metadata

#### Vector Service (`services/vector_service.py`)
- **Purpose**: High-level vector search with ranking and analytics
- **Features**: Result reranking, search analytics, multi-index support
- **Ranking Factors**: Semantic similarity, text length, keyword matching, metadata relevance
- **Analytics**: Search patterns, cache hit rates, performance metrics

### LLM Integration

#### Compliance Service (`integrations/llm/services/compliance_service.py`)
- **Purpose**: LLM-powered pharmaceutical compliance analysis
- **Features**: Structured prompts, result validation, fallback mechanisms
- **API**: OpenAI-compatible local LLM servers
- **Fallback**: Similarity-based analysis when LLM unavailable

## API Documentation

### Core Endpoints

#### Health Check
- **Endpoint**: `GET /health`
- **Purpose**: System health monitoring
- **Response**: JSON with status, timestamp, version

#### Document Management
- **Upload**: `POST /api/documents/upload` - Upload and process documents
- **List**: `GET /api/documents` - List all documents with pagination
- **Details**: `GET /api/documents/{id}` - Get document information
- **Process**: `POST /api/documents/{id}/process` - Process document through pipeline
- **Delete**: `DELETE /api/documents/{id}` - Delete document and files
- **Statistics**: `GET /api/documents/stats` - Processing statistics

#### Protocol Analysis
- **Analyze**: `POST /api/analyze` - Analyze protocol compliance
- **Results**: `GET /api/analyze/{id}` - Get analysis results
- **History**: `GET /api/analyze/history` - Analysis history
- **Statistics**: `GET /api/analyze/stats` - Analysis statistics

#### Search & Analytics
- **Search**: `POST /api/search` - Vector similarity search
- **Multi-Index**: `POST /api/search/multi-index` - Search across multiple indices
- **Analytics**: `GET /api/search/analytics` - Search analytics and statistics
- **Suggestions**: `GET /api/search/suggestions` - Search suggestions

#### Interactive Documentation
- **Swagger UI**: `http://localhost:5051/docs/` - Interactive API testing
- **ReDoc**: `http://localhost:5051/redoc/` - Alternative documentation view
- **OpenAPI JSON**: `http://localhost:5051/api/openapi.json` - Raw OpenAPI spec

### Quick Examples

#### Upload Pharmaceutical Standards Document
```bash
# Convert file to base64
base64_content=$(base64 -i european_pharmacopoeia_8.txt)

# Upload via API
curl -X POST http://localhost:5051/api/documents/upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_content": "'$base64_content'",
    "filename": "european_pharmacopoeia_8.txt",
    "file_type": ".txt",
    "document_type": "pharmacopoeia",
    "process_immediately": true
  }'
```

#### Analyze Protocol
```bash
curl -X POST http://localhost:5051/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "protocol_text": "HPLC analysis with C18 column and UV detection at 254nm",
    "analysis_options": {
      "include_compliance_check": true,
      "include_terminology_review": true
    }
  }'
```

#### Search for Similar Sections
```bash
curl -X POST http://localhost:5051/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "HPLC mobile phase preparation",
    "top_k": 10,
    "similarity_threshold": 0.5
  }'
```

### Error Handling

All endpoints return consistent error responses:
```json
{
  "status": "error",
  "message": "Human-readable error message",
  "errors": [
    {
      "error_code": "VALIDATION_ERROR",
      "error_type": "validation",
      "field": "protocol_text",
      "details": {"message": "Protocol text is required"}
    }
  ],
  "timestamp": "2025-06-26T05:00:00Z"
}
```

## Configuration

### Settings Management

Configuration is managed through `config/settings.py` using dataclasses with environment variable overrides:

```python
@dataclass
class APISettings:
    host: str = "0.0.0.0"
    port: int = 5051
    debug: bool = False
    max_file_size: int = 50 * 1024 * 1024  # 50MB

@dataclass
class MLSettings:
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_device: str = "auto"
    embedding_batch_size: int = 32
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `5051` | Server port |
| `API_DEBUG` | `false` | Debug mode |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `EMBEDDING_DEVICE` | `auto` | Device for ML inference (auto/cpu/cuda/mps) |
| `LLM_API_URL` | `http://localhost:1234/v1/chat/completions` | LLM API endpoint |
| `LLM_MODEL_NAME` | `qwen3-30b-a3b@q4_M` | LLM model name |
| `VECTOR_DB_SIMILARITY_THRESHOLD` | `0.3` | Minimum similarity for search results |
| `VECTOR_DB_MAX_SEARCH_RESULTS` | `20` | Maximum search results to return |

### Storage Configuration

- **Documents**: `storage/documents/` - Uploaded document files
- **Indices**: `storage/indices/` - FAISS vector index files (.index, .pkl, .json)
- **Reports**: `storage/reports/` - Generated compliance reports
- **Logs**: `logs/` - Application log files
- **Models**: `models/embeddings/` - Cached ML models from HuggingFace

### File Limits and Formats

- **Maximum file size**: 50MB
- **Supported formats**: `.txt`, `.pdf`, `.docx`
- **Encoding**: Base64 encoding required for API uploads
- **Processing**: Automatic text extraction and chunking for all formats

---

*GUARDIAN Backend - Pharmaceutical Compliance Analysis System*  
*Personal Reference Documentation*