// GUARDIAN Frontend Constants

export const API_ENDPOINTS = {
  // Health endpoints
  HEALTH: '/api/health/',
  HEALTH_DETAILED: '/api/health/detailed',
  HEALTH_READY: '/api/health/ready',
  
  // Authentication endpoints
  AUTH_GOOGLE_INITIATE: '/auth/google/initiate',
  AUTH_GOOGLE_CALLBACK: '/auth/google/callback',
  AUTH_VALIDATE: '/auth/validate',
  AUTH_USER: '/auth/user',
  AUTH_LOGOUT: '/auth/logout',
  AUTH_REFRESH: '/auth/refresh',
  AUTH_SESSIONS: '/auth/sessions',
  AUTH_HEALTH: '/auth/health',
  
  // Session-based analysis endpoints (multi-tenant)
  SESSION_INITIALIZE: '/api/session/initialize',
  SESSION_ANALYZE: '/api/session/analyze',
  SESSION_DOCUMENTS_UPLOAD: '/api/session/documents/upload',
  SESSION_SEARCH: '/api/session/search',
  SESSION_STATS: '/api/session/stats',
  SESSION_BACKUP: '/api/session/backup',
  SESSION_CLEANUP: '/api/session/cleanup',
  SESSION_DRIVE_FILES: '/api/session/drive/files',
  SESSION_HEALTH: '/api/session/health',
  
  // Legacy document management endpoints (single-tenant - deprecated)
  DOCUMENTS: '/api/documents',
  DOCUMENTS_UPLOAD: '/api/documents/upload',
  DOCUMENTS_STATS: '/api/documents/stats',
  DOCUMENT_BY_ID: (id: string) => `/api/documents/${id}`,
  DOCUMENT_PROCESS: (id: string) => `/api/documents/${id}/process`,
  DOCUMENT_DELETE: (id: string) => `/api/documents/${id}`,
  
  // Legacy protocol analysis endpoints (single-tenant - deprecated)
  ANALYZE: '/api/analyze',
  ANALYZE_BATCH: '/api/analyze/batch',
  ANALYZE_HISTORY: '/api/analyze/history',
  ANALYZE_STATS: '/api/analyze/stats',
  ANALYZE_BY_ID: (id: string) => `/api/analyze/${id}`,
  
  // Legacy search endpoints (single-tenant - deprecated)
  SEARCH: '/api/search',
  SEARCH_MULTI_INDEX: '/api/search/multi-index',
  SEARCH_SUGGESTIONS: '/api/search/suggestions',
  SEARCH_ANALYTICS: '/api/search/analytics',
  SEARCH_INDICES: '/api/search/indices',
  
  // Report endpoints
  REPORTS: '/api/reports',
  REPORTS_GENERATE: '/api/reports/generate',
  REPORTS_BATCH: '/api/reports/batch',
  REPORTS_TEMPLATES: '/api/reports/templates',
  REPORTS_STATS: '/api/reports/stats',
  REPORT_BY_ID: (id: string) => `/api/reports/${id}`,
  REPORT_DELETE: (id: string) => `/api/reports/${id}`,
  
  // Documentation endpoints
  DOCS: '/docs',
  DOCS_OPENAPI: '/docs/openapi.json'
} as const;

export const UPLOAD_CONFIG = {
  MAX_FILE_SIZE: 50 * 1024 * 1024, // 50MB
  ALLOWED_TYPES: ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  ALLOWED_EXTENSIONS: ['.pdf', '.txt', '.docx'],
  CHUNK_SIZE: 1024 * 1024 // 1MB chunks
} as const;

export const COMPLIANCE_THRESHOLDS = {
  HIGH: 80,
  MEDIUM: 60,
  LOW: 0
} as const;

export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 250,
  SLOW: 350
} as const;

export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536
} as const;

export const TOAST_DURATIONS = {
  SUCCESS: 4000,
  ERROR: 6000,
  WARNING: 5000,
  INFO: 4000
} as const;

