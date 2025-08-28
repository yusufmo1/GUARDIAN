# GUARDIAN Data Flow Architecture - Fixed Diagrams

## Privacy-First Architecture Overview

GUARDIAN implements a **privacy-first architecture** where user data never touches our servers permanently. All sensitive user data resides in the user's personal Google Drive, while our PostgreSQL database only stores session metadata and authentication tokens.

## Privacy-First Data Flow Architecture

### High-Level System Architecture

```mermaid
graph TB
    Title[High-Level System Arch]
    Title --> UI[SvelteKit Frontend :3000]
    
    UI --> API[Flask Backend :5051]
    API --> PG[(PostgreSQL<br/>Metadata Only)]
    API --> GDrive[User's Google Drive]
    API --> LLM[LLM Service]
    UI --> Google[Google OAuth]
    
    GDrive --> Docs[Documents]
    GDrive --> VDB[Vector DB]
    GDrive --> Analysis[Analysis Results]
    GDrive --> Chat[Chat History]
    GDrive --> Reports[Reports]
    
    API --> RAM[RAM Cache]
    API --> Session[Sessions]
    
    PG --> AuthData[Auth Records]
    PG --> SessionData[Session Metadata]
    PG --> DocMeta[Doc Metadata]
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style GDrive fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style PG fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style RAM fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
    style UI fill:#6600cc,stroke:#330066,stroke-width:3px,color:#fff
    style API fill:#009900,stroke:#004400,stroke-width:3px,color:#fff
    style LLM fill:#666666,stroke:#333333,stroke-width:3px,color:#fff
    style Google fill:#4285f4,stroke:#1a73e8,stroke-width:3px,color:#fff
    style Docs fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style VDB fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style Analysis fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style Chat fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style Reports fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
```

## Data Flow Components

### 1. Frontend (SvelteKit) - Port 3000
**Purpose:** User interface and client-side state management
**Data Stored:** 
- Session tokens (localStorage)
- UI state (Svelte stores)
- No sensitive user data

### 2. Backend (Flask) - Port 5051
**Purpose:** API orchestration and session management
**Data Stored:**
- **TEMPORARY ONLY**: Active vector databases in RAM during user sessions
- **NO PERMANENT STORAGE** of user documents or analysis results

### 3. PostgreSQL Database
**Purpose:** Metadata and session coordination only
**Data Stored:**
```sql
-- User authentication metadata
users: {
  id, google_id, email, encrypted_drive_tokens, created_at
}

-- Session tracking metadata  
sessions: {
  id, user_id, session_token_hash, expires_at, created_at
}

-- Vector database session metadata
vector_sessions: {
  id, user_id, session_id, status, drive_file_id, created_at
}

-- Document metadata (NO CONTENT)
documents: {
  id, user_id, filename, file_size, drive_file_id, processed_at
}

-- Chat session metadata (NO MESSAGES)
chat_sessions: {
  id, user_id, session_id, drive_backup_id, created_at
}
```

### 4. User's Google Drive
**Purpose:** Private data storage and persistence
**Data Stored:**
```
/GUARDIAN_Data/
├── Documents/              # User uploaded files
├── Vector_Database/        # FAISS indexes and embeddings
├── Analysis_Results/       # Compliance analysis outputs
├── Chat_History/          # LLM conversation history
├── Reports/               # Generated PDF/HTML reports
└── Session_Data/          # Session backups and metadata
```

### 5. Temporary Processing (RAM)
**Purpose:** Active session processing
**Data Stored:**
- Vector databases loaded from user's Drive
- Document chunks and embeddings during processing
- **Automatically cleaned up when session expires**

## Detailed Data Flows

### Authentication Flow

```mermaid
graph TB
    Title[Authentication Flow]
    Title --> Start([User Clicks Sign In])
    Start --> InitAuth[Frontend: POST /auth/google/initiate]
    InitAuth --> GenURL[Backend: Generate OAuth URL + CSRF]
    GenURL --> ReturnURL[Return Auth URL to Frontend]
    ReturnURL --> Redirect[Redirect to Google OAuth]
    
    Redirect --> UserAuth[User Authorizes GUARDIAN]
    UserAuth --> Callback[Google Redirects with Code]
    Callback --> Exchange[Backend: Exchange Code for Tokens]
    
    Exchange --> Encrypt[Backend: Encrypt Tokens with Fernet]
    Encrypt --> StoreUser[Store User + Encrypted Tokens in DB]
    StoreUser --> CreateSession[Create Session Token Hash]
    CreateSession --> ReturnSession[Return Session to Frontend]
    
    ReturnSession --> StoreLocal[Frontend: Store in localStorage]
    StoreLocal --> VerifyDrive[Verify Drive Access]
    VerifyDrive --> Complete([Authentication Complete])
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Start fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Complete fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Encrypt fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
    style StoreUser fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style Redirect fill:#4285f4,stroke:#1a73e8,stroke-width:3px,color:#fff
    style UserAuth fill:#4285f4,stroke:#1a73e8,stroke-width:3px,color:#fff
```

