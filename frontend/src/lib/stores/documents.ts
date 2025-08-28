import { writable, derived } from 'svelte/store';
import type { Document, DocumentState, UploadProgress } from '$lib/types';
import { generateId } from '$lib/utils';

const defaultDocumentState: DocumentState = {
  documents: [],
  uploading: [],
  selected: null,
  currentUserId: null
};

function createDocumentStore() {
  const { subscribe, set, update } = writable<DocumentState>(defaultDocumentState);

  return {
    subscribe,
    
    // Document management
    addDocument: (document: Omit<Document, 'id' | 'uploadedAt'>) => {
      const newDocument: Document = {
        ...document,
        id: generateId(),
        uploadedAt: new Date()
      };
      
      update(state => ({
        ...state,
        documents: [...state.documents, newDocument]
      }));
      
      return newDocument.id;
    },
    
    updateDocument: (id: string, updates: Partial<Document>) =>
      update(state => ({
        ...state,
        documents: state.documents.map(doc => 
          doc.id === id ? { ...doc, ...updates } : doc
        )
      })),
    
    removeDocument: (id: string) =>
      update(state => ({
        ...state,
        documents: state.documents.filter(doc => doc.id !== id),
        selected: state.selected === id ? null : state.selected
      })),
    
    selectDocument: (id: string | null) =>
      update(state => ({ ...state, selected: id })),
    
    // Upload progress management
    addUploadProgress: (progress: UploadProgress) =>
      update(state => ({
        ...state,
        uploading: [...state.uploading, progress]
      })),
    
    updateUploadProgress: (documentId: string, updates: Partial<UploadProgress>) =>
      update(state => ({
        ...state,
        uploading: state.uploading.map(upload =>
          upload.documentId === documentId 
            ? { ...upload, ...updates }
            : upload
        )
      })),
    
    removeUploadProgress: (documentId: string) =>
      update(state => ({
        ...state,
        uploading: state.uploading.filter(upload => 
          upload.documentId !== documentId
        )
      })),
    
    // User context management
    setCurrentUser: (userId: string | null) =>
      update(state => {
        // If user changed, clear all data
        if (state.currentUserId !== userId) {
          return {
            ...defaultDocumentState,
            currentUserId: userId
          };
        }
        return { ...state, currentUserId: userId };
      }),

    // Bulk operations
    clearAll: () => set(defaultDocumentState),
    
    clearCompleted: () =>
      update(state => ({
        ...state,
        documents: state.documents.filter(doc => doc.status !== 'completed')
      }))
  };
}

export const documentStore = createDocumentStore();

// Derived stores
export const selectedDocument = derived(
  documentStore,
  $documentStore => $documentStore.documents.find(doc => doc.id === $documentStore.selected)
);

export const documentCount = derived(
  documentStore,
  $documentStore => $documentStore.documents.length
);

export const processingDocuments = derived(
  documentStore,
  $documentStore => $documentStore.documents.filter(doc => 
    doc.status === 'processing' || doc.status === 'uploading'
  )
);

export const completedDocuments = derived(
  documentStore,
  $documentStore => $documentStore.documents.filter(doc => doc.status === 'completed')
);

export const errorDocuments = derived(
  documentStore,
  $documentStore => $documentStore.documents.filter(doc => doc.status === 'error')
);

export const isUploading = derived(
  documentStore,
  $documentStore => $documentStore.uploading.length > 0
);