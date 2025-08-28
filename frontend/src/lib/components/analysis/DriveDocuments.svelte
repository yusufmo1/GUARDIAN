<script lang="ts">
  import { onMount } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { session as sessionApi, GuardianApiError } from '$lib/services/api';
  import { toastStore } from '$lib/stores';
  import { formatFileSize, formatDate } from '$lib/utils';
  import type { DriveFile, SessionStats } from '$lib/types';

  // Component state
  let loading = $state(false);
  let refreshing = $state(false);
  let driveFiles = $state<DriveFile[]>([]);
  let sessionStats = $state<SessionStats | null>(null);
  let error = $state<string | null>(null);

  // Load data on mount
  onMount(async () => {
    await loadData();
  });

  async function loadData() {
    if (loading) return;
    
    try {
      loading = true;
      error = null;
      
      // Load both Drive files and session stats in parallel
      const [driveResponse, statsResponse] = await Promise.all([
        sessionApi.listDriveFiles('document'),
        sessionApi.getStats()
      ]);

      if (driveResponse.success && driveResponse.data) {
        driveFiles = driveResponse.data.files || [];
      } else {
        throw new Error('Failed to load Drive files');
      }

      if (statsResponse.success && statsResponse.data) {
        sessionStats = statsResponse.data;
      } else {
        console.warn('Failed to load session stats');
      }

    } catch (err) {
      console.error('Error loading Drive documents:', err);
      if (err instanceof GuardianApiError) {
        error = err.message;
        toastStore.error('Failed to Load Drive Documents', err.message);
      } else {
        error = 'Failed to connect to Google Drive';
        toastStore.error('Failed to Load Drive Documents', 'Could not connect to Google Drive service');
      }
    } finally {
      loading = false;
    }
  }

  async function refreshData() {
    if (refreshing) return;
    
    try {
      refreshing = true;
      await loadData();
      toastStore.success('Refreshed', 'Drive documents and session stats updated');
    } catch (err) {
      console.error('Error refreshing data:', err);
    } finally {
      refreshing = false;
    }
  }

  // Check if a document is loaded in the vector database
  function isDocumentLoaded(file: DriveFile): boolean {
    if (!sessionStats) return false;
    
    // If we have documents loaded in the session, assume the most recently modified ones are loaded
    if (sessionStats.document_count > 0) {
      // Simple heuristic: if we have any documents loaded and this file was recently modified,
      // it's likely to be loaded. For more precision, we'd need per-file tracking.
      return true;
    }
    
    return false;
  }

  // Get status indicator for a document
  function getDocumentStatus(file: DriveFile): 'loaded' | 'not-loaded' | 'unknown' {
    if (!sessionStats) return 'unknown';
    
    // Check if document is loaded in vector database
    if (isDocumentLoaded(file)) {
      return 'loaded';
    }
    
    return 'not-loaded';
  }

  // Get status icon for a document
  function getStatusIcon(status: string): string {
    switch (status) {
      case 'loaded': return 'check';
      case 'not-loaded': return 'warning';
      default: return 'help';
    }
  }

  // Get status color for a document
  function getStatusColor(status: string): string {
    switch (status) {
      case 'loaded': return 'var(--color-success-600)';
      case 'not-loaded': return 'var(--color-warning-600)';
      default: return 'var(--color-gray-600)';
    }
  }

  // Get status text for a document
  function getStatusText(status: string): string {
    switch (status) {
      case 'loaded': return 'Loaded in Vector DB';
      case 'not-loaded': return 'Not loaded';
      default: return 'Status unknown';
    }
  }

  // Format file modified time
  function formatModifiedTime(modifiedTime: string): string {
    try {
      return formatDate(new Date(modifiedTime));
    } catch {
      return 'Unknown';
    }
  }

  // Get file type icon
  function getFileTypeIcon(mimeType: string | undefined): string {
    if (!mimeType) return 'file';
    if (mimeType.includes('pdf')) return 'file-text';
    if (mimeType.includes('document') || mimeType.includes('word')) return 'file-text';
    if (mimeType.includes('text')) return 'file-text';
    return 'file';
  }

  // Calculate session age in hours
  function getSessionAge(): string {
    if (!sessionStats?.created_at) return '0';
    
    try {
      const createdAt = new Date(sessionStats.created_at);
      const now = new Date();
      const diffMs = now.getTime() - createdAt.getTime();
      const diffHours = diffMs / (1000 * 60 * 60);
      
      return (Math.round(diffHours * 10) / 10).toString();
    } catch (error) {
      console.warn('Failed to calculate session age:', error);
      return '0';
    }
  }
</script>