### Document Upload & Processing Flow

```mermaid
graph TB
    Title[Document Upload & Processing Flow]
    Title --> Start([User Uploads Document])
    Start --> Upload[Frontend: POST /api/documents/upload]
    Upload --> Verify[Backend: Verify Session Token]
    Verify --> LoadDoc[Load Document to RAM]
    
    LoadDoc --> Extract[Extract Text Content]
    Extract --> Chunk[Chunk by EP Sections]
    Chunk --> Embed[Generate Embeddings]
    
    Embed --> SaveOrig[Save Original to Drive]
    Embed --> SaveMeta[Save Metadata to DB]
    Embed --> UpdateVDB[Update Session VDB]
    
    SaveOrig --> Confirm1[Drive: Confirm Saved]
    SaveMeta --> Confirm2[DB: Metadata Only]
    UpdateVDB --> Confirm3[RAM: VDB Updated]
    
    Confirm1 --> Success
    Confirm2 --> Success
    Confirm3 --> Success[Return Success to Frontend]
    
    Success --> Clear[Clear Document from RAM]
    Clear --> Complete([Processing Complete])
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Start fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Complete fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style SaveMeta fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style SaveOrig fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style Clear fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
    style LoadDoc fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
    style UpdateVDB fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
```

### Protocol Compliance Analysis Flow

```mermaid
graph TB
    Title[Protocol Compliance Analysis Flow]
    Title --> Start([User Submits Protocol])
    Start --> Submit[Frontend: POST /api/analyze]
    Submit --> Search[Backend: Search Similar in VDB]
    Search --> TopK[Get Top-K Similar Docs]
    
    TopK --> Context[Build Compliance Context]
    Context --> LLMCall[Send to LLM Service]
    LLMCall --> Results[Receive Analysis Results]
    
    Results --> SaveResults[Save to User's Drive]
    Results --> ReturnUser[Return to Frontend]
    
    SaveResults --> DriveConfirm[Drive: Analysis Saved]
    ReturnUser --> Display[Display Results to User]
    
    DriveConfirm --> Complete([Analysis Complete])
    Display --> Complete
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Start fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Complete fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style SaveResults fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style LLMCall fill:#666666,stroke:#333333,stroke-width:3px,color:#fff
    style Search fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
```

### AI Chat Flow

```mermaid
graph TB
    Title[AI Chat Flow]
    Title --> Start([User Types Message])
    Start --> Send[Frontend: POST /api/chat/send]
    Send --> SearchCtx[Backend: Search Relevant Context]
    SearchCtx --> LoadHist[Load Chat History from Drive]
    
    LoadHist --> BuildPrompt[Build Contextual Prompt]
    BuildPrompt --> LLMChat[Send to LLM Service]
    LLMChat --> Response[Receive AI Response]
    
    Response --> SaveChat[Append to Chat History]
    Response --> ReturnResp[Return Response to Frontend]
    
    SaveChat --> DriveChat[Drive: Chat Saved]
    ReturnResp --> ShowUser[Display to User]
    
    DriveChat --> Complete([Chat Complete])
    ShowUser --> Complete
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Start fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Complete fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style SaveChat fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style LLMChat fill:#666666,stroke:#333333,stroke-width:3px,color:#fff
    style LoadHist fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style SearchCtx fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
```

### Session Cleanup & Privacy Protection Flow

