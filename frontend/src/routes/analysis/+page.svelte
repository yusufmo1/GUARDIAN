<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import DocumentUpload from '$lib/components/upload/DocumentUpload.svelte';
  import UploadProgress from '$lib/components/upload/UploadProgress.svelte';
  import ProtocolAnalyzer from '$lib/components/analysis/ProtocolAnalyzer.svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { documentStore, isUploading, isAuthenticated, currentUser } from '$lib/stores';
  import { toastStore } from '$lib/stores';
  import { formatFileSize, formatDate } from '$lib/utils';
  import { requireAuthentication } from '$lib/utils/auth';
  import { session as sessionApi, GuardianApiError } from '$lib/services/api';
  import type { Document } from '$lib/types';
  import type { DocumentInfo } from '$lib/services/api';

  let documents: Document[] = [];
  let uploadProgress: any[] = [];
  let loading = false;
  let showAnalyzer = false;
  let selectedDocumentId: string | undefined = undefined;

  // Authentication state
  $: authenticated = $isAuthenticated;
  $: user = $currentUser;

  // Subscribe to stores
  $: documents = $documentStore.documents;
  $: uploadProgress = $documentStore.uploading;

  // Redirect to login if not authenticated
  $: if (!authenticated) {
    goto('/login?redirect=/analysis');
  }

  // Load existing documents on mount
  onMount(async () => {
    // Only load documents if authenticated
    if (authenticated) {
      await loadDocuments();
    }
  });

  async function loadDocuments() {
    if (!authenticated) return;
    
    try {
      loading = true;
      const response = await sessionApi.listDocuments({ 
        processed_only: false,
        per_page: 50 
      });
      
      if (response.data) {
        // Convert API documents to store format
        response.data.forEach(docInfo => {
          documentStore.addDocument({
            id: docInfo.document_id,
            name: docInfo.filename,
            size: docInfo.file_metadata.file_size,
            type: docInfo.file_metadata.file_type,
            uploadedAt: new Date(docInfo.created_at),
            status: docInfo.processing_info.status as any,
            analysisId: docInfo.document_id
          });
        });
      }
    } catch (error) {
      if (error instanceof GuardianApiError) {
        toastStore.error('Failed to Load Documents', error.message);
      } else {
        toastStore.error('Failed to Load Documents', 'Could not connect to server');
      }
    } finally {
      loading = false;
    }
  }

  async function handleUpload(event: CustomEvent<{ files: File[] }>) {
    if (!authenticated) {
      toastStore.error('Authentication Required', 'Please sign in to upload documents');
      goto('/login?redirect=/analysis');
      return;
    }
    
    const { files } = event.detail;
    
    for (const file of files) {
      // Add document to store with temporary ID
      const tempId = crypto.randomUUID();
      documentStore.addDocument({
        id: tempId,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'uploading',
        uploadedAt: new Date()
      });

      // Add upload progress tracking
      documentStore.addUploadProgress({
        documentId: tempId,
        progress: 0,
        stage: 'uploading',
        message: 'Starting upload...'
      });

      try {
        // Upload document via API
        await uploadDocument(tempId, file);
      } catch (error) {
        documentStore.updateDocument(tempId, { status: 'error' });
        documentStore.removeUploadProgress(tempId);
        
        if (error instanceof GuardianApiError) {
          toastStore.error('Upload Failed', error.message);
        } else {
          toastStore.error('Upload Failed', 'An unexpected error occurred');
        }
      }
    }

    toastStore.success('Upload Started', `${files.length} file(s) queued for processing`);
  }

  function handleUploadError(event: CustomEvent<{ message: string }>) {
    const { message } = event.detail;
    toastStore.error('Upload Error', message);
  }

  // Real API upload function
  async function uploadDocument(tempId: string, file: File) {
    try {
      // Update progress for upload start
      documentStore.updateUploadProgress(tempId, {
        progress: 10,
        stage: 'uploading',
        message: 'Uploading file...'
      });

      // Upload document via API
      const response = await sessionApi.uploadDocument(file, {
        documentType: 'protocol',
        processImmediately: true
      });

      if (response.data) {
        const documentInfo = response.data;
        
        // Update to processing stage
        documentStore.updateUploadProgress(tempId, {
          progress: 30,
          stage: 'processing',
          message: 'Processing document...'
        });

        // Update document with real ID and info
        documentStore.updateDocument(tempId, {
          id: documentInfo.document_id,
          status: documentInfo.processing_info.status as any,
          analysisId: documentInfo.document_id
        });

        // Poll for completion if processing immediately
        if (documentInfo.processing_info.status === 'processing') {
          await pollDocumentStatus(tempId, documentInfo.document_id);
        } else if (documentInfo.processing_info.status === 'completed') {
          // Already completed
          documentStore.updateUploadProgress(tempId, {
            progress: 100,
            stage: 'completed',
            message: 'Processing complete'
          });
          
          documentStore.updateDocument(tempId, { status: 'completed' });
          documentStore.removeUploadProgress(tempId);
          toastStore.success('Processing Complete', `${file.name} is ready for analysis`);
        }
      }
    } catch (error) {
      throw error;
    }
  }

  // Poll document status until completed
  async function pollDocumentStatus(tempId: string, documentId: string) {
    const maxAttempts = 30; // 5 minutes with 10 second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        attempts++;
        const response = await sessionApi.getDocument(documentId);
        
        if (response.data) {
          const docInfo = response.data;
          const progress = Math.min(30 + (attempts * 2), 90); // Gradual progress increase
          
          documentStore.updateUploadProgress(tempId, {
            progress,
            stage: docInfo.processing_info.status === 'completed' ? 'completed' : 'processing',
            message: docInfo.processing_info.error_message || 'Processing document...'
          });

          if (docInfo.processing_info.status === 'completed') {
            documentStore.updateUploadProgress(tempId, {
              progress: 100,
              stage: 'completed',
              message: 'Processing complete'
            });
            
            documentStore.updateDocument(tempId, { status: 'completed' });
            documentStore.removeUploadProgress(tempId);
            toastStore.success('Processing Complete', `Document is ready for analysis`);
            return;
          } else if (docInfo.processing_info.status === 'failed') {
            throw new Error(docInfo.processing_info.error_message || 'Processing failed');
          }
        }

        if (attempts < maxAttempts) {
          setTimeout(poll, 10000); // Poll every 10 seconds
        } else {
          throw new Error('Processing timeout - please check status manually');
        }
      } catch (error) {
        documentStore.updateDocument(tempId, { status: 'error' });
        documentStore.removeUploadProgress(tempId);
        toastStore.error('Processing Failed', error instanceof Error ? error.message : 'Unknown error');
      }
    };

    setTimeout(poll, 5000); // Start polling after 5 seconds
  }

  async function removeDocument(id: string) {
    if (!authenticated) return;
    
    try {
      // Call API to delete document if it's a real document (not temp)
      if (!id.includes('-')) { // Real document IDs from backend won't have temp format
        await sessionApi.deleteDocument(id);
      }
      
      documentStore.removeDocument(id);
      toastStore.info('Document Removed', 'Document has been removed from the queue');
    } catch (error) {
      if (error instanceof GuardianApiError) {
        toastStore.error('Delete Failed', error.message);
      } else {
        // Remove from local store anyway
        documentStore.removeDocument(id);
        toastStore.info('Document Removed', 'Document removed locally (server may be unavailable)');
      }
    }
  }

  function analyzeDocument(document: Document) {
    selectedDocumentId = document.analysisId || document.id;
    showAnalyzer = true;
    toastStore.info('Analysis Ready', `Ready to analyze ${document.name}`);
  }

  function closeAnalyzer() {
    showAnalyzer = false;
    selectedDocumentId = undefined;
  }

  function handleAnalysisComplete(event: CustomEvent<{ result: any }>) {
    const { result } = event.detail;
    toastStore.success('Analysis Complete', 'Protocol analysis completed successfully');
    // You can handle the analysis result here if needed
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'completed': return 'var(--color-success-600)';
      case 'processing': return 'var(--color-warning-600)';
      case 'uploading': return 'var(--color-primary-600)';
      case 'error': return 'var(--color-error-600)';
      default: return 'var(--color-gray-600)';
    }
  }
