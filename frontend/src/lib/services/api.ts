// GUARDIAN API Service Layer
// Complete integration with backend endpoints including authentication

import { API_ENDPOINTS, AUTH_CONFIG } from '$lib/constants';
import { appStore } from '$lib/stores';
import { AuthErrorHandler, convertApiErrorToAuthError } from '$lib/utils/auth-error-handler';
import type { 
  ApiResponse, 
  GoogleOAuthInitiateResponse, 
  GoogleOAuthCallbackRequest, 
  GoogleOAuthCallbackResponse,
  AuthValidationResponse,
  User,
  UserSession,
  SessionAnalysisRequest,
  SessionAnalysisResult,
  SessionSearchRequest,
  SessionSearchResponse,
  SessionDocumentUploadRequest,
  SessionStats,
  SessionActionRequest,
  DriveFile
} from '$lib/types';

// Authentication utilities
class SessionTokenManager {
  private static readonly TOKEN_KEY = AUTH_CONFIG.SESSION_TOKEN_KEY;
  
  static getToken(): string | null {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem(this.TOKEN_KEY);
  }
  
  static setToken(token: string): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.setItem(this.TOKEN_KEY, token);
  }
  
  static removeToken(): void {
    if (typeof localStorage === 'undefined') return;
    localStorage.removeItem(this.TOKEN_KEY);
  }
  
  static hasToken(): boolean {
    return !!this.getToken();
  }
}

// Document Types
export interface DocumentUploadRequest {
  file_content: string; // base64 encoded
  filename: string;
  file_type: string;
  document_type?: string;
  metadata?: Record<string, any>;
  process_immediately?: boolean;
}

export interface DocumentInfo {
  document_id: string;
  filename: string;
  file_metadata: FileMetadata;
  document_type?: string;
  processing_info: ProcessingInfo;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface FileMetadata {
  filename: string;
  file_size: number;
  file_type: string;
  upload_time: string;
}

export interface ProcessingInfo {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface DocumentProcessingRequest {
  create_index?: boolean;
  index_name?: string;
}

export interface DocumentStats {
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  total_size_mb: number;
  avg_processing_time: number;
  document_types?: Record<string, number>;
  recent_uploads?: DocumentInfo[];
}

// Analysis Types
export interface ProtocolAnalysisRequest {
  protocol_text: string;
  analysis_options?: {
    include_compliance_check?: boolean;
    include_terminology_review?: boolean;
    include_missing_elements?: boolean;
  };
}

export interface ProtocolAnalysisResult {
  analysis_id: string;
  protocol_input: {
    text: string;
    word_count: number;
    character_count: number;
  };
  similar_sections: SimilarSection[];
  compliance_analysis: ComplianceAssessment;
  search_metadata: SearchMetadata;
  processing_time: number;
  timestamp: string;
}

export interface SimilarSection {
  section_text: string;
  similarity_score: number;
  source_metadata: {
    section: string;
    document_type: string;
    [key: string]: any;
  };
}

export interface ComplianceAssessment {
  overall_compliance_score: number;
  compliance_issues: ComplianceIssue[];
}

export interface ComplianceIssue {
  issue_type: string;
  description: string;
  severity: 'critical' | 'major' | 'minor' | 'info';
  suggested_fix?: string;
}

export interface SearchMetadata {
  total_sections_found: number;
  avg_similarity_score: number;
  processing_time_ms: number;
}

// Search Types
export interface VectorSearchRequest {
  query: string;
  max_results?: number;
  min_similarity?: number;
  index_name?: string;
}

export interface VectorSearchResponse {
  results: SearchResult[];
  metadata: SearchMetadata;
}

export interface SearchResult {
  text: string;
  similarity_score: number;
  metadata: Record<string, any>;
}

export interface SearchAnalytics {
  total_searches: number;
  avg_search_time: number;
  cache_hit_rate: number;
  popular_queries: { query: string; count: number }[];
  query_success_rate: number;
  unique_queries: number;
}

// Health Types
export interface HealthResponse {
  success: boolean;
  status: 'healthy' | 'unhealthy' | 'degraded' | 'ready' | 'not_ready';
  timestamp: string;
  service: string;
  version?: string;
  uptime_seconds?: number;
  dependencies?: Record<string, any>;
  system?: Record<string, any>;
  configuration?: Record<string, any>;
  response_time_ms?: number;
  warnings?: string;
  issues?: string[];
}

// API Client Class
export class GuardianApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public errors?: ApiError[]
  ) {
    super(message);
    this.name = 'GuardianApiError';
  }
}

class GuardianApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = '') {
    this.baseUrl = baseUrl; // Empty string uses relative URLs (proxy in dev)
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requireAuth: boolean = false
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders: Record<string, string> = {
      'Accept': 'application/json',
    };

    // Only set Content-Type if body is not FormData
    if (!(options.body instanceof FormData)) {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    // Add authentication header if token exists or auth is required
    const token = SessionTokenManager.getToken();
    if (token || requireAuth) {
      if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
      } else if (requireAuth) {
        throw new GuardianApiError('Authentication required but no session token found', 401, 'AUTH_TOKEN_MISSING');
      }
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      // Don't show global loading for auth endpoints - they have their own loading states
      const isAuthEndpoint = endpoint.includes('/auth/') || endpoint.includes('/google/');
      if (!isAuthEndpoint) {
        appStore.setLoading(true);
      }
      
      const response = await fetch(url, config);
      
      // Handle non-JSON responses (like file downloads)
      if (!response.headers.get('content-type')?.includes('application/json')) {
        if (!response.ok) {
          throw new GuardianApiError(
            'Request failed',
            response.status
          );
        }
        return { success: true } as ApiResponse<T>;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new GuardianApiError(
          data.message || 'Request failed',
          response.status,
          data.error_code,
          data.errors
        );
      }

      return data;
    } catch (error) {
      if (error instanceof GuardianApiError) {
        // Handle authentication-related API errors
        if (this.isAuthError(error.status, error.code)) {
          const authError = convertApiErrorToAuthError(error, {
            operation: `API ${config.method?.toUpperCase() || 'GET'} ${endpoint}`,
            route: window.location.pathname,
            retryable: requireAuth && (error.status === 401 || error.status === 403)
          });
          
          // Handle auth error (but don't block the promise chain)
          AuthErrorHandler.handleError(authError).catch(console.error);
        }
        
        throw error;
      }

      // Network or other errors
      const networkError = new GuardianApiError(
        'Network error or server unavailable',
        0
      );
      
      // Handle network errors for authenticated requests
      if (requireAuth) {
        const authError = convertApiErrorToAuthError(error, {
          operation: `API ${config.method?.toUpperCase() || 'GET'} ${endpoint}`,
          route: window.location.pathname,
          retryable: true
        });
        
        AuthErrorHandler.handleError(authError).catch(console.error);
      }
      
      throw networkError;
    } finally {
      // Only clear loading if we set it
      const isAuthEndpoint = endpoint.includes('/auth/') || endpoint.includes('/google/');
      if (!isAuthEndpoint) {
        appStore.setLoading(false);
      }
    }
  }

  async get<T>(endpoint: string, params?: Record<string, any>, requireAuth: boolean = false): Promise<ApiResponse<T>> {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      });
      if (searchParams.toString()) {
        url += `?${searchParams.toString()}`;
      }
    }
    return this.request<T>(url, { method: 'GET' }, requireAuth);
  }

  async post<T>(endpoint: string, data?: any, requireAuth: boolean = false): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }, requireAuth);
  }

  async put<T>(endpoint: string, data?: any, requireAuth: boolean = false): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }, requireAuth);
  }

  async delete<T>(endpoint: string, requireAuth: boolean = false): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' }, requireAuth);
  }

  setBaseUrl(url: string): void {
    this.baseUrl = url;
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Check if an error is authentication-related
   */
  private isAuthError(status: number, code?: string): boolean {
    const authCodes = [
      'AUTH_TOKEN_MISSING',
      'AUTH_TOKEN_INVALID', 
      'AUTH_TOKEN_EXPIRED',
      'AUTH_SESSION_INVALID',
      'OAUTH_ERROR'
    ];
    
    const authStatuses = [401, 403];
    
    return authStatuses.includes(status) || (code && authCodes.includes(code));
  }

  // Utility method to convert File to base64
  static async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          // Remove data URL prefix (data:type;base64,)
          const base64 = reader.result.split(',')[1];
          resolve(base64);
        } else {
          reject(new Error('Failed to convert file to base64'));
        }
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });
  }
}

// Create singleton instance
export const apiClient = new GuardianApiClient();