```mermaid
graph TB
    Title[Session Cleanup & Privacy Protection Flow]
    Title --> Start{Session End Trigger}
    Start --> |Logout| Logout[User Logout]
    Start --> |Timeout| Timeout[24hr Timeout]
    
    Logout --> InitClean[Initiate Cleanup]
    Timeout --> InitClean
    
    InitClean --> ExtractVDB[Extract Current VDB]
    ExtractVDB --> BackupDrive[Backup to User's Drive]
    
    InitClean --> ClearRAM[Delete ALL from RAM]
    InitClean --> UpdateDB[Update Session Status]
    
    BackupDrive --> DriveOK[Drive: Backup Complete]
    ClearRAM --> RAMOK[RAM: Fully Cleared]
    UpdateDB --> DBOK[DB: Status = cleaned_up]
    
    DriveOK --> Verify
    RAMOK --> Verify
    DBOK --> Verify[Verify Cleanup]
    
    Verify --> Complete([Privacy Guaranteed])
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Start fill:#ffcc00,stroke:#cc9900,stroke-width:3px,color:#000
    style Complete fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style ClearRAM fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
    style BackupDrive fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style UpdateDB fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
```

## Privacy Guarantees

### What NEVER Leaves User's Google Drive
- **Document content** (PDFs, text files, etc.)
- **Analysis results** (compliance findings, reports)
- **Chat conversations** (LLM conversations and history)
- **Vector databases** (embeddings and search indexes)
- **Generated reports** (PDF/HTML outputs)

### What's Stored in Our PostgreSQL (Metadata Only)
- **User profile** (Google ID, email, encrypted Drive tokens)
- **Session tracking** (session IDs, expiration times)
- **Document metadata** (filenames, file sizes, Drive file IDs)
- **System logs** (errors, performance metrics)

### What's Temporarily in Backend Memory
- **Active vector databases** (loaded during user session)
- **Processing buffers** (document chunks during upload)
- **Search results** (similarity search outputs)
- **Automatically cleaned up** when session ends

## Security & Compliance

### Data Encryption
- **In Transit**: All API calls use HTTPS/TLS
- **At Rest (Drive)**: Google Drive's encryption
- **At Rest (Database)**: Encrypted OAuth tokens using Fernet
- **In Memory**: Temporary processing only

### Access Control
- **OAuth 2.0**: Industry standard authentication
- **Session-based**: Temporary session tokens
- **User isolation**: Complete separation between users
- **Drive permissions**: Users control their own data

### Compliance Features
- **GDPR Ready**: User data in their own Drive
- **Right to deletion**: User deletes their own Drive folder
- **Data portability**: User owns all data in standard formats
- **Audit trails**: PostgreSQL logs access patterns only

## Deployment Architecture

### Production Deployment Architecture

```mermaid
graph TB
    Title[Production Deployment Architecture]
    Title --> CDN[Cloudflare/CloudFront]
    
    CDN --> LB[Load Balancer]
    LB --> App1[Flask Container 1]
    LB --> App2[Flask Container 2]
    LB --> AppN[Flask Container N]
    
    App1 --> DB[(PostgreSQL<br/>Metadata Only)]
    App2 --> DB
    AppN --> DB
    
    App1 --> Google[Google APIs]
    App2 --> Google
    AppN --> Google
    
    App1 --> LLM[LLM Service]
    App2 --> LLM
    AppN --> LLM
    
    Google -.-> Drive1[User 1 Drive]
    Google -.-> Drive2[User 2 Drive]
    Google -.-> DriveN[User N Drive]
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Drive1 fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style Drive2 fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style DriveN fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style DB fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style CDN fill:#9933cc,stroke:#660099,stroke-width:3px,color:#fff
    style LB fill:#009900,stroke:#006600,stroke-width:3px,color:#fff
    style Google fill:#4285f4,stroke:#1a73e8,stroke-width:3px,color:#fff
    style LLM fill:#666666,stroke:#333333,stroke-width:3px,color:#fff
```

### Local Development Architecture

```mermaid
graph TB
    Title[Local Development Architecture]
    Title --> Frontend[Frontend]
    
    Frontend --> Vite[Vite Server<br/>:3000]
    
    Title --> Backend[Backend]
    Backend --> Flask[Flask Dev<br/>:5051]
    
    Title --> Database[Database]
    Database --> PG[PostgreSQL<br/>:5432]
    
    Title --> TestServices[Test Services]
    TestServices --> TestLLM[Local LLM<br/>:1234]
    
    Title --> TestGoogle[Test Google]
    TestGoogle --> TestDrive[Test Drive]
    
    Vite -.->|Proxy| Flask
    Flask --> PG
    Flask --> TestLLM
    Flask -.->|OAuth| TestDrive
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style TestDrive fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style PG fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style Vite fill:#6600cc,stroke:#330066,stroke-width:3px,color:#fff
    style Flask fill:#009900,stroke:#004400,stroke-width:3px,color:#fff
    style TestLLM fill:#666666,stroke:#333333,stroke-width:3px,color:#fff
```