</script>

<svelte:head>
  <title>Protocol Analysis - GUARDIAN</title>
</svelte:head>

<div class="analysis-page">
  <div class="page-header">
    <h1>Protocol Analysis</h1>
    {#if authenticated && user}
      <p>Welcome back, {user.name || user.email}! Upload your pharmaceutical protocol documents for compliance analysis against global regulatory standards.</p>
    {:else}
      <p>Upload your pharmaceutical protocol documents for compliance analysis against global regulatory standards.</p>
    {/if}
  </div>

  <!-- Upload Section -->
  <section class="upload-section">
    <Card>
      {#if authenticated}
        <DocumentUpload
          multiple={true}
          disabled={$isUploading}
          on:upload={handleUpload}
          on:error={handleUploadError}
        />
      {:else}
        <div class="auth-required-upload">
          <Icon name="lock" size={48} color="var(--color-gray-400)" />
          <h3>Authentication Required</h3>
          <p>Please sign in to upload and analyze your pharmaceutical protocol documents.</p>
          <Button variant="primary" on:click={() => goto('/login?redirect=/analysis')}>
            <Icon name="login" size={16} />
            Sign In to Continue
          </Button>
        </div>
      {/if}
    </Card>
  </section>

  <!-- Progress Section -->
  {#if uploadProgress.length > 0}
    <section class="progress-section">
      <h2>Processing Documents</h2>
      {#each uploadProgress as progress (progress.documentId)}
        <UploadProgress {progress} />
      {/each}
    </section>
  {/if}

  <!-- Documents Section -->
  {#if documents.length > 0}
    <section class="documents-section">
      <div class="section-header">
        <h2>Uploaded Documents</h2>
        <div class="section-actions">
          <Button 
            variant="secondary" 
            size="sm"
            on:click={() => documentStore.clearCompleted()}
            disabled={documents.filter(d => d.status === 'completed').length === 0}
          >
            Clear Completed
          </Button>
        </div>
      </div>

      <div class="documents-list">
        {#each documents as document (document.id)}
          <Card hover={true}>
            <div class="document-item">
              <div class="document-icon">
                <Icon name="file" size={24} />
              </div>

              <div class="document-info">
                <h3 class="document-name">{document.name}</h3>
                <div class="document-meta">
                  <span class="document-size">{formatFileSize(document.size)}</span>
                  <span class="document-date">Uploaded {formatDate(document.uploadedAt)}</span>
                  <span 
                    class="document-status"
                    style="color: {getStatusColor(document.status)}"
                  >
                    {document.status}
                  </span>
                </div>
              </div>

              <div class="document-actions">
                {#if document.status === 'completed'}
                  <Button
                    variant="primary"
                    size="sm"
                    on:click={() => analyzeDocument(document)}
                  >
                    <Icon name="analysis" size={16} />
                    Analyze
                  </Button>
                {/if}
                
                <Button
                  variant="secondary"
                  size="sm"
                  on:click={() => removeDocument(document.id)}
                >
                  <Icon name="x" size={16} />
                  Remove
                </Button>
              </div>
            </div>
          </Card>
        {/each}
      </div>
    </section>
  {/if}

  <!-- Protocol Analyzer Section -->
  {#if showAnalyzer}
    <section class="analyzer-section">
      <div class="analyzer-header">
        <Button
          variant="secondary"
          size="sm"
          on:click={closeAnalyzer}
        >
          <Icon name="arrow-left" size={16} />
          Back to Documents
        </Button>
      </div>
      
      <ProtocolAnalyzer 
        documentId={selectedDocumentId}
        on:analysis={handleAnalysisComplete}
      />
    </section>
  {/if}

  <!-- Empty State -->
  {#if documents.length === 0 && uploadProgress.length === 0 && !showAnalyzer}
    <section class="empty-state">
      <div class="empty-state-content">
        <Icon name="file" size={64} color="var(--color-gray-400)" />
        <h3>No Documents Yet</h3>
        <p>Upload your first protocol document to get started with compliance analysis.</p>
      </div>
    </section>
  {/if}
</div>

<style>
  .analysis-page {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
  }

  .page-header {
    text-align: center;
    margin-bottom: var(--space-4);
  }

  .page-header h1 {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-4);
  }

  .page-header p {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    max-width: var(--max-width-2xl);
    margin: 0 auto;
  }

  .section-header {
    display: flex;
    justify-content: between;
    align-items: center;
    margin-bottom: var(--space-6);
  }

  .section-header h2 {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-semibold);
    margin: 0;
  }

  .section-actions {
    display: flex;
    gap: var(--space-3);
  }

  .documents-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .document-item {
    display: flex;
    align-items: center;
    gap: var(--space-4);
  }

  .document-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    background: var(--color-primary-100);
    border-radius: var(--radius-lg);
    color: var(--color-primary-600);
    flex-shrink: 0;
  }

  .document-info {
    flex: 1;
    min-width: 0;
  }

  .document-name {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0 0 var(--space-2) 0;
    word-break: break-word;
  }

  .document-meta {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    flex-wrap: wrap;
  }

  .document-status {
    font-weight: var(--font-weight-medium);
    text-transform: capitalize;
  }

  .document-actions {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    flex-shrink: 0;
  }

  .empty-state {
    display: flex;
    justify-content: center;
    padding: var(--space-16) var(--space-8);
  }

  .empty-state-content {
    text-align: center;
    max-width: var(--max-width-md);
  }

  .empty-state-content h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin: var(--space-4) 0;
    color: var(--color-text);
  }

  .empty-state-content p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  .analyzer-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .analyzer-header {
    display: flex;
    justify-content: flex-start;
  }

  /* Authentication required upload styles */
  .auth-required-upload {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
    min-height: 300px;
    justify-content: center;
  }

  .auth-required-upload h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
    margin: 0;
  }

  .auth-required-upload p {
    color: var(--color-text-secondary);
    margin: 0;
    max-width: 400px;
    line-height: var(--line-height-relaxed);
  }

  @media (max-width: 768px) {
    .page-header h1 {
      font-size: var(--font-size-2xl);
    }

    .section-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-3);
    }

    .document-item {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-3);
    }

    .document-actions {
      width: 100%;
      justify-content: flex-end;
    }

    .empty-state {
      padding: var(--space-12) var(--space-4);
    }
  }
</style>