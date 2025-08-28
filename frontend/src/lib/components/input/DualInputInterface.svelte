<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import TextProtocolInput from './TextProtocolInput.svelte';
  import ProtocolUpload from '../upload/ProtocolUpload.svelte';

  interface Props {
    disabled?: boolean;
    analysisInProgress?: boolean;
    hasGroundTruth?: boolean;
  }

  let { disabled = false, analysisInProgress = false, hasGroundTruth = true }: Props = $props();

  // Svelte 5 runes for state management
  let activeTab = $state<'text' | 'upload'>('text');
  let textContent = $state('');
  let selectedFiles = $state<File[]>([]);
  let analysisOptions = $state({
    includeCompliance: true,
    includeTerminology: true,
    includeMissingElements: true
  });

  const dispatch = createEventDispatcher<{
    textAnalysis: { text: string, options: any };
    fileAnalysis: { files: File[], options: any };
    error: { message: string };
  }>();

  // Derived values
  const canAnalyzeText = $derived(
    textContent.trim().length > 10 && !disabled && !analysisInProgress
  );
  const canAnalyzeFiles = $derived(
    selectedFiles.length > 0 && !disabled && !analysisInProgress
  );
  const hasValidInput = $derived(
    activeTab === 'text' ? canAnalyzeText : canAnalyzeFiles
  );

  function switchTab(tab: 'text' | 'upload') {
    if (disabled || analysisInProgress) return;
    activeTab = tab;
  }

  function handleTextInput(event: CustomEvent<{ text: string }>) {
    textContent = event.detail.text;
  }

  function handleTextAnalysis(event: CustomEvent<{ text: string, options: any }>) {
    if (!canAnalyzeText) {
      dispatch('error', { message: 'Please enter at least 10 characters of protocol text' });
      return;
    }
    
    if (!hasGroundTruth) {
      dispatch('error', { message: 'No ground truth documents available. Please upload ground truth documents first.' });
      return;
    }

    dispatch('textAnalysis', {
      text: event.detail.text,
      options: { ...analysisOptions, ...event.detail.options }
    });
  }

  function handleFileUpload(event: CustomEvent<{ files: File[] }>) {
    selectedFiles = event.detail.files;
  }

  function handleFileAnalysis(event: CustomEvent<{ files: File[], options: any }>) {
    if (!canAnalyzeFiles) {
      dispatch('error', { message: 'Please select at least one protocol file' });
      return;
    }
    
    if (!hasGroundTruth) {
      dispatch('error', { message: 'No ground truth documents available. Please upload ground truth documents first.' });
      return;
    }

    dispatch('fileAnalysis', {
      files: event.detail.files,
      options: { ...analysisOptions, ...event.detail.options }
    });
  }

  function handleError(event: CustomEvent<{ message: string }>) {
    dispatch('error', event.detail);
  }

  function clearInput() {
    if (activeTab === 'text') {
      textContent = '';
    } else {
      selectedFiles = [];
    }
  }

  function analyzeInput() {
    if (activeTab === 'text' && canAnalyzeText) {
      handleTextAnalysis(new CustomEvent('textAnalysis', {
        detail: { text: textContent, options: analysisOptions }
      }));
    } else if (activeTab === 'upload' && canAnalyzeFiles) {
      handleFileAnalysis(new CustomEvent('fileAnalysis', {
        detail: { files: selectedFiles, options: analysisOptions }
      }));
    }
  }
</script>