## Performance Characteristics

### Response Times
- **Authentication**: ~500ms (OAuth exchange)
- **Document upload**: ~2-5s (depending on file size)
- **Analysis**: ~3-8s (LLM processing time)
- **Search**: ~100-300ms (FAISS vector search)
- **Chat**: ~2-4s (LLM response time)

### Scalability
- **Users**: Unlimited (data in their own Drives)
- **Documents per user**: Limited by their Google Drive quota
- **Concurrent sessions**: Limited by backend memory/CPU
- **Database size**: Minimal (metadata only)

### Storage Efficiency
- **Backend storage**: Near zero (temporary processing only)
- **Database size**: ~1KB per user (metadata only)
- **User data**: Stored in their 15GB+ Google Drive quota
- **Vector databases**: Compressed and stored in user's Drive

## Privacy-First Architecture Flow

```mermaid
graph TB
    Title[Privacy-First Architecture]
    Title --> UserAction[User Action Initiated]
    
    UserAction --> DataType{What Type of Data?}
    
    DataType -->|Documents| DocPath[Document Processing Path]
    DataType -->|Analysis| AnalysisPath[Analysis Processing Path]
    DataType -->|Chat| ChatPath[Chat Processing Path]
    DataType -->|Auth| AuthPath[Authentication Path]
    
    DocPath --> TempRAM1[Load to RAM Temporarily]
    TempRAM1 --> Process1[Process in Memory]
    Process1 --> SaveDrive1[Save to User's Drive]
    SaveDrive1 --> ClearRAM1[Clear from RAM]
    
    AnalysisPath --> TempRAM2[Load Context to RAM]
    TempRAM2 --> LLMProcess[Send to LLM Service]
    LLMProcess --> SaveDrive2[Save Results to Drive]
    SaveDrive2 --> ClearRAM2[Clear from RAM]
    
    ChatPath --> TempRAM3[Load History from Drive]
    TempRAM3 --> ChatProcess[Process with LLM]
    ChatProcess --> SaveDrive3[Update Chat in Drive]
    SaveDrive3 --> ClearRAM3[Clear from RAM]
    
    AuthPath --> EncryptTokens[Encrypt OAuth Tokens]
    EncryptTokens --> SaveMeta[Save Metadata Only to DB]
    
    ClearRAM1 --> PrivacyCheck
    ClearRAM2 --> PrivacyCheck
    ClearRAM3 --> PrivacyCheck
    SaveMeta --> PrivacyCheck
    
    PrivacyCheck{Privacy Verification}
    PrivacyCheck -->|Backend Memory| NoUserData[NO User Data Retained]
    PrivacyCheck -->|Database| OnlyMetadata[ONLY Metadata Stored]
    PrivacyCheck -->|User's Drive| AllUserData[ALL User Data Preserved]
    
    NoUserData --> FinalGuarantee
    OnlyMetadata --> FinalGuarantee
    AllUserData --> FinalGuarantee
    
    FinalGuarantee[Complete Privacy Maintained:<br/>User Owns All Their Data]
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style FinalGuarantee fill:#00cc00,stroke:#006600,stroke-width:4px,color:#fff
    style NoUserData fill:#cc0066,stroke:#660033,stroke-width:3px,color:#fff
    style OnlyMetadata fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style AllUserData fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style TempRAM1 fill:#cc0066,stroke:#660033,stroke-width:2px,color:#fff
    style TempRAM2 fill:#cc0066,stroke:#660033,stroke-width:2px,color:#fff
    style TempRAM3 fill:#cc0066,stroke:#660033,stroke-width:2px,color:#fff
    style ClearRAM1 fill:#cc0066,stroke:#660033,stroke-width:2px,color:#fff
    style ClearRAM2 fill:#cc0066,stroke:#660033,stroke-width:2px,color:#fff
    style ClearRAM3 fill:#cc0066,stroke:#660033,stroke-width:2px,color:#fff
    style SaveDrive1 fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style SaveDrive2 fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style SaveDrive3 fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style EncryptTokens fill:#666666,stroke:#333333,stroke-width:2px,color:#fff
    style SaveMeta fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
```

