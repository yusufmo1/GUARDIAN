<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import type { SimilarSection, DocumentInfo } from '$lib/types';

  interface Props {
    similarSections: SimilarSection[];
    groundTruthDocuments: DocumentInfo[];
  }

  let { similarSections, groundTruthDocuments }: Props = $props();

  // Svelte 5 runes for state management
  let expandedReferences = $state<Set<number>>(new Set());
  let selectedReference = $state<number | null>(null);
  let showFullContent = $state(false);

  const dispatch = createEventDispatcher<{
    viewDocument: { documentId: string };
    highlightSection: { sectionId: string };
  }>();

  // Derived values
  const topReferences = $derived(
    similarSections
      .slice(0, 10)
      .sort((a, b) => b.similarity_score - a.similarity_score)
  );

  const averageSimilarity = $derived(() => {
    if (similarSections.length === 0) return 0;
    const total = similarSections.reduce((sum, section) => sum + section.similarity_score, 0);
    return Math.round((total / similarSections.length) * 100);
  });

  const highSimilarityCount = $derived(
    similarSections.filter(section => section.similarity_score >= 0.8).length
  );

  const mediumSimilarityCount = $derived(
    similarSections.filter(section => section.similarity_score >= 0.6 && section.similarity_score < 0.8).length
  );

  function toggleReference(index: number) {
    if (expandedReferences.has(index)) {
      expandedReferences.delete(index);
    } else {
      expandedReferences.add(index);
    }
    expandedReferences = expandedReferences; // Trigger reactivity
  }

  function selectReference(index: number) {
    selectedReference = selectedReference === index ? null : index;
  }

  function getSimilarityLevel(score: number): string {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  }

  function getSimilarityColor(score: number): string {
    if (score >= 0.8) return 'var(--color-success-600)';
    if (score >= 0.6) return 'var(--color-warning-600)';
    return 'var(--color-error-600)';
  }

  function getSimilarityIcon(score: number): string {
    if (score >= 0.8) return 'check';
    if (score >= 0.6) return 'warning';
    return 'info';
  }

  function getDocumentTitle(section: SimilarSection): string {
    return section.source_metadata?.document_title || 'Unknown Document';
  }

  function getDocumentSection(section: SimilarSection): string {
    return section.source_metadata?.section || 'Section';
  }

  function getPageNumber(section: SimilarSection): string | null {
    return section.source_metadata?.page_number?.toString() || null;
  }

  function viewDocument(section: SimilarSection) {
    if (section.source_metadata?.document_id) {
      dispatch('viewDocument', { documentId: section.source_metadata.document_id });
    }
  }

  function copyReferenceText(section: SimilarSection) {
    navigator.clipboard.writeText(section.section_text);
  }

  function highlightSection(section: SimilarSection, index: number) {
    dispatch('highlightSection', { sectionId: `section-${index}` });
  }

  function truncateText(text: string, maxLength: number = 150): string {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  }
</script>