// Health API
export const healthApi = {
  /**
   * Basic health check
   */
  check: (): Promise<ApiResponse<HealthResponse>> =>
    apiClient.get<HealthResponse>(API_ENDPOINTS.HEALTH),

  /**
   * Detailed health check with dependencies
   */
  detailed: (): Promise<ApiResponse<HealthResponse>> =>
    apiClient.get<HealthResponse>(API_ENDPOINTS.HEALTH_DETAILED),

  /**
   * Readiness check
   */
  ready: (): Promise<ApiResponse<HealthResponse>> =>
    apiClient.get<HealthResponse>(API_ENDPOINTS.HEALTH_READY),
};

// Authentication API
export const authApi = {
  /**
   * Initiate Google OAuth 2.0 flow
   */
  initiateGoogleAuth: (): Promise<ApiResponse<GoogleOAuthInitiateResponse>> =>
    apiClient.get<GoogleOAuthInitiateResponse>(API_ENDPOINTS.AUTH_GOOGLE_INITIATE),

  /**
   * Handle OAuth callback with authorization code
   */
  handleGoogleCallback: (request: GoogleOAuthCallbackRequest): Promise<ApiResponse<GoogleOAuthCallbackResponse>> =>
    apiClient.post<GoogleOAuthCallbackResponse>(API_ENDPOINTS.AUTH_GOOGLE_CALLBACK, request),

  /**
   * Validate current session
   */
  validateSession: (): Promise<ApiResponse<AuthValidationResponse>> =>
    apiClient.get<AuthValidationResponse>(API_ENDPOINTS.AUTH_VALIDATE, {}, true),

  /**
   * Get current user information
   */
  getCurrentUser: (): Promise<ApiResponse<User>> =>
    apiClient.get<User>(API_ENDPOINTS.AUTH_USER, {}, true),

  /**
   * Logout and invalidate session
   */
  logout: (sessionToken?: string): Promise<ApiResponse<void>> =>
    apiClient.post<void>(API_ENDPOINTS.AUTH_LOGOUT, sessionToken ? { session_token: sessionToken } : undefined),

  /**
   * Refresh Google Drive tokens
   */
  refreshTokens: (): Promise<ApiResponse<void>> =>
    apiClient.post<void>(API_ENDPOINTS.AUTH_REFRESH, {}, true),

  /**
   * List all active sessions for current user
   */
  listSessions: (): Promise<ApiResponse<{ sessions: UserSession[]; total_sessions: number }>> =>
    apiClient.get<{ sessions: UserSession[]; total_sessions: number }>(API_ENDPOINTS.AUTH_SESSIONS, {}, true),

  /**
   * Authentication system health check
   */
  healthCheck: (): Promise<ApiResponse<any>> =>
    apiClient.get<any>(API_ENDPOINTS.AUTH_HEALTH),
};

