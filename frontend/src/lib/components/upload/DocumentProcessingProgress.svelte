<script lang="ts">
  import Icon from '$lib/components/common/Icon.svelte';

  interface Props {
    files?: File[];
    currentStage?: number;
    isProcessing?: boolean;
    onCancel?: () => void;
  }

  let { files = [], currentStage = 0, isProcessing = false, onCancel }: Props = $props();

  // Processing stages based on ANALYSIS_STAGES from constants
  const processingStages = [
    { key: 'uploading', label: 'Uploading document', progress: 10 },
    { key: 'extracting', label: 'Extracting text', progress: 25 },
    { key: 'processing', label: 'Processing content', progress: 45 },
    { key: 'embedding', label: 'Generating embeddings', progress: 70 },
    { key: 'indexing', label: 'Building search index', progress: 90 },
    { key: 'completed', label: 'Analysis complete', progress: 100 }
  ];

  // Derived values
  const currentStageData = $derived(processingStages[currentStage] || processingStages[0]);
  const progressPercentage = $derived(currentStageData.progress);
  const completedStages = $derived(currentStage);
</script>

<div class="processing-progress">
  <div class="progress-header">
    <h3>Processing Documents</h3>
    {#if files.length > 0}
      <p>Processing {files.length} document{files.length === 1 ? '' : 's'}...</p>
    {/if}
  </div>

  <!-- Current Stage Display -->
  <div class="current-stage">
    <div class="stage-info">
      <h4>Processing Document</h4>
      <div class="stage-details">
        <span class="stage-label">{currentStageData.label}</span>
        <span class="stage-progress">{progressPercentage}%</span>
      </div>
    </div>
    
    <!-- Progress Bar -->
    <div class="progress-bar">
      <div 
        class="progress-fill" 
        style="width: {progressPercentage}%"
      ></div>
    </div>
  </div>

  <!-- Stage List -->
  <div class="stages-list">
    {#each processingStages as stage, index}
      <div 
        class="stage-item"
        class:active={index === currentStage}
        class:completed={index < currentStage}
        class:pending={index > currentStage}
      >
        <div class="stage-icon">
          {#if index < currentStage}
            <Icon name="check" size={16} />
          {:else if index === currentStage && isProcessing}
            <Icon name="loading" size={16} class="animate-spin" />
          {:else}
            <span class="stage-number">{index + 1}</span>
          {/if}
        </div>
        <span class="stage-text">{stage.label}</span>
      </div>
    {/each}
  </div>

  <!-- Files being processed -->
  {#if files.length > 0}
    <div class="files-being-processed">
      <h5>Documents</h5>
      <div class="files-list">
        {#each files as file}
          <div class="file-item">
            <Icon name="file-text" size={16} />
            <span class="file-name">{file.name}</span>
            <div class="file-status">
              {#if currentStage < processingStages.length - 1}
                <Icon name="loading" size={14} class="animate-spin" />
              {:else}
                <Icon name="check" size={14} />
              {/if}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Cancel Button -->
  {#if onCancel && isProcessing}
    <div class="progress-actions">
      <button class="cancel-button" onclick={onCancel}>
        <Icon name="x" size={16} />
        Cancel Processing
      </button>
    </div>
  {/if}
</div>

<style>
  .processing-progress {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    padding: var(--space-6);
    background: white;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .progress-header {
    text-align: center;
  }

  .progress-header h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .progress-header p {
    color: var(--color-text-secondary);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  .current-stage {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .stage-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .stage-info h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    margin: 0;
    color: var(--color-text);
  }

  .stage-details {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .stage-label {
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
  }

  .stage-progress {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-600);
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--color-gray-200);
    border-radius: var(--radius-full);
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary-500), var(--color-primary-600));
    border-radius: var(--radius-full);
    transition: width 0.5s ease-in-out;
  }

  .stages-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .stage-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
  }

  .stage-item.completed {
    background: var(--color-success-50);
    border: 1px solid var(--color-success-200);
  }

  .stage-item.active {
    background: var(--color-primary-50);
    border: 1px solid var(--color-primary-200);
  }

  .stage-item.pending {
    background: var(--color-gray-50);
    border: 1px solid var(--color-gray-200);
    opacity: 0.7;
  }

  .stage-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: var(--radius-full);
    flex-shrink: 0;
  }

  .stage-item.completed .stage-icon {
    background: var(--color-success-500);
    color: white;
  }

  .stage-item.active .stage-icon {
    background: var(--color-primary-500);
    color: white;
  }

  .stage-item.pending .stage-icon {
    background: var(--color-gray-300);
    color: var(--color-gray-600);
  }

  .stage-number {
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-bold);
  }

  .stage-text {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
  }

  .stage-item.completed .stage-text {
    color: var(--color-success-700);
  }

  .stage-item.active .stage-text {
    color: var(--color-primary-700);
  }

  .stage-item.pending .stage-text {
    color: var(--color-gray-600);
  }

  .files-being-processed {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .files-being-processed h5 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .files-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-gray-200);
  }

  .file-name {
    flex: 1;
    font-size: var(--font-size-sm);
    color: var(--color-text);
    word-break: break-word;
  }

  .file-status {
    color: var(--color-primary-600);
  }

  .progress-actions {
    display: flex;
    justify-content: center;
    gap: var(--space-3);
  }

  .cancel-button {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    background: var(--color-gray-100);
    border: 1px solid var(--color-gray-300);
    border-radius: var(--radius-md);
    color: var(--color-text);
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .cancel-button:hover {
    background: var(--color-gray-200);
    border-color: var(--color-gray-400);
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
    .processing-progress {
      padding: var(--space-4);
    }

    .stage-details {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-1);
    }

    .stages-list {
      gap: var(--space-2);
    }

    .stage-item {
      padding: var(--space-2);
    }
  }
</style>