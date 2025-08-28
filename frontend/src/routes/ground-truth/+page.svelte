<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import GroundTruthUpload from '$lib/components/upload/GroundTruthUpload.svelte';
  import GroundTruthManager from '$lib/components/analysis/GroundTruthManager.svelte';
  import { authState, toastStore } from '$lib/stores';
  import { session as sessionApi, GuardianApiError } from '$lib/services/api';
  import { requireAuthentication } from '$lib/utils/auth';
  import type { DocumentInfo, SessionStats } from '$lib/types';

  // Svelte 5 runes for reactive state
  let loading = $state(false);
  let sessionInitialized = $state(false);
  let initializingSession = $state(false);
  let groundTruthDocuments = $state<DocumentInfo[]>([]);
  let sessionStats = $state<SessionStats | null>(null);
  let navigationInProgress = $state(false);
  let pageInitialized = $state(false);
  let uploadComponent = $state<any>(null);

  // Derived state using $derived
  const isAuthenticated = $derived(authState.authenticated);
  const user = $derived(authState.user);
  const documentCount = $derived(groundTruthDocuments.length);
  const hasDocuments = $derived(documentCount > 0);

  // Handle initial page load - SINGLE EXECUTION ONLY
  onMount(() => {
    if (pageInitialized) return;
    pageInitialized = true;
    
    // Break reactive chain
    setTimeout(async () => {
      try {
        console.log('Ground Truth page: Checking authentication state...');
        
        // Wait for auth to complete if still loading
        if (authState.loading) {
          console.log('Ground Truth page: Authentication still loading, waiting...');
          
          let attempts = 0;
          while (attempts < 20) {
            await new Promise(resolve => setTimeout(resolve, 100));
            if (!authState.loading) break;
            attempts++;
          }
        }
        
        if (authState.authenticated) {
          console.log('Ground Truth page: Authenticated, initializing session');
          await initializeSession();
          await loadGroundTruthDocuments();
        } else if (!navigationInProgress) {
          console.log('Ground Truth page: Not authenticated, redirecting to login');
          navigationInProgress = true;
          goto('/login?redirect=/ground-truth');
        }
      } catch (error) {
        console.error('Ground Truth page initialization error:', error);
      }
    }, 0);
  });

  async function initializeSession() {
    if (sessionInitialized || initializingSession) return;
    
    try {
      initializingSession = true;
      console.log('Initializing session for ground truth document management...');
      
      const response = await sessionApi.initialize();
      
      if (response.success) {
        sessionInitialized = true;
        console.log('Session initialized successfully:', response.data);
        toastStore.success('Session Ready', 'You can now upload and manage ground truth documents');
      } else {
        throw new Error('Failed to initialize session');
      }
    } catch (error) {
      console.error('Session initialization error:', error);
      if (error instanceof GuardianApiError) {
        toastStore.error('Session Error', error.message);
      } else {
        toastStore.error('Session Error', 'Failed to initialize document session. Please refresh the page.');
      }
    } finally {
      initializingSession = false;
    }
  }

  async function loadGroundTruthDocuments() {
    if (!isAuthenticated) return;
    
    try {
      loading = true;
      
      // Load session stats to get ground truth document information
      const statsResponse = await sessionApi.getStats();
      if (statsResponse.success && statsResponse.data) {
        sessionStats = statsResponse.data;
        console.log('Ground truth session stats:', statsResponse.data);
      }

      // In a future implementation, we would call a filtered endpoint for ground truth only
      // For now, we'll use the general Drive files endpoint
      const driveResponse = await sessionApi.listDriveFiles('document');
      if (driveResponse.success && driveResponse.data) {
        // Transform DriveFile[] to DocumentInfo[] to match GroundTruthManager expectations
        const driveFiles = driveResponse.data.files || [];
        
        // Filter out folders and only keep actual documents
        const actualDocuments = driveFiles.filter(file => {
          // Check if it has a file extension (not a folder)
          const hasExtension = file.name && file.name.includes('.');
          // Check if it has a size (folders typically don't have size)
          const hasSize = file.size && file.size !== '0';
          // Check if it's not a folder type
          const notFolder = !file.mimeType?.includes('folder') && !file.mime_type?.includes('folder');
          
          return hasExtension && hasSize && notFolder;
        });
        
        groundTruthDocuments = actualDocuments.map(file => ({
          id: file.id,
          name: file.name,
          size: file.size ? parseInt(file.size) : 0, // Convert string to number, default to 0
          type: file.mimeType || file.mime_type || 'application/octet-stream',
          uploadedAt: new Date(file.createdTime), // Use createdTime, not created_time
          modifiedTime: file.modifiedTime, // Use modifiedTime, not modified_time
          status: 'completed' as const,
          // Add any additional DocumentInfo fields if needed
          analysisId: undefined
        }));
      }
      
    } catch (error) {
      console.error('Error loading ground truth documents:', error);
      if (error instanceof GuardianApiError) {
        toastStore.error('Failed to Load Documents', error.message);
      } else {
        toastStore.error('Failed to Load Documents', 'Could not connect to server');
      }
    } finally {
      loading = false;
    }
  }

  async function handleGroundTruthUpload(event: CustomEvent<{ files: File[], category: string }>) {
    console.log('Ground Truth Page: handleGroundTruthUpload called', event.detail);
    
    if (!isAuthenticated) {
      console.log('Ground Truth Page: User not authenticated');
      toastStore.error('Authentication Required', 'Please sign in to upload documents');
      return;
    }

    if (!sessionInitialized) {
      console.log('Ground Truth Page: Session not initialized, initializing...');
      await initializeSession();
      if (!sessionInitialized) {
        console.log('Ground Truth Page: Session initialization failed');
        toastStore.error('Session Error', 'Failed to initialize session. Please refresh the page.');
        return;
      }
    }

    const { files, category } = event.detail;
    
    try {
      console.log(`Ground Truth Page: Uploading ${files.length} ground truth documents (category: ${category})`);
      
      // For now, we'll use the existing upload endpoint
      // TODO: Use document type specific endpoint when implemented
      const response = await sessionApi.uploadDocuments(files);
      
      if (response.success) {
        // Refresh the document list
        await loadGroundTruthDocuments();
        
        // Signal completion to upload component
        if (uploadComponent && uploadComponent.completeProcessing) {
          uploadComponent.completeProcessing(true);
        }
      }
    } catch (error) {
      console.error('Ground truth upload error:', error);
      
      const errorMessage = error instanceof GuardianApiError ? error.message : 'An unexpected error occurred';
      
      // Signal error to upload component
      if (uploadComponent && uploadComponent.completeProcessing) {
        uploadComponent.completeProcessing(false, errorMessage);
      }
      
      toastStore.error('Upload Failed', errorMessage);
    }
  }

  function handleUploadError(event: CustomEvent<{ message: string }>) {
    const { message } = event.detail;
    toastStore.error('Upload Error', message);
  }

  async function refreshDocuments() {
    await loadGroundTruthDocuments();
    toastStore.success('Refreshed', 'Ground truth documents updated');
  }

  function navigateToProtocolAnalysis() {
    goto('/protocols');
  }