// Session-Based Analysis API (Multi-tenant)
export const sessionApi = {
  /**
   * Initialize user vector database session
   */
  initialize: (): Promise<ApiResponse<{ user_id: string; session_id: string; initialized: boolean }>> =>
    apiClient.post<{ user_id: string; session_id: string; initialized: boolean }>(API_ENDPOINTS.SESSION_INITIALIZE, {}, true),

  /**
   * Analyze protocol using user's session-based vector database
   */
  analyze: (request: SessionAnalysisRequest): Promise<ApiResponse<SessionAnalysisResult>> =>
    apiClient.post<SessionAnalysisResult>(API_ENDPOINTS.SESSION_ANALYZE, request, true),

  /**
   * Upload documents to user's session
   */
  uploadDocuments: async (
    files: File[] | SessionDocumentUploadRequest | SessionDocumentUploadRequest[]
  ): Promise<ApiResponse<{ documents_uploaded: number; user_id: string; session_id: string }>> => {
    if (Array.isArray(files) && files.length > 0 && files[0] instanceof File) {
      // Handle File upload
      const formData = new FormData();
      (files as File[]).forEach(file => formData.append('files', file));
      
      return apiClient.request<{ documents_uploaded: number; user_id: string; session_id: string }>(
        API_ENDPOINTS.SESSION_DOCUMENTS_UPLOAD,
        {
          method: 'POST',
          body: formData,
          headers: {} // Don't set Content-Type for FormData
        },
        true
      );
    } else {
      // Handle JSON upload
      const documents = Array.isArray(files) ? files : [files] as SessionDocumentUploadRequest[];
      return apiClient.post<{ documents_uploaded: number; user_id: string; session_id: string }>(
        API_ENDPOINTS.SESSION_DOCUMENTS_UPLOAD, 
        documents,
        true
      );
    }
  },

  /**
   * Search user's session vector database
   */
  search: (request: SessionSearchRequest): Promise<ApiResponse<SessionSearchResponse>> =>
    apiClient.post<SessionSearchResponse>(API_ENDPOINTS.SESSION_SEARCH, request, true),

  /**
   * Get session statistics
   */
  getStats: (): Promise<ApiResponse<SessionStats>> =>
    apiClient.get<SessionStats>(API_ENDPOINTS.SESSION_STATS, {}, true),

  /**
   * Backup session to Google Drive
   */
  backup: (force: boolean = false): Promise<ApiResponse<{ user_id: string; session_id: string; backed_up: boolean }>> =>
    apiClient.post<{ user_id: string; session_id: string; backed_up: boolean }>(
      API_ENDPOINTS.SESSION_BACKUP, 
      { force },
      true
    ),

  /**
   * Cleanup user session
   */
  cleanup: (force: boolean = false): Promise<ApiResponse<{ user_id: string; session_id: string; cleaned_up: boolean }>> =>
    apiClient.post<{ user_id: string; session_id: string; cleaned_up: boolean }>(
      API_ENDPOINTS.SESSION_CLEANUP,
      { force },
      true
    ),

  /**
   * List user's Google Drive files
   */
  listDriveFiles: (fileType: string = 'document'): Promise<ApiResponse<{ files: DriveFile[]; file_type: string; count: number }>> =>
    apiClient.get<{ files: DriveFile[]; file_type: string; count: number }>(
      API_ENDPOINTS.SESSION_DRIVE_FILES,
      { file_type: fileType },
      true
    ),

  /**
   * Session services health check
   */
  healthCheck: (): Promise<ApiResponse<{ active_sessions: number; session_service: string }>> =>
    apiClient.get<{ active_sessions: number; session_service: string }>(API_ENDPOINTS.SESSION_HEALTH),
};

// Document Management API
export const documentApi = {
  /**
   * Upload a document
   */
  upload: async (
    file: File, 
    options: {
      documentType?: string;
      metadata?: Record<string, any>;
      processImmediately?: boolean;
    } = {}
  ): Promise<ApiResponse<DocumentInfo>> => {
    const base64Content = await GuardianApiClient.fileToBase64(file);
    
    const request: DocumentUploadRequest = {
      file_content: base64Content,
      filename: file.name,
      file_type: file.name.split('.').pop() || '',
      document_type: options.documentType,
      metadata: options.metadata,
      process_immediately: options.processImmediately ?? true,
    };

    return apiClient.post<DocumentInfo>(API_ENDPOINTS.DOCUMENTS_UPLOAD, request);
  },

  /**
   * List documents with pagination and filtering
   */
  list: (params: {
    page?: number;
    per_page?: number;
    document_type?: string;
    processed_only?: boolean;
    search_term?: string;
  } = {}): Promise<ApiResponse<DocumentInfo[]>> =>
    apiClient.get<DocumentInfo[]>(API_ENDPOINTS.DOCUMENTS, params),

  /**
   * Get document information
   */
  get: (documentId: string): Promise<ApiResponse<DocumentInfo>> =>
    apiClient.get<DocumentInfo>(API_ENDPOINTS.DOCUMENT_BY_ID(documentId)),

  /**
   * Process a document
   */
  process: (
    documentId: string, 
    options: DocumentProcessingRequest = {}
  ): Promise<ApiResponse<DocumentInfo>> =>
    apiClient.post<DocumentInfo>(
      API_ENDPOINTS.DOCUMENT_PROCESS(documentId), 
      options
    ),

  /**
   * Delete a document
   */
  delete: (documentId: string): Promise<ApiResponse<{ document_id: string }>> =>
    apiClient.delete<{ document_id: string }>(API_ENDPOINTS.DOCUMENT_DELETE(documentId)),

  /**
   * Get document statistics
   */
  stats: (): Promise<ApiResponse<DocumentStats>> =>
    apiClient.get<DocumentStats>(API_ENDPOINTS.DOCUMENTS_STATS),
};

