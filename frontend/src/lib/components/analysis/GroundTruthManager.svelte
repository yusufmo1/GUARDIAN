<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { formatFileSize, formatDate } from '$lib/utils';
  import type { DocumentInfo, SessionStats } from '$lib/types';

  interface Props {
    documents: DocumentInfo[];
    sessionStats: SessionStats | null;
    loading?: boolean;
  }

  let { documents, sessionStats, loading = false }: Props = $props();

  // Svelte 5 runes for state management
  let viewMode = $state<'grid' | 'list'>('list');
  let selectedCategory = $state<string>('all');
  let sortBy = $state<'name' | 'date' | 'size' | 'category'>('date');
  let sortOrder = $state<'asc' | 'desc'>('desc');
  let searchQuery = $state('');

  const dispatch = createEventDispatcher<{
    refresh: void;
  }>();

  // Document categories for filtering
  const documentCategories = [
    { value: 'all', label: 'All Categories' },
    { value: 'regulatory_standards', label: 'Regulatory Standards' },
    { value: 'analytical_method', label: 'Analytical Methods' },
    { value: 'quality_control', label: 'Quality Control' },
    { value: 'regulatory_guidance', label: 'Regulatory Guidance' },
    { value: 'ich_guideline', label: 'ICH Guidelines' },
    { value: 'pharmacopoeial_general', label: 'Pharmacopoeial General' }
  ];

  // Derived values using $derived.by for complex computations
  const filteredDocuments = $derived.by(() => {
    if (!documents || !Array.isArray(documents)) {
      return [];
    }
    
    let filtered = documents;

    // Filter by category
    if (selectedCategory !== 'all') {
      // Note: In real implementation, we'd filter by document.category
      // For now, we'll show all documents since the backend doesn't yet return category info
      filtered = documents;
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(doc => 
        doc?.name?.toLowerCase().includes(query)
      );
    }

    // Sort documents
    filtered = [...filtered].sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;

      switch (sortBy) {
        case 'name':
          aVal = a.name?.toLowerCase() || '';
          bVal = b.name?.toLowerCase() || '';
          break;
        case 'date':
          aVal = a.modifiedTime ? new Date(a.modifiedTime).getTime() : 0;
          bVal = b.modifiedTime ? new Date(b.modifiedTime).getTime() : 0;
          break;
        case 'size':
          aVal = a.size || 0;
          bVal = b.size || 0;
          break;
        case 'category':
          // For now, we'll sort by name since we don't have category info
          aVal = a.name?.toLowerCase() || '';
          bVal = b.name?.toLowerCase() || '';
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  });

  const documentCount = $derived(filteredDocuments?.length || 0);
  const hasDocuments = $derived((documents?.length || 0) > 0);
  const hasFilteredResults = $derived((filteredDocuments?.length || 0) > 0);

  function toggleSort(newSortBy: typeof sortBy) {
    if (sortBy === newSortBy) {
      sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      sortBy = newSortBy;
      sortOrder = 'desc';
    }
  }

  function getFileTypeIcon(fileName: string): string {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
        return 'file-text';
      case 'docx':
      case 'doc':
        return 'file-text';
      case 'txt':
        return 'file-text';
      default:
        return 'file';
    }
  }

  function getDocumentStatus(doc: DocumentInfo): 'loaded' | 'not-loaded' | 'processing' {
    // This is a simplified check - in a real implementation, we'd have proper status tracking
    if (sessionStats && sessionStats.total_documents > 0) {
      return 'loaded';
    }
    return 'not-loaded';
  }

  function getStatusColor(status: string): string {
    switch (status) {
      case 'loaded':
        return 'var(--color-success-600)';
      case 'processing':
        return 'var(--color-warning-600)';
      case 'not-loaded':
        return 'var(--color-gray-600)';
      default:
        return 'var(--color-gray-600)';
    }
  }

  function getStatusIcon(status: string): string {
    switch (status) {
      case 'loaded':
        return 'check';
      case 'processing':
        return 'loading';
      case 'not-loaded':
        return 'clock';
      default:
        return 'help';
    }
  }

  function getStatusText(status: string): string {
    switch (status) {
      case 'loaded':
        return 'Indexed & Ready';
      case 'processing':
        return 'Processing...';
      case 'not-loaded':
        return 'Not Indexed';
      default:
        return 'Unknown Status';
    }
  }

  function formatModifiedTime(modifiedTime: string | undefined): string {
    if (!modifiedTime) return 'Unknown';
    try {
      return formatDate(new Date(modifiedTime));
    } catch {
      return 'Unknown';
    }
  }

  function clearFilters() {
    searchQuery = '';
    selectedCategory = 'all';
    sortBy = 'date';
    sortOrder = 'desc';
  }

  function refreshDocuments() {
    dispatch('refresh');
  }
</script>