<Card>
  <div class="ground-truth-references">
    <div class="references-header">
      <div class="header-title">
        <Icon name="book-open" size={20} color="var(--color-primary-600)" />
        <h3>Ground Truth References</h3>
      </div>
      
      <div class="header-stats">
        <div class="stat-summary">
          <span class="stat-count">{similarSections.length}</span>
          <span class="stat-label">references</span>
        </div>
        <div class="stat-summary">
          <span class="stat-count">{averageSimilarity}%</span>
          <span class="stat-label">avg match</span>
        </div>
      </div>
    </div>

    <!-- Similarity Distribution -->
    <div class="similarity-distribution">
      <div class="distribution-item">
        <Icon name="check" size={14} color="var(--color-success-600)" />
        <span class="count">{highSimilarityCount}</span>
        <span class="label">High (≥80%)</span>
      </div>
      <div class="distribution-item">
        <Icon name="warning" size={14} color="var(--color-warning-600)" />
        <span class="count">{mediumSimilarityCount}</span>
        <span class="label">Medium (60-79%)</span>
      </div>
      <div class="distribution-item">
        <Icon name="info" size={14} color="var(--color-error-600)" />
        <span class="count">{similarSections.length - highSimilarityCount - mediumSimilarityCount}</span>
        <span class="label">Low (&lt;60%)</span>
      </div>
    </div>

    <!-- References List -->
    <div class="references-list">
      {#if topReferences.length > 0}
        {#each topReferences as section, index}
          <div 
            class="reference-item"
            class:expanded={expandedReferences.has(index)}
            class:selected={selectedReference === index}
          >
            <div class="reference-header" onclick={() => selectReference(index)}>
              <div class="reference-number">{index + 1}</div>
              
              <div class="reference-info">
                <div class="reference-title">
                  <span class="section-name">{getDocumentSection(section)}</span>
                  {#if getPageNumber(section)}
                    <span class="page-number">p.{getPageNumber(section)}</span>
                  {/if}
                </div>
                <div class="document-title">{getDocumentTitle(section)}</div>
              </div>
              
              <div class="similarity-badge" style="background-color: {getSimilarityColor(section.similarity_score)}20; color: {getSimilarityColor(section.similarity_score)}">
                <Icon name={getSimilarityIcon(section.similarity_score)} size={12} />
                <span>{Math.round(section.similarity_score * 100)}%</span>
              </div>
            </div>

            <div class="reference-content">
              <div class="section-text">
                {#if showFullContent || expandedReferences.has(index)}
                  {section.section_text}
                {:else}
                  {truncateText(section.section_text)}
                {/if}
              </div>
              
              <div class="reference-actions">
                <Button 
                  variant="secondary" 
                  size="xs" 
                  onclick={() => toggleReference(index)}
                >
                  <Icon name={expandedReferences.has(index) ? 'chevron-up' : 'chevron-down'} size={12} />
                  {expandedReferences.has(index) ? 'Show Less' : 'Show More'}
                </Button>
                
                <Button 
                  variant="secondary" 
                  size="xs" 
                  onclick={() => copyReferenceText(section)}
                >
                  <Icon name="copy" size={12} />
                  Copy
                </Button>
                
                {#if section.source_metadata?.document_id}
                  <Button 
                    variant="secondary" 
                    size="xs" 
                    onclick={() => viewDocument(section)}
                  >
                    <Icon name="external-link" size={12} />
                    View
                  </Button>
                {/if}
              </div>
            </div>
          </div>
        {/each}
      {:else}
        <div class="no-references">
          <Icon name="search" size={32} color="var(--color-gray-400)" />
          <h4>No References Found</h4>
          <p>No similar sections were found in your ground truth library.</p>
        </div>
      {/if}
    </div>

    <!-- Footer Actions -->
    {#if topReferences.length > 0}
      <div class="references-footer">
        <div class="footer-info">
          <span class="info-text">
            Showing top {Math.min(10, similarSections.length)} of {similarSections.length} references
          </span>
        </div>
        
        <div class="footer-actions">
          <Button 
            variant="secondary" 
            size="sm" 
            onclick={() => showFullContent = !showFullContent}
          >
            <Icon name="eye" size={14} />
            {showFullContent ? 'Collapse All' : 'Expand All'}
          </Button>
        </div>
      </div>
    {/if}
  </div>
</Card>

<style>
  .ground-truth-references {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    max-height: 80vh;
    overflow: hidden;
  }

  .references-header {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    padding: var(--space-4) var(--space-4) 0 var(--space-4);
    border-bottom: 1px solid var(--color-border);
    padding-bottom: var(--space-3);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .header-title h3 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .header-stats {
    display: flex;
    gap: var(--space-4);
  }

  .stat-summary {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-1);
  }

  .stat-count {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-600);
  }

  .stat-label {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .similarity-distribution {
    display: flex;
    justify-content: space-between;
    padding: var(--space-3) var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
    margin: 0 var(--space-4);
  }

  .distribution-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-xs);
  }

  .distribution-item .count {
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
  }

  .distribution-item .label {
    color: var(--color-text-muted);
  }

  .references-list {
    flex: 1;
    overflow-y: auto;
    padding: 0 var(--space-4);
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .reference-item {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    overflow: hidden;
    transition: all var(--transition-fast);
    background: white;
  }

  .reference-item:hover {
    border-color: var(--color-primary-300);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  }

  .reference-item.selected {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 2px var(--color-primary-100);
  }

  .reference-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    cursor: pointer;
    background: var(--color-gray-25);
  }

  .reference-item.expanded .reference-header {
    background: var(--color-primary-50);
  }

  .reference-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
    border-radius: 50%;
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-bold);
    flex-shrink: 0;
  }

  .reference-info {
    flex: 1;
    min-width: 0;
  }

  .reference-title {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-1);
  }

  .section-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .page-number {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    background: var(--color-gray-100);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
  }

  .document-title {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    truncate: true;
  }

  .similarity-badge {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    flex-shrink: 0;
  }

  .reference-content {
    padding: var(--space-3);
    border-top: 1px solid var(--color-border);
    background: white;
    display: none;
  }

  .reference-item.expanded .reference-content,
  .reference-item.selected .reference-content {
    display: block;
  }

  .section-text {
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
    color: var(--color-text-secondary);
    margin-bottom: var(--space-3);
    word-wrap: break-word;
  }

  .reference-actions {
    display: flex;
    gap: var(--space-2);
    flex-wrap: wrap;
  }

  .references-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-3) var(--space-4);
    border-top: 1px solid var(--color-border);
    background: var(--color-gray-25);
  }

  .info-text {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  .footer-actions {
    display: flex;
    gap: var(--space-2);
  }

  .no-references {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-8);
    text-align: center;
  }

  .no-references h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .no-references p {
    color: var(--color-text-secondary);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  /* Scrollbar styling for references list */
  .references-list::-webkit-scrollbar {
    width: 6px;
  }

  .references-list::-webkit-scrollbar-track {
    background: var(--color-gray-100);
    border-radius: var(--radius-full);
  }

  .references-list::-webkit-scrollbar-thumb {
    background: var(--color-gray-300);
    border-radius: var(--radius-full);
  }

  .references-list::-webkit-scrollbar-thumb:hover {
    background: var(--color-gray-400);
  }

  @media (max-width: 1200px) {
    .ground-truth-references {
      max-height: 60vh;
    }

    .similarity-distribution {
      flex-direction: column;
      gap: var(--space-2);
    }

    .distribution-item {
      justify-content: space-between;
    }
  }

  @media (max-width: 768px) {
    .ground-truth-references {
      max-height: 50vh;
    }

    .references-header {
      padding: var(--space-3);
    }

    .references-list {
      padding: 0 var(--space-3);
    }

    .reference-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .reference-title {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-1);
    }

    .reference-actions {
      justify-content: stretch;
    }

    .reference-actions > * {
      flex: 1;
    }

    .references-footer {
      flex-direction: column;
      gap: var(--space-2);
      align-items: stretch;
    }
  }
</style>