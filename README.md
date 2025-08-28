# GUARDIAN: Privacy-First Pharmaceutical Compliance Analysis System

**Guided Universal Adherence & Regulatory Document Intelligence Assistant Network**

**MSc AI in Biosciences Dissertation Project**  
**Queen Mary University of London**  
**Author:** Yusuf Mohammed  
**Supervisor:** Mohammed Elbadawi  

<div align="center">

[![MSc Dissertation](https://img.shields.io/badge/MSc%20Dissertation-Queen%20Mary%20University%20of%20London-003E74?style=for-the-badge&logo=graduation-cap)](https://www.qmul.ac.uk/)
[![Academic Year](https://img.shields.io/badge/Academic%20Year-2024--2025-blue?style=for-the-badge)](https://github.com/yusufmo1)

### Core Technologies

[![Python](https://img.shields.io/badge/Python-3.10--3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-5.34.7-FF3E00?style=flat-square&logo=svelte&logoColor=white)](https://kit.svelte.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8.3-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Google Drive](https://img.shields.io/badge/Google%20Drive-API-4285F4?style=flat-square&logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)

### Privacy & Compliance Features

[![Privacy](https://img.shields.io/badge/Privacy-Zero%20Data%20Storage-darkgreen?style=flat-square&logo=shield)](https://github.com/yusufmo1)
[![OAuth](https://img.shields.io/badge/Auth-Google%20OAuth%202.0-EA4335?style=flat-square&logo=google)](https://developers.google.com/identity/protocols/oauth2)
[![FAISS](https://img.shields.io/badge/Vector%20DB-FAISS-FB923C?style=flat-square&logo=meta)](https://github.com/facebookresearch/faiss)
[![SentenceTransformers](https://img.shields.io/badge/Embeddings-MiniLM--L6--v2-orange?style=flat-square)](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
[![LLM](https://img.shields.io/badge/LLM-Qwen3--30B-blueviolet?style=flat-square)](https://github.com/yusufmo1)
[![API Endpoints](https://img.shields.io/badge/API%20Endpoints-40+-purple?style=flat-square)](https://github.com/yusufmo1)
[![Multi-Tenant](https://img.shields.io/badge/Architecture-Multi--Tenant-blue?style=flat-square)](https://github.com/yusufmo1)
[![Compliance](https://img.shields.io/badge/Standards-EP%2C%20USP%2C%20FDA-red?style=flat-square)](https://github.com/yusufmo1)

</div>

---

## Quick Navigation

[Executive Summary](#executive-summary) • 
[System Features](#system-features) • 
[Architecture](#system-architecture) • 
[Installation](#installation-and-setup) • 
[API Documentation](#api-documentation) • 
[Configuration](#configuration) • 
[Deployment](#deployment) • 
[Citation](#citation)

---

## Executive Summary

GUARDIAN is a production-ready privacy-first multi-tenant pharmaceutical compliance analysis system developed as part of an MSc dissertation exploring the integration of artificial intelligence into electronic laboratory notebooks. The system revolutionises pharmaceutical protocol validation against European Pharmacopoeia standards through a zero-trust architecture where all user data remains exclusively in the user's personal Google Drive, making data breaches mathematically impossible whilst providing enterprise-grade AI compliance analysis.

### Key Innovation

GUARDIAN addresses the critical challenge of pharmaceutical compliance whilst maintaining absolute data privacy through a revolutionary architecture:
- **Zero-trust implementation**: Backend servers store no user data, only authentication tokens and metadata
- **Complete user control**: All documents, analyses, and results persist exclusively in user's Google Drive
- **Session-based processing**: Temporary RAM processing with automatic cleanup ensures no data persistence
- **Multi-tenant isolation**: Complete separation between users with session-based vector databases

## System Features

### Privacy-First Data Architecture

- **Zero User Data Storage**: Backend never stores documents, analysis results, or chat history
- **Google Drive Integration**: All user content persists exclusively in user's Drive
- **PostgreSQL Metadata Only**: Database contains only auth tokens and file metadata
- **Temporary RAM Processing**: Documents processed in memory with immediate cleanup
- **Complete User Isolation**: Multi-tenant architecture with zero data leakage

### Backend Capabilities

- **40+ REST API Endpoints** across 7 functional areas
- **Google OAuth 2.0** authentication with encrypted token storage
- **Session-Based Vector Databases** loaded on-demand from user's Drive
- **AI-Powered Compliance Analysis** against European Pharmacopoeia standards
- **Multi-Format Document Support** (PDF, DOCX, TXT) with intelligent chunking
- **FAISS Vector Search** with user-isolated similarity matching
- **LLM Integration** for contextual compliance feedback
- **Professional Report Generation** with clustering visualisations
- **Automatic Session Management** with Drive backup and cleanup

### Frontend Features

- **Modern SvelteKit 5** with TypeScript and static site generation
- **Real-Time Processing Updates** with WebSocket integration
- **Interactive Chat Interface** for compliance guidance
- **Visual Analytics Dashboard** with Plotly.js visualisations
- **Drag-and-Drop Upload** with progress tracking
- **Responsive Design** optimised for all devices
- **Professional UI/UX** tailored for pharmaceutical industry

## System Architecture

### System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  SvelteKit      │────▶│  Flask Backend   │────▶│  PostgreSQL     │
│  Frontend       │     │  (Port 5051)     │     │  (Metadata)     │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                           
                               ▼                           
                    ┌──────────────────┐                  
                    │                  │                  
                    │  Google Drive    │                  
                    │  (User Data)     │                  
                    │                  │                  
                    └──────────────────┘                  
```

### Directory Structure

```
guardian/
├── backend/                    # Flask API server
│   ├── api/                   # REST API endpoints
│   │   ├── routes/           # Route handlers (auth, analysis, etc.)
│   │   ├── schemas/          # Pydantic request/response models
│   │   └── middleware/       # Authentication, validation, error handling
│   ├── core/                  # ML components
│   │   ├── ml/              # Embedding models, vector databases
│   │   └── processors/      # Document processing, chunking
│   ├── models/               # PostgreSQL database models
│   ├── services/             # Business logic layer
│   │   ├── auth/           # Authentication services
│   │   └── *.py            # Document, analysis, report services
│   ├── integrations/         # External integrations
│   │   ├── google/         # OAuth 2.0, Drive API
│   │   └── llm/            # LLM client and services
│   └── config/              # Configuration management
├── frontend/                 # SvelteKit application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/ # UI components
│   │   │   ├── services/   # API client
│   │   │   ├── stores/     # State management
│   │   │   └── types/      # TypeScript definitions
│   │   └── routes/         # Page components
│   └── static/             # Static assets
├── docker/                   # Docker configuration
├── scripts/                  # Deployment scripts
└── docs/                    # Architecture documentation
```

### Core Architectural Principles

1. **Privacy by Design**: User data never persists on servers
2. **Multi-Tenant Isolation**: Complete separation between users at all layers
3. **Session-Based Processing**: Temporary in-memory processing with cleanup
4. **Google Drive Persistence**: All user data stored in personal Drive
5. **Microservice-Ready**: Clean service boundaries for future scaling

## Installation and Setup

### Prerequisites

- **Python 3.10-3.11** (Python 3.12+ has compatibility issues)
- **Node.js 18+** with npm
- **PostgreSQL 14+** for metadata storage
- **Docker & Docker Compose** (optional for containerised deployment)
- **Google Cloud Project** with OAuth 2.0 credentials configured

### Development Environment

#### 1. Clone Repository

```bash
git clone https://github.com/yusufmo1/guardian.git
cd guardian
```

#### 2. Backend Configuration

```bash
# Create Virtual Environment
cd backend
python3.10 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Configure Environment
cp .env.example .env
# Edit .env with your configuration (see Configuration section)

# Start PostgreSQL with Docker
docker run --name guardian-postgres \
  -e POSTGRES_DB=guardian \
  -e POSTGRES_USER=guardian \
  -e POSTGRES_PASSWORD=guardian_pass \
  -p 5432:5432 -d postgres:14

# Run backend server (from guardian/backend directory)
python main.py  # Runs on http://localhost:5051

# Alternative: Run from guardian root directory
cd ..  # Go back to guardian root
python -m backend.main  # Runs on http://localhost:5051
```

#### 3. Frontend Configuration

```bash
# Install Dependencies
cd ../frontend
npm install

# Start development server
npm run dev  # Runs on http://localhost:3000
```

#### 4. Access the Application

Open `http://localhost:3000` in your browser. The frontend will proxy API requests to the backend.

### Production Environment

```bash
# Automated deployment
cd guardian
./scripts/deploy.sh

# Or using Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## API Documentation

### Authentication Endpoints

```bash
# Initialize Google OAuth flow
POST /auth/google/initiate
Content-Type: application/json
{
  "redirect_uri": "http://localhost:3000/auth/callback"
}

# Validate session
GET /auth/validate
Cookie: session_token=<token>

# Get user profile
GET /auth/user
Cookie: session_token=<token>
```

### Analysis Endpoints

```bash
# Initialize user session
POST /api/session/initialize
Cookie: session_token=<token>

# Upload document
POST /api/session/documents/upload
Cookie: session_token=<token>
Content-Type: multipart/form-data
file: <file>

# Analyse Protocol
POST /api/session/analyze
Cookie: session_token=<token>
Content-Type: application/json
{
  "query": "Analyse this protocol for GMP compliance",
  "document_ids": ["doc_123"],
  "analysis_type": "comprehensive"
}

# Generate report
POST /api/reports/generate
Cookie: session_token=<token>
Content-Type: application/json
{
  "analysis_id": "analysis_123",
  "format": "pdf",
  "include_visualizations": true
}
```

### Example Implementation

```python
import requests

# Authenticate
session = requests.Session()
response = session.post('http://localhost:5051/auth/google/callback', 
                       json={'code': google_auth_code})

# Initialise Session
session.post('http://localhost:5051/api/session/initialize')

# Upload document
with open('protocol.pdf', 'rb') as f:
    files = {'file': f}
    response = session.post('http://localhost:5051/api/session/documents/upload', 
                          files=files)
    document_id = response.json()['document']['id']

# Analyse for Compliance
analysis = session.post('http://localhost:5051/api/session/analyze',
                       json={
                           'query': 'Check GMP compliance',
                           'document_ids': [document_id]
                       })
```

## Configuration

### Required Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://guardian:guardian_pass@localhost:5432/guardian

# Google OAuth 2.0 (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback

# Security
SECRET_KEY=your-super-secret-key-for-production
SESSION_SECRET=your-session-secret-key
SESSION_DURATION_HOURS=24

# LLM Integration
LLM_API_URL=http://localhost:1234/v1/chat/completions
LLM_MODEL_NAME=qwen3-30b-a3b@q4_M

# ML Configuration
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu  # cpu | cuda | mps

# Server Configuration
FLASK_ENV=development
API_HOST=localhost
API_PORT=5051
```

### Google Cloud Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Google Drive API and Google+ API
3. Create OAuth 2.0 credentials (Web application type)
4. Add authorised redirect URIs:
   - `http://localhost:3000/auth/callback` (development)
   - `https://yourdomain.com/auth/callback` (production)
5. Download credentials and add to `.env`

## Technical Specifications

### ML Pipeline

1. **Document Processing**: Intelligent chunking for pharmaceutical documents
2. **Embedding Generation**: SentenceTransformer with GPU acceleration
3. **Vector Storage**: FAISS indexes stored in user's Google Drive
4. **Similarity Search**: Cosine similarity with configurable thresholds
5. **LLM Analysis**: Context-aware compliance checking with structured prompts

### Security Features

- **OAuth 2.0**: Industry-standard authentication
- **Token Encryption**: Fernet encryption for Google tokens
- **Session Management**: Secure session tokens with configurable expiry
- **CORS Protection**: Configurable cross-origin policies
- **Input Validation**: Pydantic models for all API endpoints
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterised queries

### Frontend Technology Stack

- **Framework**: SvelteKit 5.34.7 with TypeScript 5.8.3
- **Build Tool**: Vite for optimised development
- **Styling**: CSS custom properties design system
- **Icons**: Lucide Svelte with TypeScript-safe wrapper system
- **Charts**: Plotly.js for data visualisations
- **State Management**: Svelte stores with reactive patterns

## Performance Metrics

- **Embedding Generation**: ~100 documents/minute (CPU), ~500 documents/minute (GPU)
- **Vector Search**: <100ms for 10k documents
- **Report Generation**: 2-5 seconds for comprehensive PDF
- **Frontend Build**: <10 seconds production build
- **API Response Time**: <200ms average (excluding ML operations)

## Docker Deployment

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production

```bash
# Build and deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Health check
./scripts/health-check.sh

# View metrics
docker-compose exec backend curl http://localhost:9090/metrics
```

## Technical Implementation Details

### System Extension Architecture

1. **Backend Services**: Service layer in `backend/services/`, routing in `backend/api/routes/`
2. **Frontend Components**: Component library in `frontend/src/lib/components/` with reactive store management
3. **Database Models**: SQLAlchemy ORM models in `backend/models/` with migration support
4. **API Validation**: Pydantic schemas in `backend/api/schemas/` for request/response validation



## Academic Context

This system was developed as one of two complementary implementations demonstrating AI integration into electronic laboratory notebooks. Together with the SMILES2SPEC molecular spectral prediction system, it forms the technical foundation of the dissertation "Integrating AI into Electronic Lab Notebooks" submitted for the MSc AI in Biosciences programme at Queen Mary University of London.

## Citation

For academic use of this work, please cite:

```bibtex
@mastersthesis{mohammed2025guardian,
  title = {GUARDIAN: Privacy-First Pharmaceutical Compliance Analysis System for Electronic Laboratory Notebooks},
  author = {Mohammed, Yusuf},
  year = {2025},
  school = {Queen Mary University of London},
  department = {MSc AI in Biosciences},
  supervisor = {Elbadawi, Mohammed},
  note = {MSc Dissertation Project: Integrating AI into Electronic Lab Notebooks}
}
```

---

<div align="center">

[![Author](https://img.shields.io/badge/Author-Yusuf%20Mohammed-blue?style=flat-square&logo=github)](https://github.com/yusufmo1)
[![Supervisor](https://img.shields.io/badge/Supervisor-Dr%20Mohammed%20Elbadawi-green?style=flat-square&logo=github)](https://github.com/Dr-M-ELBA)
[![Institution](https://img.shields.io/badge/Institution-QMUL-003E74?style=flat-square)](https://www.qmul.ac.uk/)
[![Programme](https://img.shields.io/badge/Programme-MSc%20AI%20in%20Biosciences-purple?style=flat-square)](https://www.qmul.ac.uk/)

</div>

*Developed as part of MSc AI in Biosciences dissertation at Queen Mary University of London (2025)*