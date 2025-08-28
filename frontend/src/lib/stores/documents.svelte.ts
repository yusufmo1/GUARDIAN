import type { Document, UploadProgress } from '$lib/types';
import { generateId } from '$lib/utils';
import { 
  memoized, 
  debouncedEffect, 
  createVirtualList,
  getPerformanceMetrics,
  batchUpdates 
} from '$lib/utils/performance.svelte';
import { 
  globalErrorBoundary, 
  withRetry, 
  ErrorType,
  ErrorSeverity,
  createError 
} from '$lib/utils/error-handling.svelte';
import { persistedState } from '$lib/utils/state-persistence.svelte';

// Create reactive document state using Svelte 5 runes
let documents = $state<Document[]>([]);
let uploading = $state<UploadProgress[]>([]);
let selected = $state<string | null>(null);
let currentUserId = $state<string | null>(null);

// State persistence for document management
const persistedDocumentState = persistedState(
  { documents: [], selected: null as string | null },
  {
    key: 'guardian-document-state',
    version: 1,
    storage: 'localStorage',
    debounceMs: 2000,
    exclude: ['uploading'], // Don't persist upload progress (temporary state)
    crossTab: false, // DISABLED: Cross-tab sync was causing infinite reactive loops
    compress: true // Compress document data as it can be large
  }
);

// Note: Document persistence moved to component initialization
// Store-level effects are not allowed in Svelte 5

// Note: Persistence is now manual - called by components when needed
// No automatic persistence to avoid infinite loops in Svelte 5

// Optimized derived computations with memoization for performance
export const selectedDocument = memoized(
  () => documents.find(doc => doc.id === selected) || null,
  () => [selected, documents.length, documents.map(d => d.id).join(',')],
  { name: 'document-selected', maxAge: 3000 }
);

export function documentCount() { return documents.length; }

const processingDocumentsMemo = memoized(
  () => documents.filter(doc => 
    doc.status === 'processing' || doc.status === 'uploading'
  ),
  () => [documents.length, documents.map(d => d.status).join(',')],
  { name: 'document-processing', maxAge: 2000 }
);

const completedDocumentsMemo = memoized(
  () => documents.filter(doc => doc.status === 'completed'),
  () => [documents.length, documents.map(d => d.status).join(',')],
  { name: 'document-completed', maxAge: 2000 }
);

const errorDocumentsMemo = memoized(
  () => documents.filter(doc => doc.status === 'error'),
  () => [documents.length, documents.map(d => d.status).join(',')],
  { name: 'document-error', maxAge: 2000 }
);

export function processingDocuments() { return processingDocumentsMemo(); }
export function completedDocuments() { return completedDocumentsMemo(); }
export function errorDocuments() { return errorDocumentsMemo(); }

export function isUploading() { return uploading.length > 0; }

// Additional derived computations for better UX
export function hasDocuments() { return documents.length > 0; }
export function hasSelectedDocument() { return selected !== null; }
export function uploadProgress() { return uploading; }
export function processingCount() { return processingDocuments().length; }
export function completedCount() { return completedDocuments().length; }
export function errorCount() { return errorDocuments().length; }

// Virtual list support for large document lists
export function createDocumentVirtualList(containerHeight: number = 600) {
  return createVirtualList(
    () => documents,
    {
      itemHeight: 72, // Approximate document item height
      containerHeight,
      overscan: 10,
      name: 'document-list'
    }
  );
}

// Optimized sorting with memoization for performance
const documentsByDateMemo = memoized(
  () => {
    return [...documents].sort((a, b) => {
      const dateA = new Date(a.uploadedAt).getTime();
      const dateB = new Date(b.uploadedAt).getTime();
      return dateB - dateA; // Default: newest first
    });
  },
  () => [
    documents.length, 
    documents.map(d => d.uploadedAt.getTime()).join(',')
  ],
  { name: 'document-sort-date', maxAge: 5000 }
);