<div class="ground-truth-manager">
  {#if hasDocuments}
    <!-- Controls Bar -->
    <div class="controls-bar">
      <div class="search-section">
        <div class="search-input">
          <Icon name="search" size={16} />
          <input
            type="text"
            placeholder="Search ground truth documents..."
            bind:value={searchQuery}
          />
          {#if searchQuery}
            <button class="clear-search" onclick={() => searchQuery = ''}>
              <Icon name="x" size={14} />
            </button>
          {/if}
        </div>
      </div>

      <div class="filter-section">
        <select bind:value={selectedCategory}>
          {#each documentCategories as category}
            <option value={category.value}>{category.label}</option>
          {/each}
        </select>
      </div>

      <div class="view-controls">
        <button
          class="view-toggle"
          class:active={viewMode === 'list'}
          onclick={() => viewMode = 'list'}
          title="List view"
        >
          <Icon name="menu" size={16} />
        </button>
        <button
          class="view-toggle"
          class:active={viewMode === 'grid'}
          onclick={() => viewMode = 'grid'}
          title="Grid view"
        >
          <Icon name="clipboard" size={16} />
        </button>
      </div>
    </div>

    <!-- Results Info -->
    <div class="results-info">
      <div class="results-count">
        <span class="count-text">
          Showing {documentCount} of {documents.length} document{documents.length === 1 ? '' : 's'}
        </span>
        {#if searchQuery || selectedCategory !== 'all'}
          <Button variant="secondary" size="sm" onclick={clearFilters}>
            <Icon name="x" size={14} />
            Clear Filters
          </Button>
        {/if}
      </div>

      <!-- Sort Controls -->
      <div class="sort-controls">
        <span>Sort by:</span>
        <button
          class="sort-button"
          class:active={sortBy === 'name'}
          onclick={() => toggleSort('name')}
        >
          Name
          {#if sortBy === 'name'}
            <Icon name={sortOrder === 'asc' ? 'arrow-up' : 'arrow-down'} size={12} />
          {/if}
        </button>
        <button
          class="sort-button"
          class:active={sortBy === 'date'}
          onclick={() => toggleSort('date')}
        >
          Date
          {#if sortBy === 'date'}
            <Icon name={sortOrder === 'asc' ? 'arrow-up' : 'arrow-down'} size={12} />
          {/if}
        </button>
        <button
          class="sort-button"
          class:active={sortBy === 'size'}
          onclick={() => toggleSort('size')}
        >
          Size
          {#if sortBy === 'size'}
            <Icon name={sortOrder === 'asc' ? 'arrow-up' : 'arrow-down'} size={12} />
          {/if}
        </button>
      </div>
    </div>

    <!-- Documents Display -->
    {#if hasFilteredResults}
      <div class="documents-container" class:grid-view={viewMode === 'grid'}>
        {#each filteredDocuments as document (document.id)}
          {@const status = getDocumentStatus(document)}
          <Card hover={true}>
            <div class="document-item" class:grid-item={viewMode === 'grid'}>
              <div class="document-icon">
                <Icon name={getFileTypeIcon(document.name)} size={viewMode === 'grid' ? 32 : 24} />
              </div>

              <div class="document-info">
                <h4 class="document-name">{document.name}</h4>
                <div class="document-meta">
                  <span class="document-size">{formatFileSize(document.size || 0)}</span>
                  <span class="document-date">Modified {formatModifiedTime(document.modifiedTime)}</span>
                </div>
                {#if viewMode === 'grid'}
                  <div class="document-description">
                    Ground truth reference document for compliance analysis
                  </div>
                {/if}
              </div>

              <div class="document-status">
                <div class="status-indicator" style="color: {getStatusColor(status)}">
                  <Icon 
                    name={getStatusIcon(status)} 
                    size={16} 
                    class={status === 'processing' ? 'animate-spin' : ''}
                  />
                  <span class="status-text">{getStatusText(status)}</span>
                </div>
              </div>

              {#if viewMode === 'grid'}
                <div class="document-actions">
                  <Button variant="secondary" size="sm">
                    <Icon name="eye" size={14} />
                    View
                  </Button>
                  <Button variant="secondary" size="sm">
                    <Icon name="download" size={14} />
                    Download
                  </Button>
                </div>
              {/if}
            </div>
          </Card>
        {/each}
      </div>
    {:else}
      <!-- No Results -->
      <Card>
        <div class="no-results">
          <Icon name="search" size={48} color="var(--color-gray-400)" />
          <h3>No Documents Found</h3>
          <p>
            {#if searchQuery}
              No documents match your search for "{searchQuery}".
            {:else if selectedCategory !== 'all'}
              No documents found in the selected category.
            {:else}
              No ground truth documents available.
            {/if}
          </p>
          {#if searchQuery || selectedCategory !== 'all'}
            <Button variant="primary" onclick={clearFilters}>
              <Icon name="x" size={16} />
              Clear Filters
            </Button>
          {/if}
        </div>
      </Card>
    {/if}
  {:else if loading}
    <!-- Loading State -->
    <Card>
      <div class="loading-state">
        <Icon name="loading" size={32} color="var(--color-primary-600)" class="animate-spin" />
        <p>Loading ground truth documents...</p>
      </div>
    </Card>
  {:else}
    <!-- Empty State -->
    <Card>
      <div class="empty-state">
        <Icon name="book-open" size={64} color="var(--color-gray-400)" />
        <h3>No Ground Truth Documents</h3>
        <p>You haven't uploaded any ground truth documents yet. Upload some regulatory standards or compliance documents to get started.</p>
        <Button variant="primary" onclick={refreshDocuments}>
          <Icon name="refresh" size={16} />
          Refresh
        </Button>
      </div>
    </Card>
  {/if}
</div>

<style>
  .ground-truth-manager {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .controls-bar {
    display: flex;
    gap: var(--space-4);
    align-items: center;
    flex-wrap: wrap;
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .search-section {
    flex: 1;
    min-width: 250px;
  }

  .search-input {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-input input {
    width: 100%;
    padding: var(--space-2) var(--space-3) var(--space-2) var(--space-8);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
  }

  .search-input input:focus {
    outline: none;
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-primary-100);
  }

  .search-input :global(svg:first-child) {
    position: absolute;
    left: var(--space-2);
    color: var(--color-text-muted);
    pointer-events: none;
  }

  .clear-search {
    position: absolute;
    right: var(--space-2);
    background: none;
    border: none;
    cursor: pointer;
    color: var(--color-text-muted);
    padding: var(--space-1);
    border-radius: var(--radius-sm);
  }

  .clear-search:hover {
    background: var(--color-gray-100);
  }

  .filter-section select {
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    background: white;
  }

  .view-controls {
    display: flex;
    gap: var(--space-1);
    background: white;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-1);
  }

  .view-toggle {
    padding: var(--space-2);
    background: none;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    color: var(--color-text-muted);
    transition: all var(--transition-fast);
  }

  .view-toggle:hover {
    background: var(--color-gray-100);
    color: var(--color-text);
  }

  .view-toggle.active {
    background: var(--color-primary-100);
    color: var(--color-primary-600);
  }

  .results-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .results-count {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .count-text {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .sort-controls {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .sort-button {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    background: none;
    border: none;
    cursor: pointer;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    transition: all var(--transition-fast);
  }

  .sort-button:hover {
    background: var(--color-gray-100);
    color: var(--color-text);
  }

  .sort-button.active {
    color: var(--color-primary-600);
    font-weight: var(--font-weight-medium);
  }

  .documents-container {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .documents-container.grid-view {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: var(--space-4);
  }

  .document-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
  }

  .document-item.grid-item {
    flex-direction: column;
    align-items: flex-start;
    text-align: center;
    padding: var(--space-4);
  }

  .document-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: var(--color-primary-100);
    border-radius: var(--radius-md);
    color: var(--color-primary-600);
    flex-shrink: 0;
  }

  .grid-item .document-icon {
    width: 48px;
    height: 48px;
    margin-bottom: var(--space-3);
  }

  .document-info {
    flex: 1;
    min-width: 0;
  }

  .grid-item .document-info {
    text-align: center;
    width: 100%;
  }

  .document-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0 0 var(--space-2) 0;
    word-break: break-word;
  }

  .grid-item .document-name {
    font-size: var(--font-size-base);
  }

  .document-meta {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    flex-wrap: wrap;
  }

  .grid-item .document-meta {
    justify-content: center;
    flex-direction: column;
    gap: var(--space-1);
  }

  .document-description {
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    margin-top: var(--space-2);
    line-height: var(--line-height-relaxed);
  }

  .document-status {
    flex-shrink: 0;
  }

  .grid-item .document-status {
    margin-top: var(--space-3);
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

  .document-actions {
    display: flex;
    gap: var(--space-2);
    margin-top: var(--space-3);
    width: 100%;
    justify-content: center;
  }

  .loading-state,
  .empty-state,
  .no-results {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
  }

  .empty-state h3,
  .no-results h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .empty-state p,
  .no-results p,
  .loading-state p {
    color: var(--color-text-secondary);
    margin: 0;
    line-height: var(--line-height-relaxed);
    max-width: 400px;
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
    .controls-bar {
      flex-direction: column;
      align-items: stretch;
    }

    .search-section {
      min-width: auto;
    }

    .results-info {
      flex-direction: column;
      align-items: flex-start;
    }

    .sort-controls {
      flex-wrap: wrap;
    }

    .documents-container.grid-view {
      grid-template-columns: 1fr;
    }

    .document-item {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .document-status {
      width: 100%;
    }
  }
</style>