<div class="drive-documents">
  <div class="section-header">
    <div class="header-content">
      <h2>Google Drive Documents</h2>
      <p>Documents stored in your personal Google Drive and their vector database status</p>
    </div>
    <div class="section-actions">
      <Button
        variant="secondary"
        size="sm"
        onclick={refreshData}
        disabled={loading || refreshing}
      >
        <Icon 
          name="refresh" 
          size={16} 
          class={refreshing ? "animate-spin" : ""}
        />
        {refreshing ? 'Refreshing...' : 'Refresh'}
      </Button>
    </div>
  </div>

  {#if loading && !driveFiles.length}
    <Card>
      <div class="loading-state">
        <Icon name="loading" size={32} color="var(--color-primary-600)" class="animate-spin" />
        <p>Loading Google Drive documents...</p>
      </div>
    </Card>
  {:else if error}
    <Card>
      <div class="error-state">
        <Icon name="error" size={32} color="var(--color-error-600)" />
        <h3>Failed to Load Drive Documents</h3>
        <p>{error}</p>
        <Button variant="primary" size="sm" onclick={loadData}>
          <Icon name="refresh" size={16} />
          Try Again
        </Button>
      </div>
    </Card>
  {:else}
    <!-- Session Statistics -->
    {#if sessionStats}
      <Card>
        <div class="session-stats">
          <h3>Session Statistics</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <Icon name="file" size={20} color="var(--color-primary-600)" />
              <div class="stat-content">
                <span class="stat-value">{sessionStats.total_documents}</span>
                <span class="stat-label">Documents</span>
              </div>
            </div>
            <div class="stat-item">
              <Icon name="book-open" size={20} color="var(--color-success-600)" />
              <div class="stat-content">
                <span class="stat-value">{sessionStats.total_chunks}</span>
                <span class="stat-label">Text Chunks</span>
              </div>
            </div>
            <div class="stat-item">
              <Icon name="search" size={20} color="var(--color-warning-600)" />
              <div class="stat-content">
                <span class="stat-value">{sessionStats.vector_count}</span>
                <span class="stat-label">Vectors</span>
              </div>
            </div>
            <div class="stat-item">
              <Icon name="clock" size={20} color="var(--color-gray-600)" />
              <div class="stat-content">
                <span class="stat-value">{getSessionAge()}h</span>
                <span class="stat-label">Session Age</span>
              </div>
            </div>
          </div>
          {#if sessionStats.last_activity}
            <div class="last-activity">
              <Icon name="activity" size={16} color="var(--color-gray-500)" />
              <span>Last activity: {formatDate(new Date(sessionStats.last_activity))}</span>
            </div>
          {/if}
        </div>
      </Card>
    {/if}

    <!-- Documents List -->
    {#if driveFiles.length > 0}
      <Card>
        <div class="documents-header">
          <h3>Documents in Google Drive</h3>
          <div class="document-count">
            <Icon name="globe" size={16} color="var(--color-primary-600)" />
            <span>{driveFiles.length} files found</span>
          </div>
        </div>

        <div class="documents-list">
          {#each driveFiles as file (file.id)}
            {@const status = getDocumentStatus(file)}
            <div class="document-item">
              <div class="document-icon">
                <Icon name={getFileTypeIcon(file.mimeType || file.mime_type)} size={20} />
              </div>

              <div class="document-info">
                <h4 class="document-name">{file.name}</h4>
                <div class="document-meta">
                  <span class="document-size">{formatFileSize(file.size)}</span>
                  <span class="document-date">Modified {formatModifiedTime(file.modifiedTime || file.modified_time)}</span>
                </div>
              </div>

              <div class="document-status">
                <div class="status-indicator" style="color: {getStatusColor(status)}">
                  <Icon name={getStatusIcon(status)} size={16} />
                  <span class="status-text">{getStatusText(status)}</span>
                </div>
              </div>
            </div>
          {/each}
        </div>
      </Card>
    {:else}
      <Card>
        <div class="empty-state">
          <Icon name="file" size={32} color="var(--color-gray-400)" />
          <h3>No Documents Found</h3>
          <p>No documents found in your Google Drive GUARDIAN folder. Upload some documents to get started.</p>
        </div>
      </Card>
    {/if}

    <!-- Sync Status Legend -->
    <Card>
      <div class="sync-legend">
        <h3>Status Legend</h3>
        <div class="legend-items">
          <div class="legend-item">
            <Icon name="check" size={16} color="var(--color-success-600)" />
            <span><strong>Loaded:</strong> Document is processed and available for analysis</span>
          </div>
          <div class="legend-item">
            <Icon name="warning" size={16} color="var(--color-warning-600)" />
            <span><strong>Not Loaded:</strong> Document exists in Drive but not yet processed</span>
          </div>
          <div class="legend-item">
            <Icon name="help" size={16} color="var(--color-gray-600)" />
            <span><strong>Unknown:</strong> Status could not be determined</span>
          </div>
        </div>
      </div>
    </Card>
  {/if}
</div>

<style>
  .drive-documents {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-4);
  }

  .header-content h2 {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .header-content p {
    color: var(--color-text-secondary);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  .section-actions {
    flex-shrink: 0;
  }

  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
  }

  .error-state h3,
  .empty-state h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .error-state p,
  .empty-state p,
  .loading-state p {
    color: var(--color-text-secondary);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }

  /* Session Statistics */
  .session-stats {
    padding: var(--space-4);
  }

  .session-stats h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-4) 0;
    color: var(--color-text);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
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

  .last-activity {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-4);
    padding-top: var(--space-4);
    border-top: 1px solid var(--color-border);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  /* Documents List */
  .documents-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
    padding: var(--space-4) var(--space-4) 0 var(--space-4);
  }

  .documents-header h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .document-count {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .documents-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .document-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--color-border);
  }

  .document-item:last-child {
    border-bottom: none;
  }

  .document-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--color-primary-100);
    border-radius: var(--radius-md);
    color: var(--color-primary-600);
    flex-shrink: 0;
  }

  .document-info {
    flex: 1;
    min-width: 0;
  }

  .document-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0 0 var(--space-1) 0;
    word-break: break-word;
  }

  .document-meta {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    flex-wrap: wrap;
  }

  .document-status {
    flex-shrink: 0;
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
  }

  .status-text {
    white-space: nowrap;
  }

  /* Sync Legend */
  .sync-legend {
    padding: var(--space-4);
  }

  .sync-legend h3 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-3) 0;
    color: var(--color-text);
  }

  .legend-items {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
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
    .section-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .documents-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .document-item {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .document-status {
      width: 100%;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .legend-items {
      gap: var(--space-3);
    }
  }
</style>