const documentsByNameMemo = memoized(
  () => {
    return [...documents].sort((a, b) => a.name.localeCompare(b.name));
  },
  () => [
    documents.length,
    documents.map(d => d.name).join(',')
  ],
  { name: 'document-sort-name', maxAge: 5000 }
);

const documentsBySizeMemo = memoized(
  () => {
    return [...documents].sort((a, b) => b.size - a.size); // Default: largest first
  },
  () => [
    documents.length,
    documents.map(d => d.size).join(',')
  ],
  { name: 'document-sort-size', maxAge: 5000 }
);

// Create search function that takes query as parameter
let lastSearchQuery = '';
let lastSearchResults: any[] = [];

export function documentsByDate() { return documentsByDateMemo(); }
export function documentsByName() { return documentsByNameMemo(); }
export function documentsBySize() { return documentsBySizeMemo(); }

export function searchDocuments(query: string) {
  if (!query?.trim()) return [];
  
  // Simple caching for last search
  if (query === lastSearchQuery) return lastSearchResults;
  
  const lowercaseQuery = query.toLowerCase();
  const results = documents.filter(doc =>
    doc.name.toLowerCase().includes(lowercaseQuery) ||
    doc.type.toLowerCase().includes(lowercaseQuery)
  );
  
  lastSearchQuery = query;
  lastSearchResults = results;
  return results;
}

// Performance monitoring
export function getDocumentPerformanceMetrics() {
  return getPerformanceMetrics();
}

// Note: User isolation moved to component initialization
// Store-level effects are not allowed in Svelte 5

