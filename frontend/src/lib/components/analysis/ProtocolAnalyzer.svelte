<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { session as sessionApi, GuardianApiError } from '$lib/services/api';
  import { toastStore, authState } from '$lib/stores';
  import type { ProtocolAnalysisRequest, ProtocolAnalysisResult } from '$lib/services/api';

  interface Props {
    documentId?: string;
  }
  
  let { documentId }: Props = $props();

  // Convert local state to Svelte 5 runes
  let protocolText = $state('');
  let analyzing = $state(false);
  let analysisResult = $state<ProtocolAnalysisResult | null>(null);
  let analysisError = $state<string | null>(null);

  // Authentication state accessed directly to avoid reactive loops

  const dispatch = createEventDispatcher<{
    analysis: { result: ProtocolAnalysisResult };
  }>();

  // Convert analysis options to Svelte 5 state
  let includeComplianceCheck = $state(true);
  let includeTerminologyReview = $state(true);
  let includeMissingElements = $state(true);

  async function analyzeProtocol() {
    if (!authState.authenticated) {
      toastStore.error('Authentication Required', 'Please sign in to analyze protocols');
      return;
    }

    if (!protocolText.trim()) {
      toastStore.error('Analysis Error', 'Please enter protocol text to analyze');
      return;
    }

    try {
      analyzing = true;
      analysisError = null;
      analysisResult = null;

      const request: ProtocolAnalysisRequest = {
        protocol_text: protocolText.trim(),
        analysis_options: {
          include_compliance_check: includeComplianceCheck,
          include_terminology_review: includeTerminologyReview,
          include_missing_elements: includeMissingElements
        }
      };

      const response = await sessionApi.analyzeProtocol(request);

      if (response.data) {
        analysisResult = response.data;
        dispatch('analysis', { result: response.data });
        toastStore.success('Analysis Complete', 'Protocol analysis completed successfully');
      }
    } catch (error) {
      if (error instanceof GuardianApiError) {
        analysisError = error.message;
        toastStore.error('Analysis Failed', error.message);
      } else {
        analysisError = 'An unexpected error occurred during analysis';
        toastStore.error('Analysis Failed', 'An unexpected error occurred');
      }
    } finally {
      analyzing = false;
    }
  }

  function clearAnalysis() {
    analysisResult = null;
    analysisError = null;
    protocolText = '';
  }

  function getComplianceScoreColor(score: number): string {
    if (score >= 0.8) return 'var(--color-success-600)';
    if (score >= 0.6) return 'var(--color-warning-600)';
    return 'var(--color-error-600)';
  }

  function getSeverityColor(severity: string): string {
    switch (severity) {
      case 'critical': return 'var(--color-error-600)';
      case 'major': return 'var(--color-error-500)';
      case 'minor': return 'var(--color-warning-600)';
      case 'info': return 'var(--color-primary-600)';
      default: return 'var(--color-gray-600)';
    }
  }

  function getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'critical': return 'error';
      case 'major': return 'warning';
      case 'minor': return 'info';
      case 'info': return 'info';
      default: return 'info';
    }
  }
</script>