<div class="dual-input-interface">
  <div class="interface-header">
    <h3>
      <Icon name="analysis" size={20} />
      Protocol Analysis Input
    </h3>
    <p>Choose your preferred input method and configure analysis options</p>
  </div>

  <!-- Tab Navigation -->
  <div class="tab-navigation">
    <button
      class="tab-button"
      class:active={activeTab === 'text'}
      class:disabled={disabled}
      onclick={() => switchTab('text')}
    >
      <Icon name="edit" size={16} />
      <span class="tab-label">Paste Text</span>
      <span class="tab-description">Direct text input</span>
    </button>
    
    <button
      class="tab-button"
      class:active={activeTab === 'upload'}
      class:disabled={disabled}
      onclick={() => switchTab('upload')}
    >
      <Icon name="upload" size={16} />
      <span class="tab-label">Upload File</span>
      <span class="tab-description">PDF, DOCX, TXT</span>
    </button>
  </div>

  <!-- Analysis Options -->
  <div class="analysis-options">
    <h4>Analysis Options</h4>
    <div class="options-grid">
      <label class="option-item">
        <input 
          type="checkbox" 
          bind:checked={analysisOptions.includeCompliance}
          {disabled}
        />
        <Icon name="shield" size={16} />
        <div class="option-content">
          <span class="option-label">Compliance Check</span>
          <span class="option-description">Compare against regulatory standards</span>
        </div>
      </label>
      
      <label class="option-item">
        <input 
          type="checkbox" 
          bind:checked={analysisOptions.includeTerminology}
          {disabled}
        />
        <Icon name="book-open" size={16} />
        <div class="option-content">
          <span class="option-label">Terminology Review</span>
          <span class="option-description">Validate pharmaceutical terminology</span>
        </div>
      </label>
      
      <label class="option-item">
        <input 
          type="checkbox" 
          bind:checked={analysisOptions.includeMissingElements}
          {disabled}
        />
        <Icon name="search" size={16} />
        <div class="option-content">
          <span class="option-label">Missing Elements</span>
          <span class="option-description">Identify gaps and omissions</span>
        </div>
      </label>
    </div>
  </div>

  <!-- Tab Content -->
  <div class="tab-content">
    {#if activeTab === 'text'}
      <div class="text-input-panel" class:disabled={disabled}>
        <TextProtocolInput
          {disabled}
          {analysisInProgress}
          {hasGroundTruth}
          on:input={handleTextInput}
          on:analyze={handleTextAnalysis}
          on:error={handleError}
        />
      </div>
    {:else}
      <div class="upload-panel" class:disabled={disabled}>
        <ProtocolUpload
          {disabled}
          {analysisInProgress}
          {hasGroundTruth}
          on:upload={handleFileUpload}
          on:analyze={handleFileAnalysis}
          on:error={handleError}
        />
      </div>
    {/if}
  </div>

  <!-- Action Bar -->
  <div class="action-bar">
    <div class="action-info">
      {#if !hasGroundTruth}
        <div class="ground-truth-warning">
          <Icon name="warning" size={16} color="var(--color-warning-600)" />
          <span>Upload ground truth documents first for comprehensive analysis</span>
        </div>
      {:else}
        <div class="analysis-ready">
          <Icon name="check" size={16} color="var(--color-success-600)" />
          <span>Ready to analyze against ground truth library</span>
        </div>
      {/if}
    </div>

    <div class="action-buttons">
      {#if hasValidInput}
        <Button
          variant="secondary"
          size="sm"
          onclick={clearInput}
          {disabled}
        >
          <Icon name="x" size={16} />
          Clear
        </Button>
      {/if}
      
      <Button
        variant="primary"
        loading={analysisInProgress}
        disabled={!hasValidInput || disabled}
        onclick={analyzeInput}
      >
        <Icon name="activity" size={16} />
        {analysisInProgress ? 'Analyzing...' : 'Analyze Protocol'}
      </Button>
    </div>
  </div>

  <!-- Progress Indicator -->
  {#if analysisInProgress}
    <div class="progress-indicator">
      <div class="progress-bar">
        <div class="progress-fill"></div>
      </div>
      <div class="progress-text">
        <Icon name="loading" size={16} class="animate-spin" />
        <span>Analyzing protocol against ground truth library...</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .dual-input-interface {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .interface-header {
    text-align: center;
    margin-bottom: var(--space-4);
  }

  .interface-header h3 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .interface-header p {
    color: var(--color-text-secondary);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  .tab-navigation {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-2);
    background: var(--color-gray-100);
    padding: var(--space-2);
    border-radius: var(--radius-lg);
  }

  .tab-button {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-4);
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-align: center;
  }

  .tab-button:hover:not(.disabled) {
    background: var(--color-gray-50);
  }

  .tab-button.active {
    background: white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    color: var(--color-primary-600);
  }

  .tab-button.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .tab-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: inherit;
  }

  .tab-description {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  .tab-button.active .tab-description {
    color: var(--color-primary-500);
  }

  .analysis-options {
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .analysis-options h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    margin: 0 0 var(--space-4) 0;
    color: var(--color-text);
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .options-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-3);
  }

  .option-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    cursor: pointer;
    padding: var(--space-3);
    border-radius: var(--radius-md);
    transition: background-color var(--transition-fast);
  }

  .option-item:hover {
    background: white;
  }

  .option-item input[type="checkbox"] {
    margin: 0;
    flex-shrink: 0;
  }

  .option-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    flex: 1;
  }

  .option-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .option-description {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    line-height: var(--line-height-tight);
  }

  .tab-content {
    min-height: 400px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: white;
  }

  .text-input-panel,
  .upload-panel {
    height: 100%;
    transition: opacity var(--transition-fast);
  }

  .text-input-panel.disabled,
  .upload-panel.disabled {
    opacity: 0.7;
    pointer-events: none;
  }

  .action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    flex-wrap: wrap;
    gap: var(--space-3);
  }

  .action-info {
    flex: 1;
    min-width: 200px;
  }

  .ground-truth-warning,
  .analysis-ready {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
  }

  .ground-truth-warning {
    color: var(--color-warning-700);
    background: var(--color-warning-50);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-warning-200);
  }

  .analysis-ready {
    color: var(--color-success-700);
  }

  .action-buttons {
    display: flex;
    gap: var(--space-3);
    align-items: center;
  }

  .progress-indicator {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-primary-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-primary-200);
  }

  .progress-bar {
    width: 100%;
    height: 4px;
    background: var(--color-primary-200);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    border-radius: var(--radius-full);
    animation: progress-pulse 1.5s ease-in-out infinite;
  }

  .progress-text {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    color: var(--color-primary-700);
    justify-content: center;
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

  @keyframes progress-pulse {
    0% {
      transform: translateX(-100%);
    }
    50% {
      transform: translateX(0%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  @media (max-width: 768px) {
    .dual-input-interface {
      padding: var(--space-4);
    }

    .tab-navigation {
      grid-template-columns: 1fr;
    }

    .options-grid {
      grid-template-columns: 1fr;
    }

    .action-bar {
      flex-direction: column;
      align-items: stretch;
    }

    .action-buttons {
      justify-content: stretch;
      width: 100%;
    }

    .action-buttons > * {
      flex: 1;
    }

    .tab-content {
      min-height: 300px;
    }
  }
</style>