export const CHAT_CONFIG = {
  MAX_MESSAGES: 100,
  MESSAGE_TIMEOUT: 30000,
  TYPING_INDICATOR_DELAY: 1000
} as const;

export const ANALYSIS_STAGES = [
  { key: 'uploading', label: 'Uploading document' },
  { key: 'extracting', label: 'Extracting text' },
  { key: 'chunking', label: 'Processing content' },
  { key: 'embedding', label: 'Generating embeddings' },
  { key: 'indexing', label: 'Building search index' },
  { key: 'completed', label: 'Analysis complete' }
] as const;

export const NAVIGATION_ITEMS = [
  { label: 'Dashboard', href: '/', icon: 'home', protected: false },
  { label: 'Ground Truth', href: '/ground-truth', icon: 'book-open', protected: true, description: 'Manage regulatory standards and compliance references' },
  { label: 'Analyze Protocols', href: '/protocols', icon: 'analysis', protected: true, description: 'Analyze pharmaceutical protocols against ground truth standards' },
  { label: 'Sample Reports', href: '/sample-reports', icon: 'reports', protected: false, description: 'View example compliance analysis reports' }
] as const;

export const AUTH_CONFIG = {
  SESSION_TOKEN_KEY: 'guardian_session_token',
  USER_DATA_KEY: 'guardian_user_data',
  SESSION_TIMEOUT_MS: 24 * 60 * 60 * 1000, // 24 hours
  TOKEN_REFRESH_THRESHOLD_MS: 60 * 60 * 1000, // 1 hour before expiry
  REDIRECT_URL_KEY: 'guardian_redirect_url',
  OAUTH_POPUP_WIDTH: 500,
  OAUTH_POPUP_HEIGHT: 600,
  MAX_SESSION_RETRIES: 3
} as const;

export const AUTH_ROUTES = {
  LOGIN: '/login',
  LOGOUT: '/logout',
  CALLBACK: '/auth/callback',
  PROFILE: '/profile',
  UNAUTHORIZED: '/unauthorized'
} as const;

export const SEVERITY_LABELS = {
  critical: 'Critical',
  major: 'Major',
  minor: 'Minor',
  info: 'Info'
} as const;

export const STATUS_LABELS = {
  compliant: 'Compliant',
  'non-compliant': 'Non-Compliant',
  partial: 'Partially Compliant',
  'needs-review': 'Needs Review'
} as const;

export const DOCUMENT_STATUS_LABELS = {
  uploading: 'Uploading',
  processing: 'Processing',
  completed: 'Completed',
  error: 'Error'
} as const;

export const ANALYSIS_STATUS_LABELS = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  error: 'Error'
} as const;

// Icon categories for comprehensive usage
export const ICON_CATEGORIES = {
  'Core Application': ['shield', 'home', 'analysis', 'reports', 'settings'],
  'File Operations': ['upload', 'download', 'file', 'file-text', 'file-image'],
  'Actions': ['check', 'x', 'close', 'menu', 'search', 'chat', 'edit', 'trash', 'copy', 'save', 'send', 'plus', 'minus'],
  'Status & Feedback': ['info', 'warning', 'error', 'success', 'loading', 'activity'],
  'Navigation': ['arrow-right', 'arrow-left', 'arrow-up', 'arrow-down', 'chevron-down', 'chevron-up', 'chevron-left', 'chevron-right'],
  'User & Account': ['user', 'user-plus', 'logout', 'lock', 'unlock'],
  'Utility': ['eye', 'eye-off', 'maximize', 'minimize', 'external-link', 'filter', 'sort-asc', 'sort-desc', 'clipboard', 'bookmark', 'calendar', 'clock', 'share', 'star', 'heart', 'mail', 'phone', 'map-pin', 'globe', 'more-horizontal', 'more-vertical', 'refresh', 'help'],
  'Charts & Analytics': ['trending', 'users', 'book-open'],
  'Theme & Display': ['sun', 'moon', 'monitor']
} as const;