### Ground Truth vs Protocol Query Flow (Two-Tier Document System)

```mermaid
graph TB
    Title[Ground Truth vs Protocol Query Flow]
    Title --> Start([User Workflow Start])
    
    Start --> Phase1[Phase 1: Upload Ground Truth Documents]
    Phase1 --> GTUpload[Upload European Pharmacopoeia Standards]
    GTUpload --> GTClassify[Backend: Classify as document_type='ground_truth']
    GTClassify --> GTFolder[Store in Drive: /Ground_Truth_Standards/]
    GTFolder --> GTEmbedding[Generate Embeddings with Type Metadata]
    GTEmbedding --> GTVectorDB[Add to User VectorDB with Type Filters]
    
    GTVectorDB --> Phase2[Phase 2: Upload Protocol Documents]
    Phase2 --> ProtUpload[Upload User Protocols to Analyze]
    ProtUpload --> ProtClassify[Backend: Classify as document_type='protocol']
    ProtClassify --> ProtFolder[Store in Drive: /User_Protocols/]
    ProtFolder --> ProtEmbedding[Generate Embeddings with Type Metadata]
    ProtEmbedding --> ProtVectorDB[Add to User VectorDB with Type Filters]
    
    ProtVectorDB --> Phase3[Phase 3: Protocol Analysis Against Ground Truth]
    Phase3 --> QueryInit[User: Analyze Protocol Against Standards]
    QueryInit --> TypeFilter[Backend: Apply Document Type Filtering]
    
    TypeFilter --> GTOnlySearch[Search ONLY Ground Truth Documents]
    GTOnlySearch --> EuroPharm[Filter: European Pharmacopoeia Categories]
    EuroPharm --> USPStandards[Filter: USP Standards]
    USPStandards --> ICHGuidelines[Filter: ICH Guidelines]
    ICHGuidelines --> TopKResults[Get Top-K Relevant Standards]
    
    TopKResults --> ContextBuild[Build Compliance Context]
    ContextBuild --> LLMAnalysis[LLM: Analyze Protocol vs Standards]
    LLMAnalysis --> ComplianceReport[Generate Compliance Assessment]
    
    ComplianceReport --> SaveResults[Save Analysis Results to Drive]
    ComplianceReport --> UserResults[Return Detailed Analysis to User]
    
    SaveResults --> ResultsFolder[Drive: /Analysis_Results/]
    UserResults --> DisplayUI[Frontend: Display Compliance Findings]
    
    ResultsFolder --> Complete([Analysis Complete])
    DisplayUI --> Complete
    
    %% Styling for different document types
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Start fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Complete fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    
    %% Ground Truth styling (Blue)
    style Phase1 fill:#0066cc,stroke:#003366,stroke-width:3px,color:#fff
    style GTUpload fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style GTClassify fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style GTFolder fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style GTEmbedding fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style GTVectorDB fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    
    %% Protocol styling (Orange)
    style Phase2 fill:#ff6600,stroke:#cc3300,stroke-width:3px,color:#fff
    style ProtUpload fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style ProtClassify fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style ProtFolder fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style ProtEmbedding fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style ProtVectorDB fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    
    %% Analysis styling (Purple)
    style Phase3 fill:#6600cc,stroke:#330066,stroke-width:3px,color:#fff
    style QueryInit fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style TypeFilter fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style GTOnlySearch fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style ContextBuild fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style LLMAnalysis fill:#666666,stroke:#333333,stroke-width:2px,color:#fff
    style ComplianceReport fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    
    %% Results styling (Green)
    style SaveResults fill:#009900,stroke:#006600,stroke-width:2px,color:#fff
    style UserResults fill:#009900,stroke:#006600,stroke-width:2px,color:#fff
    style ResultsFolder fill:#009900,stroke:#006600,stroke-width:2px,color:#fff
    style DisplayUI fill:#009900,stroke:#006600,stroke-width:2px,color:#fff
```

### Document Type Classification Flow

