// GUARDIAN Store Exports - Svelte 5 Runes Edition

// Phase 1-6 - Modernized Stores (Svelte 5 Runes)
export { 
  appStore, 
  isLoading, 
  hasError, 
  currentSettings, 
  currentUser as appCurrentUser, 
  isAuthenticated as appIsAuthenticated 
} from './app.svelte';

export { 
  toastStore, 
  toastCount, 
  hasToasts, 
  latestToast 
} from './toast.svelte';

export { 
  themeStore, 
  resolvedTheme 
} from './theme.svelte';

export { 
  authStore,
  authState,
  isAuthenticated,
  currentUser,
  currentSession,
  authLoading,
  authError,
  hasValidSession
} from './auth.svelte';

export { 
  documentStore, 
  selectedDocument, 
  documentCount, 
  processingDocuments, 
  completedDocuments, 
  errorDocuments, 
  isUploading,
  hasDocuments,
  hasSelectedDocument,
  uploadProgress,
  processingCount as docProcessingCount,
  completedCount as docCompletedCount,
  errorCount as docErrorCount,
  createDocumentVirtualList,
  documentsByDate,
  documentsByName,
  documentsBySize,
  searchDocuments,
  getDocumentPerformanceMetrics
} from './documents.svelte';

export { 
  analysisStore, 
  analysisCount, 
  processingAnalysis, 
  completedAnalysis, 
  errorAnalysis, 
  averageComplianceScore, 
  criticalFindings, 
  nonCompliantFindings,
  hasResults,
  hasCurrentAnalysis,
  isProcessing,
  processingCount as analysisProcessingCount,
  completedCount as analysisCompletedCount,
  errorCount as analysisErrorCount,
  currentAnalysisFindings,
  currentComplianceScore,
  currentAnalysisStatus,
  findingsBySeverity,
  findingsByStatus,
  complianceStats
} from './analysis.svelte';

export { 
  chatStore, 
  sessionCount, 
  currentMessages, 
  lastMessage, 
  messageCount, 
  hasActiveSession, 
  canSendMessage,
  hasSessions,
  isStreaming,
  hasMessages,
  currentSessionId,
  sessionsByDate,
  recentSessions,
  messagesByRole,
  conversationContext,
  chatStats,
  createMessageVirtualList,
  getChatPerformanceMetrics
} from './chat.svelte';

// Type exports
export type { Theme, ResolvedTheme } from './theme.svelte';
export type { ToastMessage } from './toast.svelte';