// Document store interface - maintains compatibility with existing code
export const documentStore = {
  // Getters for reactive access
  get documents(): Document[] {
    return documents;
  },
  
  get uploading(): UploadProgress[] {
    return uploading;
  },
  
  get selected(): string | null {
    return selected;
  },
  
  get currentUserId(): string | null {
    return currentUserId;
  },
  
  // Document management with error handling and validation
  addDocument(document: Omit<Document, 'id' | 'uploadedAt'>): string {
    try {
      // Validate document data
      if (!document.name?.trim()) {
        const error = createError(
          'Document name is required',
          ErrorType.VALIDATION,
          ErrorSeverity.MEDIUM
        );
        globalErrorBoundary.addError(error);
        throw new Error(error.message);
      }
      
      if (!document.size || document.size <= 0) {
        const error = createError(
          'Document size must be greater than 0',
          ErrorType.VALIDATION,
          ErrorSeverity.MEDIUM
        );
        globalErrorBoundary.addError(error);
        throw new Error(error.message);
      }
      
      if (!document.type?.trim()) {
        const error = createError(
          'Document type is required',
          ErrorType.VALIDATION,
          ErrorSeverity.MEDIUM
        );
        globalErrorBoundary.addError(error);
        throw new Error(error.message);
      }
      
      const newDocument: Document = {
        ...document,
        id: generateId(),
        uploadedAt: new Date()
      };
      
      documents = [...documents, newDocument];
      
      console.log(` Document added: ${newDocument.name} (${newDocument.id})`);
      return newDocument.id;
    } catch (error) {
      console.error('Failed to add document:', error);
      globalErrorBoundary.addError(createError(
        `Failed to add document: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.MEDIUM,
        { originalError: error, documentData: document }
      ));
      throw error;
    }
  },
  
  updateDocument(id: string, updates: Partial<Document>): void {
    documents = documents.map(doc => 
      doc.id === id ? { ...doc, ...updates } : doc
    );
  },
  
  removeDocument(id: string): void {
    documents = documents.filter(doc => doc.id !== id);
    
    // Clear selection if the removed document was selected
    if (selected === id) {
      selected = null;
    }
  },
  
  selectDocument(id: string | null): void {
    selected = id;
  },
  
  // Upload progress management
  addUploadProgress(progress: UploadProgress): void {
    uploading = [...uploading, progress];
  },
  
  updateUploadProgress(documentId: string, updates: Partial<UploadProgress>): void {
    uploading = uploading.map(upload =>
      upload.documentId === documentId 
        ? { ...upload, ...updates }
        : upload
    );
  },
  
  removeUploadProgress(documentId: string): void {
    uploading = uploading.filter(upload => 
      upload.documentId !== documentId
    );
  },
  
  // Batch upload operations
  clearCompletedUploads(): void {
    uploading = uploading.filter(upload => 
      upload.stage !== 'completed' && upload.stage !== 'error'
    );
  },
  
  getUploadProgress(documentId: string): UploadProgress | undefined {
    return uploading.find(upload => upload.documentId === documentId);
  },
  
  // User context management
  setCurrentUser(userId: string | null): void {
    const previousUserId = currentUserId;
    
    // If user changed, clear all data
    if (previousUserId !== userId) {
      console.log(` Documents: User changed from ${previousUserId} to ${userId}, clearing data`);
      
      documents = [];
      uploading = [];
      selected = null;
    }
    
    currentUserId = userId;
  },
  
  // Bulk operations
  clearAll(): void {
    console.log(' Documents: Clearing all data');
    documents = [];
    uploading = [];
    selected = null;
    currentUserId = null;
  },
  
  clearCompleted(): void {
    documents = documents.filter(doc => doc.status !== 'completed');
  },
  
  // Document filtering helpers
  getDocumentsByStatus(status: Document['status']): Document[] {
    return documents.filter(doc => doc.status === status);
  },
  
  getDocumentById(id: string): Document | undefined {
    return documents.find(doc => doc.id === id);
  },
  
  // Statistics and analytics
  getDocumentStats() {
    return {
      total: documents.length,
      processing: processingDocuments.length,
      completed: completedDocuments.length,
      error: errorDocuments.length,
      uploading: uploading.length
    };
  },
  
  // Optimized bulk document operations using Set for better performance
  removeMultipleDocuments(ids: string[]): void {
    try {
      if (!ids.length) return;
      
      // Use Set for O(1) lookups instead of O(n) array.includes()
      const idsToRemove = new Set(ids);
      const before = documents.length;
      
      documents = documents.filter(doc => !idsToRemove.has(doc.id));
      
      // Clear selection if selected document was removed
      if (selected && idsToRemove.has(selected)) {
        selected = null;
      }
      
      const removed = before - documents.length;
      console.log(` Removed ${removed} documents`);
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Failed to remove multiple documents: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.MEDIUM,
        { documentIds: ids }
      ));
    }
  },
  
  updateMultipleDocuments(ids: string[], updates: Partial<Document>): void {
    try {
      if (!ids.length) return;
      
      // Use Set for O(1) lookups
      const idsToUpdate = new Set(ids);
      let updatedCount = 0;
      
      documents = documents.map(doc => {
        if (idsToUpdate.has(doc.id)) {
          updatedCount++;
          return { ...doc, ...updates };
        }
        return doc;
      });
      
      console.log(` Updated ${updatedCount} documents`);
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Failed to update multiple documents: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.MEDIUM,
        { documentIds: ids, updates }
      ));
    }
  },
  
  // Optimized batch operations with progress tracking
  batchUpdateStatus(ids: string[], status: Document['status']): void {
    try {
      batchUpdates(this, { 
        documents: documents.map(doc => 
          ids.includes(doc.id) ? { ...doc, status } : doc
        )
      });
      
      console.log(` Batch updated ${ids.length} documents to status: ${status}`);
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Batch status update failed: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.MEDIUM,
        { documentIds: ids, status }
      ));
    }
  },
  
  // Optimized search and filtering using memoized functions
  searchDocuments(query: string): Document[] {
    return searchDocuments(query);
  },
  
  getDocumentsByType(type: string): Document[] {
    try {
      return documents.filter(doc => doc.type === type);
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Failed to filter documents by type: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.LOW,
        { type }
      ));
      return [];
    }
  },
  
  // Optimized sorting using memoized functions
  getDocumentsSortedByDate(ascending: boolean = false): Document[] {
    return documentsByDate(ascending);
  },
  
  getDocumentsSortedByName(ascending: boolean = true): Document[] {
    return documentsByName(ascending);
  },
  
  getDocumentsSortedBySize(ascending: boolean = false): Document[] {
    return documentsBySize(ascending);
  },
  
  // Advanced filtering with multiple criteria
  getDocumentsFiltered(filters: {
    status?: Document['status'];
    type?: string;
    sizeRange?: { min: number; max: number };
    dateRange?: { start: Date; end: Date };
  }): Document[] {
    try {
      let result = [...documents];
      
      if (filters.status) {
        result = result.filter(doc => doc.status === filters.status);
      }
      
      if (filters.type) {
        result = result.filter(doc => doc.type === filters.type);
      }
      
      if (filters.sizeRange) {
        result = result.filter(doc => 
          doc.size >= filters.sizeRange!.min && 
          doc.size <= filters.sizeRange!.max
        );
      }
      
      if (filters.dateRange) {
        result = result.filter(doc => {
          const docTime = doc.uploadedAt.getTime();
          return docTime >= filters.dateRange!.start.getTime() && 
                 docTime <= filters.dateRange!.end.getTime();
        });
      }
      
      return result;
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Failed to filter documents: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.LOW,
        { filters }
      ));
      return [];
    }
  },
  
  // Error recovery and health check
  async recoverFromErrors(): Promise<boolean> {
    try {
      // Validate current state
      const isValid = this.validateDocumentState();
      if (!isValid) {
        console.warn('Document state validation failed, attempting recovery...');
        
        // Attempt to restore from persistence
        await persistedDocumentState.restore();
        
        // Re-validate
        if (!this.validateDocumentState()) {
          // Reset to clean state if still invalid
          this.reset();
        }
      }
      
      // Clear old error states
      globalErrorBoundary.clearErrors(ErrorType.CLIENT);
      
      return true;
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Document recovery failed: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.HIGH,
        { recoveryAttempt: true }
      ));
      return false;
    }
  },
  
  // State validation for error recovery
  validateDocumentState(): boolean {
    try {
      // Check documents array integrity
      if (!Array.isArray(documents)) return false;
      
      // Validate each document
      for (const document of documents) {
        if (!this.validateDocument(document)) return false;
      }
      
      // Check upload progress array
      if (!Array.isArray(uploading)) return false;
      
      // Validate selected document reference
      if (selected && !documents.find(d => d.id === selected)) {
        return false;
      }
      
      return true;
    } catch (error) {
      return false;
    }
  },
  
  // Performance analytics
  getDocumentPerformanceStats() {
    const metrics = getDocumentPerformanceMetrics();
    return {
      cacheStats: Object.entries(metrics.derivedComputations)
        .filter(([name]) => name.startsWith('document-'))
        .reduce((acc, [name, data]) => {
          acc[name] = {
            computations: data.count,
            averageTime: data.avgTime,
            totalTime: data.totalTime
          };
          return acc;
        }, {} as Record<string, any>),
      lastUpdate: metrics.lastUpdate
    };
  },
  
  // State management helpers
  getSnapshot() {
    return {
      documents: [...documents],
      uploading: [...uploading],
      selected,
      currentUserId
    };
  },
  
  // Reset to initial state (for testing)
  reset(): void {
    documents = [];
    uploading = [];
    selected = null;
    currentUserId = null;
  },
  
  // Validation helpers
  validateDocument(document: Partial<Document>): boolean {
    return !!(
      document.name &&
      document.size &&
      document.type &&
      document.status
    );
  },
  
  hasValidUpload(documentId: string): boolean {
    const upload = this.getUploadProgress(documentId);
    return upload ? upload.stage !== 'error' : false;
  }
};