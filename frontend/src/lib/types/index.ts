// GUARDIAN Frontend Type Definitions

/// <reference lib="es2022" />
/// <reference lib="dom" />

export interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: DocumentStatus;
  analysisId?: string;
}

// Interface for documents displayed in GroundTruthManager and similar components
// This matches the structure expected by the component filtering and sorting logic
export interface DocumentInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  modifiedTime?: string; // For compatibility with Google Drive modified_time
  status: DocumentStatus;
  analysisId?: string;
}

export type DocumentStatus = 'uploading' | 'processing' | 'completed' | 'error';

export interface AnalysisResult {
  id: string;
  documentId: string;
  status: AnalysisStatus;
  complianceScore: number;
  findings: ComplianceFinding[];
  recommendations: string[];
  createdAt: Date;
  completedAt?: Date;
}

export type AnalysisStatus = 'pending' | 'processing' | 'completed' | 'error';

export interface ComplianceFinding {
  id: string;
  section: string;
  requirement: string;
  status: ComplianceStatus;
  description: string;
  severity: ComplianceSeverity;
  reference?: string;
}

export type ComplianceStatus = 'compliant' | 'non-compliant' | 'partial' | 'needs-review';
export type ComplianceSeverity = 'critical' | 'major' | 'minor' | 'info';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  documentContext?: string;
  analysisContext?: string;
}

export interface ChatSession {
  id: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface VectorSearchResult {
  id: string;
  text: string;
  similarity: number;
  metadata: {
    section: string;
    page?: number;
    chapter?: string;
  };
}

// Basic API Response Type (for simple operations)
export interface BasicApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface UploadProgress {
  documentId: string;
  progress: number;
  stage: UploadStage;
  message?: string;
}

export type UploadStage = 
  | 'uploading'
  | 'extracting'
  | 'chunking'
  | 'embedding'
  | 'indexing'
  | 'completed'
  | 'error';

export interface AppSettings {
  apiUrl: string;
  theme: 'light' | 'dark' | 'auto';
  notifications: boolean;
  autoAnalysis: boolean;
}

export interface NavigationItem {
  label: string;
  href: string;
  icon?: string;
  active?: boolean;
}

// UI Component Props
export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
}

export interface ModalProps {
  open: boolean;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  closable?: boolean;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: number;
  actions?: ToastAction[];
}

export interface ToastAction {
  label: string;
  action: () => void;
}

// Store Types
export interface AppState {
  loading: boolean;
  error: string | null;
  settings: AppSettings;
  user: User | null;
}

export interface DocumentState {
  documents: Document[];
  uploading: UploadProgress[];
  selected: string | null;
  currentUserId: string | null;
}

export interface AnalysisState {
  results: AnalysisResult[];
  current: AnalysisResult | null;
  processing: boolean;
  currentUserId: string | null;
}

export interface ChatState {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  streaming: boolean;
  currentUserId: string | null;
}

// Authentication & User Types
export interface User {
  id: string;
  email: string;
  name: string;
  google_id: string;
  active_sessions?: number;
  sessions?: UserSession[];
  created_at?: string;
  updated_at?: string;
}

export interface UserSession {
  id: string;
  user_id: string;
  session_token_hash: string;
  expires_at: string;
  created_at: string;
  last_activity: string;
  ip_address?: string;
  user_agent?: string;
  is_active: boolean;
}

export interface AuthState {
  authenticated: boolean;
  user: User | null;
  session: UserSession | null;
  loading: boolean;
  error: string | null;
  sessionToken: string | null;
}

// Google OAuth Types
export interface GoogleOAuthInitiateResponse {
  authorization_url: string;
  state: string;
}

export interface GoogleOAuthCallbackRequest {
  code: string;
  state: string;
}

export interface GoogleOAuthCallbackResponse {
  session_token: string;
  user: User;
  session: UserSession;
}

export interface AuthValidationResponse {
  user: User;
  session: UserSession;
  authenticated: boolean;
}

// Session-Based API Types
export interface SessionAnalysisRequest {
  protocol_text: string;
  protocol_title?: string;
  protocol_type?: string;
  analysis_options?: {
    top_k_sections?: number;
    [key: string]: any;
  };
  metadata?: Record<string, any>;
}

export interface SessionAnalysisResult {
  analysis_id: string;
  user_id: string;
  session_id: string;
  protocol_title?: string;
  protocol_type?: string;
  similar_sections: SimilarSection[];
  compliance_analysis: ComplianceAnalysis;
  processing_time: number;
  timestamp: number;
  search_stats: {
    total_results: number;
    indices_searched: string[];
    query_analysis: Record<string, any>;
  };
}

export interface SimilarSection {
  section_text: string;
  similarity_score: number;
  section_metadata: Record<string, any>;
  chunk_index: number;
}

export interface ComplianceAnalysis {
  compliance_score: number;
  compliance_status: string;
  issues: string[];
  recommendations: string[];
  missing_elements: string[];
  terminology_corrections: string[];
  confidence_score: number;
  analysis_text: string;
}

export interface SessionSearchRequest {
  query_text: string;
  top_k?: number;
  query_type?: string;
  filters?: Record<string, any>;
}

export interface SessionSearchResponse {
  query: string;
  results: SessionSearchResult[];
  total_results: number;
  search_time: number;
  query_analysis: Record<string, any>;
}

export interface SessionSearchResult {
  text: string;
  score: number;
  metadata: Record<string, any>;
  ranking_factors: Record<string, any>;
  explanation: string;
}

export interface SessionDocumentUploadRequest {
  filename: string;
  content: string;
  metadata?: Record<string, any>;
}

export interface SessionStats {
  total_documents: number;
  total_chunks: number;
  vector_count: number;
  session_age_hours: number;
  last_activity: string;
  [key: string]: any;
}

export interface SessionActionRequest {
  force?: boolean;
}

export interface DriveFile {
  id: string;
  name: string;
  size?: string | number; // Can be string from API
  createdTime: string; // Note: camelCase in actual API response
  modifiedTime: string; // Note: camelCase in actual API response  
  mimeType?: string; // Note: camelCase in actual API response
  mime_type?: string; // Fallback for snake_case
  created_time?: string; // Fallback for snake_case
  modified_time?: string; // Fallback for snake_case
  properties?: Record<string, any>; // Additional file properties
  [key: string]: any;
}

// Error Types
export interface GuardianApiError {
  error: string;
  error_code: string;
  message: string;
  details?: Record<string, any>;
}

// Enhanced API Response Type
export interface ApiResponse<T = any> {
  success?: boolean;
  status?: string;
  message?: string;
  data?: T;
  error?: string;
  error_code?: string;
  errors?: GuardianApiError[];
  timestamp?: string;
}