```mermaid
graph TB
    Title[Document Type Classification Flow]
    Title --> Upload[Document Upload Request]
    
    Upload --> TypeCheck{Document Type Specified?}
    TypeCheck -->|Yes| Validate[Validate Document Type]
    TypeCheck -->|No| DefaultType[Default: document_type='protocol']
    
    Validate --> ValidTypes{Valid Type?}
    ValidTypes -->|ground_truth| GTPath[Ground Truth Processing Path]
    ValidTypes -->|protocol| ProtPath[Protocol Processing Path]
    ValidTypes -->|reference| RefPath[Reference Processing Path]
    ValidTypes -->|analysis_result| AnalysisPath[Analysis Result Processing Path]
    ValidTypes -->|Invalid| Error[Return Validation Error]
    
    DefaultType --> ProtPath
    
    GTPath --> GTCategories[Apply Ground Truth Categories]
    ProtPath --> ProtCategories[Apply Protocol Categories] 
    RefPath --> RefCategories[Apply Reference Categories]
    AnalysisPath --> AnalysisCategories[Apply Analysis Categories]
    
    GTCategories --> GTSubcategory{Subcategory?}
    GTSubcategory -->|european_pharmacopoeia| EPGT[European Pharmacopoeia Standards]
    GTSubcategory -->|usp_standard| USPGT[USP Standards]
    GTSubcategory -->|ich_guideline| ICHGT[ICH Guidelines]
    GTSubcategory -->|fda_guidance| FDAGT[FDA Guidance Documents]
    GTSubcategory -->|ema_guideline| EMAGT[EMA Guidelines]
    GTSubcategory -->|other| OtherGT[Other Ground Truth]
    
    ProtCategories --> ProtSubcategory{Subcategory?}
    ProtSubcategory -->|analytical_method| AnalyticalProt[Analytical Methods]
    ProtSubcategory -->|quality_control| QCProt[Quality Control Protocols]
    ProtSubcategory -->|stability_testing| StabilityProt[Stability Testing]
    ProtSubcategory -->|other| OtherProt[Other Protocols]
    
    EPGT --> DriveOrg[Organize in Google Drive by Type]
    USPGT --> DriveOrg
    ICHGT --> DriveOrg
    FDAGT --> DriveOrg
    EMAGT --> DriveOrg
    OtherGT --> DriveOrg
    
    AnalyticalProt --> DriveOrg
    QCProt --> DriveOrg
    StabilityProt --> DriveOrg
    OtherProt --> DriveOrg
    
    RefCategories --> DriveOrg
    AnalysisCategories --> DriveOrg
    
    DriveOrg --> Metadata[Add Type Metadata to Embeddings]
    Metadata --> VectorStore[Store in User Vector Database]
    VectorStore --> Success[Classification Complete]
    
    Error --> End([End])
    Success --> End
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style Success fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    style Error fill:#cc0000,stroke:#660000,stroke-width:3px,color:#fff
    style End fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    
    %% Ground Truth (Blue)
    style GTPath fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style EPGT fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style USPGT fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style ICHGT fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style FDAGT fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style EMAGT fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    
    %% Protocols (Orange)
    style ProtPath fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style AnalyticalProt fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style QCProt fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style StabilityProt fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    
    %% References (Gray)
    style RefPath fill:#666666,stroke:#333333,stroke-width:2px,color:#fff
    
    %% Analysis (Purple)
    style AnalysisPath fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
```

### Vector Search with Document Type Filtering