</script>

<svelte:head>
  <title>Ground Truth Documents - GUARDIAN</title>
</svelte:head>

<div class="ground-truth-page">
  <div class="page-header">
    <div class="header-content">
      <h1>
        <Icon name="book-open" size={32} color="var(--color-primary-600)" />
        Ground Truth Documents
      </h1>
      {#if isAuthenticated && user}
        <p>Welcome back, {user.name || user.email}! Manage your regulatory standards and compliance reference documents here.</p>
      {:else}
        <p>Upload and organize regulatory standards, analytical methods, and compliance reference documents for compliance analysis.</p>
      {/if}
    </div>
    
    <div class="header-actions">
      <Button variant="secondary" onclick={navigateToProtocolAnalysis}>
        <Icon name="analysis" size={16} />
        Analyze Protocols
      </Button>
    </div>
  </div>

  <!-- Quick Stats Section -->
  {#if sessionStats && isAuthenticated}
    <Card>
      <div class="stats-section">
        <h3>
          <Icon name="activity" size={20} />
          Ground Truth Library Status
        </h3>
        <div class="stats-grid">
          <div class="stat-item">
            <Icon name="file" size={20} color="var(--color-primary-600)" />
            <div class="stat-content">
              <span class="stat-value">{sessionStats.total_documents}</span>
              <span class="stat-label">Reference Documents</span>
            </div>
          </div>
          <div class="stat-item">
            <Icon name="book-open" size={20} color="var(--color-success-600)" />
            <div class="stat-content">
              <span class="stat-value">{sessionStats.total_chunks}</span>
              <span class="stat-label">Text Sections</span>
            </div>
          </div>
          <div class="stat-item">
            <Icon name="search" size={20} color="var(--color-warning-600)" />
            <div class="stat-content">
              <span class="stat-value">{sessionStats.vector_count}</span>
              <span class="stat-label">Searchable Vectors</span>
            </div>
          </div>
          <div class="stat-item">
            <Icon name="shield" size={20} color="var(--color-secondary-600)" />
            <div class="stat-content">
              <span class="stat-value">{sessionStats.analyses_count || 0}</span>
              <span class="stat-label">Compliance Checks</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  {/if}

  <!-- Upload Section -->
  <section class="upload-section">
    <Card>
      {#if isAuthenticated}
        {#if initializingSession}
          <div class="session-initializing">
            <Icon name="loading" size={48} color="var(--color-primary-600)" class="animate-spin" />
            <h3>Initializing Ground Truth Session</h3>
            <p>Setting up your secure reference document workspace...</p>
          </div>
        {:else}
          <GroundTruthUpload
            bind:this={uploadComponent}
            disabled={!sessionInitialized}
            on:upload={handleGroundTruthUpload}
            on:error={handleUploadError}
          />
        {/if}
      {:else}
        <div class="auth-required-upload">
          <Icon name="lock" size={48} color="var(--color-gray-400)" />
          <h3>Authentication Required</h3>
          <p>Please sign in to upload and manage your ground truth reference documents.</p>
          <Button variant="primary" onclick={() => {
            if (!navigationInProgress) {
              navigationInProgress = true;
              goto('/login?redirect=/ground-truth');
            }
          }}>
            <Icon name="login" size={16} />
            Sign In to Continue
          </Button>
        </div>
      {/if}
    </Card>
  </section>

  <!-- Document Management Section -->
  {#if isAuthenticated && sessionInitialized}
    <section class="management-section">
      <div class="section-header">
        <h2>Ground Truth Library</h2>
        <div class="section-actions">
          <Button 
            variant="secondary" 
            size="sm"
            onclick={refreshDocuments}
            disabled={loading}
          >
            <Icon name="refresh" size={16} class={loading ? "animate-spin" : ""} />
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </div>

      <GroundTruthManager 
        documents={groundTruthDocuments}
        sessionStats={sessionStats}
        {loading}
        on:refresh={refreshDocuments}
      />
    </section>
  {/if}

  <!-- Empty State -->
  {#if !hasDocuments && !loading && isAuthenticated && sessionInitialized}
    <section class="empty-state">
      <div class="empty-state-content">
        <Icon name="book-open" size={64} color="var(--color-gray-400)" />
        <h3>No Ground Truth Documents Yet</h3>
        <p>Upload your first regulatory standard or compliance reference document to build your compliance library.</p>
        <div class="empty-state-suggestions">
          <h4>Recommended Document Types:</h4>
          <ul>
            <li>Regulatory standards monographs</li>
            <li>Analytical method standards</li>
            <li>Quality control procedures</li>
            <li>Regulatory guidance documents</li>
          </ul>
        </div>
      </div>
    </section>
  {/if}

  <!-- Information Section -->
  <section class="info-section">
    <Card>
      <div class="info-content">
        <h3>
          <Icon name="info" size={20} />
          About Ground Truth Documents
        </h3>
        <div class="info-grid">
          <div class="info-item">
            <Icon name="shield" size={24} color="var(--color-primary-600)" />
            <div>
              <h4>Reference Standards</h4>
              <p>Upload regulatory monographs and compliance standards that serve as the authoritative reference for compliance analysis.</p>
            </div>
          </div>
          <div class="info-item">
            <Icon name="search" size={24} color="var(--color-secondary-600)" />
            <div>
              <h4>Smart Indexing</h4>
              <p>Documents are automatically processed and indexed using AI to enable intelligent similarity search against your protocols.</p>
            </div>
          </div>
          <div class="info-item">
            <Icon name="lock" size={24} color="var(--color-success-600)" />
            <div>
              <h4>Private & Secure</h4>
              <p>All documents are stored securely in your personal Google Drive with encrypted processing and zero permanent server storage.</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </section>
</div>

<style>
  .ground-truth-page {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-6);
    margin-bottom: var(--space-4);
  }

  .header-content {
    flex: 1;
  }

  .header-content h1 {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-4);
    color: var(--color-text);
  }

  .header-content p {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    max-width: var(--max-width-2xl);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }

  .header-actions {
    flex-shrink: 0;
  }

  .stats-section {
    padding: var(--space-4);
  }

  .stats-section h3 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-4) 0;
    color: var(--color-text);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: var(--space-4);
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
  }

  .stat-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .stat-value {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
  }

  .stat-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-6);
  }

  .section-header h2 {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .section-actions {
    display: flex;
    gap: var(--space-3);
  }

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

  .session-initializing {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8) var(--space-4);
    text-align: center;
    min-height: 300px;
    justify-content: center;
  }

  .session-initializing h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .session-initializing p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
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
    margin: 0 0 var(--space-6) 0;
  }

  .empty-state-suggestions {
    text-align: left;
    background: var(--color-gray-50);
    padding: var(--space-4);
    border-radius: var(--radius-lg);
  }

  .empty-state-suggestions h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    margin: 0 0 var(--space-3) 0;
    color: var(--color-text);
  }

  .empty-state-suggestions ul {
    margin: 0;
    padding-left: var(--space-5);
    color: var(--color-text-secondary);
  }

  .empty-state-suggestions li {
    margin-bottom: var(--space-1);
    line-height: var(--line-height-relaxed);
  }

  .info-section {
    margin-top: var(--space-8);
  }

  .info-content {
    padding: var(--space-6);
  }

  .info-content h3 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-6) 0;
    color: var(--color-text);
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-6);
  }

  .info-item {
    display: flex;
    gap: var(--space-3);
    align-items: flex-start;
  }

  .info-item h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .info-item p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  /* Loading animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-4);
    }

    .header-content h1 {
      font-size: var(--font-size-2xl);
      flex-direction: column;
      gap: var(--space-2);
    }

    .section-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-3);
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .info-grid {
      grid-template-columns: 1fr;
    }

    .empty-state {
      padding: var(--space-12) var(--space-4);
    }
  }
</style>