// Protocol Analysis API
export const analysisApi = {
  /**
   * Analyze a protocol
   */
  analyze: (request: ProtocolAnalysisRequest): Promise<ApiResponse<ProtocolAnalysisResult>> =>
    apiClient.post<ProtocolAnalysisResult>(API_ENDPOINTS.ANALYZE, request),

  /**
   * Get analysis result by ID
   */
  get: (analysisId: string): Promise<ApiResponse<ProtocolAnalysisResult>> =>
    apiClient.get<ProtocolAnalysisResult>(API_ENDPOINTS.ANALYZE_BY_ID(analysisId)),

  /**
   * Get analysis history
   */
  history: (params: {
    page?: number;
    per_page?: number;
    start_date?: string;
    end_date?: string;
  } = {}): Promise<ApiResponse<ProtocolAnalysisResult[]>> =>
    apiClient.get<ProtocolAnalysisResult[]>(API_ENDPOINTS.ANALYZE_HISTORY, params),

  /**
   * Get analysis statistics
   */
  stats: (): Promise<ApiResponse<any>> =>
    apiClient.get(API_ENDPOINTS.ANALYZE_STATS),

  /**
   * Batch analysis
   */
  batch: (protocols: ProtocolAnalysisRequest[]): Promise<ApiResponse<ProtocolAnalysisResult[]>> =>
    apiClient.post<ProtocolAnalysisResult[]>(API_ENDPOINTS.ANALYZE_BATCH, { protocols }),
};

// Vector Search API
export const searchApi = {
  /**
   * Perform vector similarity search
   */
  search: (request: VectorSearchRequest): Promise<ApiResponse<VectorSearchResponse>> =>
    apiClient.post<VectorSearchResponse>(API_ENDPOINTS.SEARCH, request),

  /**
   * Get search suggestions
   */
  suggestions: (params: {
    query: string;
    limit?: number;
  }): Promise<ApiResponse<string[]>> =>
    apiClient.get<string[]>(API_ENDPOINTS.SEARCH_SUGGESTIONS, params),

  /**
   * Get search analytics
   */
  analytics: (params: {
    date_range?: number;
  } = {}): Promise<ApiResponse<SearchAnalytics>> =>
    apiClient.get<SearchAnalytics>(API_ENDPOINTS.SEARCH_ANALYTICS, params),

  /**
   * Get available indices
   */
  indices: (): Promise<ApiResponse<string[]>> =>
    apiClient.get<string[]>(API_ENDPOINTS.SEARCH_INDICES),
};

// Reports API
export const reportApi = {
  /**
   * Generate a report
   */
  generate: (params: {
    analysis_id: string;
    format?: 'pdf' | 'html' | 'json';
    template?: string;
    options?: Record<string, any>;
  }): Promise<ApiResponse<{ report_id: string }>> =>
    apiClient.post<{ report_id: string }>(API_ENDPOINTS.REPORTS_GENERATE, params),

  /**
   * Get/download a report
   */
  get: (reportId: string): Promise<ApiResponse<any>> =>
    apiClient.get(API_ENDPOINTS.REPORT_BY_ID(reportId)),

  /**
   * List reports
   */
  list: (params: {
    page?: number;
    per_page?: number;
    format?: string;
  } = {}): Promise<ApiResponse<any[]>> =>
    apiClient.get<any[]>(API_ENDPOINTS.REPORTS, params),

  /**
   * Delete a report
   */
  delete: (reportId: string): Promise<ApiResponse<{ report_id: string }>> =>
    apiClient.delete<{ report_id: string }>(API_ENDPOINTS.REPORT_DELETE(reportId)),

  /**
   * Get report templates
   */
  templates: (): Promise<ApiResponse<any[]>> =>
    apiClient.get<any[]>(API_ENDPOINTS.REPORTS_TEMPLATES),

  /**
   * Get report statistics
   */
  stats: (): Promise<ApiResponse<any>> =>
    apiClient.get(API_ENDPOINTS.REPORTS_STATS),

  /**
   * Get download URL for a report
   */
  downloadUrl: (reportId: string): string =>
    `${apiClient.getBaseUrl()}${API_ENDPOINTS.REPORT_BY_ID(reportId)}`,
};

// Export all APIs
export {
  // Core system APIs
  healthApi as health,
  
  // Authentication & Multi-tenant APIs (Primary)
  authApi as auth,
  sessionApi as session,
  
  // Legacy single-tenant APIs (Deprecated - use session APIs instead)
  documentApi as documents,
  analysisApi as analysis,
  searchApi as search,
  
  // Report APIs
  reportApi as reports,
};

// Combined API object for convenience
export const api = {
  health: healthApi,
  auth: authApi,
  session: sessionApi,
  documents: documentApi,
  analysis: analysisApi,
  search: searchApi,
  reports: reportApi,
};

// Export authentication utilities
export { SessionTokenManager };