<div class="protocol-analyzer">
  <Card>
    <div class="analyzer-header">
      <h2>
        <Icon name="analysis" size={24} />
        Protocol Analysis
      </h2>
      {#if authState.authenticated && authState.user}
        <p>Welcome, {authState.user.name || authState.user.email}! Analyze your pharmaceutical protocol against global regulatory standards</p>
      {:else}
        <p>Sign in to analyze your pharmaceutical protocol against global regulatory standards</p>
      {/if}
    </div>

    <!-- Input Section -->
    <div class="input-section">
      <div class="form-group">
        <label for="protocol-text">Protocol Text</label>
        <textarea
          id="protocol-text"
          bind:value={protocolText}
          placeholder={authState.authenticated ? "Enter your pharmaceutical protocol text here. For example: 'HPLC Analysis of Acetaminophen: Prepare mobile phase with acetonitrile and water (30:70 v/v). Use C18 column. Inject 20μL sample. Detection at 254nm UV.'" : "Please sign in to analyze protocols"}
          rows="8"
          disabled={!authState.authenticated || analyzing}
        ></textarea>
        <p class="form-help">
          Enter the protocol text you want to analyze for compliance with global regulatory standards.
        </p>
      </div>

      <!-- Analysis Options -->
      <div class="options-section">
        <h3>Analysis Options</h3>
        <div class="checkbox-group">
          <label class="checkbox-option">
            <input type="checkbox" bind:checked={includeComplianceCheck} disabled={!authState.authenticated || analyzing} />
            <Icon name="check" size={16} />
            Include compliance check
          </label>
          <label class="checkbox-option">
            <input type="checkbox" bind:checked={includeTerminologyReview} disabled={!authState.authenticated || analyzing} />
            <Icon name="book-open" size={16} />
            Include terminology review
          </label>
          <label class="checkbox-option">
            <input type="checkbox" bind:checked={includeMissingElements} disabled={!authState.authenticated || analyzing} />
            <Icon name="search" size={16} />
            Identify missing elements
          </label>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="actions">
        <Button
          variant="primary"
          loading={analyzing}
          disabled={!authState.authenticated || !protocolText.trim() || analyzing}
          onclick={analyzeProtocol}
        >
          <Icon name="activity" size={16} />
          {analyzing ? 'Analyzing...' : authState.authenticated ? 'Analyze Protocol' : 'Sign In Required'}
        </Button>

        {#if analysisResult || analysisError}
          <Button
            variant="secondary"
            disabled={analyzing}
            onclick={clearAnalysis}
          >
            <Icon name="refresh" size={16} />
            Clear Results
          </Button>
        {/if}
      </div>
    </div>

    <!-- Results Section -->
    {#if analysisResult}
      <div class="results-section">
        <div class="results-header">
          <h3>
            <Icon name="analysis" size={20} />
            Analysis Results
          </h3>
          <div class="analysis-meta">
            <span class="processing-time">
              <Icon name="clock" size={14} />
              {analysisResult.processing_time.toFixed(2)}s
            </span>
            <span class="timestamp">
              <Icon name="calendar" size={14} />
              {new Date(analysisResult.timestamp).toLocaleString()}
            </span>
          </div>
        </div>

        <!-- Protocol Input Summary -->
        <div class="input-summary">
          <h4>Protocol Input</h4>
          <div class="input-stats">
            <span class="stat">
              <strong>{analysisResult.protocol_input.word_count}</strong> words
            </span>
            <span class="stat">
              <strong>{analysisResult.protocol_input.character_count}</strong> characters
            </span>
          </div>
        </div>

        <!-- Compliance Analysis -->
        <div class="compliance-section">
          <div class="compliance-header">
            <h4>Compliance Analysis</h4>
            <div 
              class="compliance-score"
              style="color: {getComplianceScoreColor(analysisResult.compliance_analysis.overall_compliance_score)}"
            >
              {Math.round(analysisResult.compliance_analysis.overall_compliance_score * 100)}%
            </div>
          </div>

          {#if analysisResult.compliance_analysis.compliance_issues.length > 0}
            <div class="issues-list">
              <h5>Issues Found ({analysisResult.compliance_analysis.compliance_issues.length})</h5>
              {#each analysisResult.compliance_analysis.compliance_issues as issue}
                <div class="issue-item">
                  <div class="issue-header">
                    <Icon 
                      name={getSeverityIcon(issue.severity)} 
                      size={16} 
                      color={getSeverityColor(issue.severity)}
                    />
                    <span class="issue-type">{issue.issue_type.replace('_', ' ')}</span>
                    <span 
                      class="issue-severity"
                      style="color: {getSeverityColor(issue.severity)}"
                    >
                      {issue.severity}
                    </span>
                  </div>
                  <p class="issue-description">{issue.description}</p>
                  {#if issue.suggested_fix}
                    <div class="issue-fix">
                      <Icon name="info" size={14} />
                      <span>Suggestion: {issue.suggested_fix}</span>
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {:else}
            <div class="no-issues">
              <Icon name="check" size={24} color="var(--color-success-600)" />
              <p>No compliance issues found</p>
            </div>
          {/if}
        </div>

        <!-- Similar Sections -->
        {#if analysisResult.similar_sections.length > 0}
          <div class="similar-sections">
            <h4>
              Similar Sections Found 
              <span class="section-count">({analysisResult.similar_sections.length})</span>
            </h4>
            <div class="sections-list">
              {#each analysisResult.similar_sections as section}
                <div class="section-item">
                  <div class="section-header">
                    <span class="section-reference">{section.source_metadata.section}</span>
                    <span class="similarity-score">
                      {Math.round(section.similarity_score * 100)}% match
                    </span>
                  </div>
                  <p class="section-text">{section.section_text}</p>
                </div>
              {/each}
            </div>
          </div>
        {/if}

        <!-- Search Metadata -->
        <div class="search-metadata">
          <h4>Search Statistics</h4>
          <div class="metadata-grid">
            <div class="metadata-item">
              <span class="metadata-label">Sections Found</span>
              <span class="metadata-value">{analysisResult.search_metadata.total_sections_found}</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">Avg Similarity</span>
              <span class="metadata-value">{Math.round(analysisResult.search_metadata.avg_similarity_score * 100)}%</span>
            </div>
            <div class="metadata-item">
              <span class="metadata-label">Search Time</span>
              <span class="metadata-value">{analysisResult.search_metadata.processing_time_ms}ms</span>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Error Section -->
    {#if analysisError}
      <div class="error-section">
        <div class="error-message">
          <Icon name="error" size={20} color="var(--color-error-600)" />
          <div>
            <h4>Analysis Failed</h4>
            <p>{analysisError}</p>
          </div>
        </div>
      </div>
    {/if}
  </Card>
</div>

<style>
  .protocol-analyzer {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .analyzer-header {
    text-align: center;
    margin-bottom: var(--space-6);
  }

  .analyzer-header h2 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-3);
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-3);
    color: var(--color-text);
  }

  .analyzer-header p {
    color: var(--color-text-secondary);
    font-size: var(--font-size-base);
  }

  .input-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .form-group label {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .form-group textarea {
    padding: var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    font-family: inherit;
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
    resize: vertical;
    min-height: 200px;
  }

  .form-group textarea:focus {
    outline: none;
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-primary-100);
  }

  .form-group textarea:disabled {
    background: var(--color-gray-50);
    opacity: 0.7;
  }

  .form-help {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin: 0;
  }

  .options-section h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-4);
    color: var(--color-text);
  }

  .checkbox-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .checkbox-option {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    cursor: pointer;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    transition: background-color var(--transition-fast);
  }

  .checkbox-option:hover {
    background: var(--color-gray-50);
  }

  .actions {
    display: flex;
    gap: var(--space-3);
    align-items: center;
    padding-top: var(--space-4);
    border-top: 1px solid var(--color-border);
  }

  .results-section {
    margin-top: var(--space-6);
    padding-top: var(--space-6);
    border-top: 1px solid var(--color-border);
  }

  .results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-6);
  }

  .results-header h3 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .analysis-meta {
    display: flex;
    gap: var(--space-4);
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
  }

  .analysis-meta span {
    display: flex;
    align-items: center;
    gap: var(--space-1);
  }

  .input-summary {
    margin-bottom: var(--space-6);
  }

  .input-summary h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-3);
    color: var(--color-text);
  }

  .input-stats {
    display: flex;
    gap: var(--space-4);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .compliance-section {
    margin-bottom: var(--space-6);
  }

  .compliance-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
  }

  .compliance-header h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    margin: 0;
    color: var(--color-text);
  }

  .compliance-score {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
  }

  .issues-list h5 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-3);
    color: var(--color-text);
  }

  .issue-item {
    padding: var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-3);
  }

  .issue-header {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-2);
  }

  .issue-type {
    font-weight: var(--font-weight-medium);
    text-transform: capitalize;
    flex: 1;
  }

  .issue-severity {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    text-transform: uppercase;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    background: var(--color-gray-100);
  }

  .issue-description {
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-2) 0;
    line-height: var(--line-height-relaxed);
  }

  .issue-fix {
    display: flex;
    align-items: flex-start;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    background: var(--color-primary-50);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    color: var(--color-primary-700);
  }

  .no-issues {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-6);
    text-align: center;
  }

  .no-issues p {
    margin: 0;
    color: var(--color-text-secondary);
  }

  .similar-sections {
    margin-bottom: var(--space-6);
  }

  .similar-sections h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-4);
    color: var(--color-text);
  }

  .section-count {
    color: var(--color-text-muted);
    font-weight: var(--font-weight-normal);
  }

  .section-item {
    padding: var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-3);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-2);
  }

  .section-reference {
    font-weight: var(--font-weight-medium);
    color: var(--color-primary-600);
  }

  .similarity-score {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    background: var(--color-gray-100);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
  }

  .section-text {
    margin: 0;
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    font-size: var(--font-size-sm);
  }

  .search-metadata h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    margin-bottom: var(--space-4);
    color: var(--color-text);
  }

  .metadata-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: var(--space-4);
  }

  .metadata-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .metadata-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
  }

  .metadata-value {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .error-section {
    margin-top: var(--space-6);
    padding-top: var(--space-6);
    border-top: 1px solid var(--color-border);
  }

  .error-message {
    display: flex;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-error-50);
    border: 1px solid var(--color-error-200);
    border-radius: var(--radius-lg);
  }

  .error-message h4 {
    margin: 0 0 var(--space-1) 0;
    color: var(--color-error-700);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
  }

  .error-message p {
    margin: 0;
    color: var(--color-error-600);
    font-size: var(--font-size-sm);
  }

  @media (max-width: 768px) {
    .results-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-3);
    }

    .compliance-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .section-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-1);
    }

    .actions {
      flex-direction: column;
      align-items: stretch;
    }

    .metadata-grid {
      grid-template-columns: 1fr;
    }
  }
</style>