```mermaid
graph TB
    Title[Vector Search with Document Type Filtering]
    Title --> SearchReq[User Search Request]
    
    SearchReq --> FilterType{Search Type?}
    FilterType -->|All Documents| AllSearch[Search All Document Types]
    FilterType -->|Ground Truth Only| GTSearch[Filter: document_type='ground_truth']
    FilterType -->|Protocols Only| ProtSearch[Filter: document_type='protocol']
    FilterType -->|Specific Categories| CatSearch[Filter by Document Categories]
    
    GTSearch --> GTCategories{Specific GT Categories?}
    GTCategories -->|European Pharmacopoeia| EPFilter[Filter: category='european_pharmacopoeia']
    GTCategories -->|USP Standards| USPFilter[Filter: category='usp_standard']
    GTCategories -->|ICH Guidelines| ICHFilter[Filter: category='ich_guideline']
    GTCategories -->|All Ground Truth| AllGTFilter[No Category Filter]
    
    ProtSearch --> ProtCategories{Specific Prot Categories?}
    ProtCategories -->|Analytical Methods| AnalyticalFilter[Filter: category='analytical_method']
    ProtCategories -->|Quality Control| QCFilter[Filter: category='quality_control']
    ProtCategories -->|All Protocols| AllProtFilter[No Category Filter]
    
    AllSearch --> EmbedQuery[Generate Query Embedding]
    EPFilter --> EmbedQuery
    USPFilter --> EmbedQuery
    ICHFilter --> EmbedQuery
    AllGTFilter --> EmbedQuery
    AnalyticalFilter --> EmbedQuery
    QCFilter --> EmbedQuery
    AllProtFilter --> EmbedQuery
    CatSearch --> EmbedQuery
    
    EmbedQuery --> VectorSearch[Perform Vector Similarity Search]
    VectorSearch --> MetadataFilter[Apply Document Type & Category Filters]
    MetadataFilter --> ScoreBoost[Apply Type-Based Score Boosting]
    
    ScoreBoost --> PriorityLogic{Apply Priority Logic}
    PriorityLogic -->|Ground Truth Match| GTBoost[+0.6 Boost Score]
    PriorityLogic -->|Protocol Match| ProtBoost[+0.4 Boost Score] 
    PriorityLogic -->|Reference Match| RefBoost[+0.2 Boost Score]
    
    GTBoost --> CategoryBoost{Category Boost?}
    CategoryBoost -->|European Pharmacopoeia| EPBoost[+0.3 Additional Boost]
    CategoryBoost -->|Regulatory Standard| RegBoost[+0.2 Additional Boost]
    CategoryBoost -->|Other| NoBoost[No Additional Boost]
    
    ProtBoost --> CategoryBoost
    RefBoost --> CategoryBoost
    EPBoost --> FinalScore[Calculate Final Relevance Score]
    RegBoost --> FinalScore
    NoBoost --> FinalScore
    
    FinalScore --> RankResults[Rank by Final Score]
    RankResults --> TopK[Return Top-K Results with Type Info]
    TopK --> UserDisplay[Display Results with Type Indicators]
    
    style Title fill:#000000,stroke:#000000,stroke-width:3px,color:#fff
    style UserDisplay fill:#00cc00,stroke:#006600,stroke-width:3px,color:#fff
    
    %% Ground Truth (Blue)
    style GTSearch fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style EPFilter fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style USPFilter fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style ICHFilter fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style GTBoost fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    style EPBoost fill:#0066cc,stroke:#003366,stroke-width:2px,color:#fff
    
    %% Protocols (Orange)
    style ProtSearch fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style AnalyticalFilter fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style QCFilter fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    style ProtBoost fill:#ff6600,stroke:#cc3300,stroke-width:2px,color:#fff
    
    %% Search Processing (Purple)
    style VectorSearch fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style MetadataFilter fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style ScoreBoost fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style FinalScore fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
    style RankResults fill:#6600cc,stroke:#330066,stroke-width:2px,color:#fff
```

## Document Type Architecture Summary

The ground truth vs protocol query system implements a **two-tier document classification** that enables targeted pharmaceutical compliance analysis:

### Document Type Hierarchy
1. **Ground Truth Documents** (`document_type='ground_truth'`)
   - European Pharmacopoeia standards
   - USP monographs and standards
   - ICH guidelines
   - FDA guidance documents
   - EMA guidelines

2. **Protocol Documents** (`document_type='protocol'`)
   - User-uploaded analytical methods
   - Quality control procedures
   - Stability testing protocols
   - Manufacturing procedures

3. **Reference Documents** (`document_type='reference'`)
   - Supporting documentation
   - Additional reference materials

4. **Analysis Results** (`document_type='analysis_result'`)
   - Generated compliance reports
   - AI analysis outputs

### Query Flow Benefits
- **Targeted Analysis**: Protocols analyzed specifically against regulatory standards
- **Relevance Scoring**: Ground truth documents receive priority in similarity matching
- **Type-Aware Search**: Filter searches by document type and category
- **Compliance Context**: LLM receives proper regulatory context for analysis
- **Organized Storage**: Type-based folder structure in user's Google Drive

### Privacy Preservation
- **Complete User Isolation**: Each user's documents remain in their personal Google Drive
- **Type-Based Organization**: Documents organized by type in user's Drive folders
- **Metadata-Only Database**: Only document type information stored in PostgreSQL
- **Temporary Processing**: All document content processed in RAM only

This architecture ensures complete user privacy while providing powerful AI-powered pharmaceutical compliance analysis capabilities.