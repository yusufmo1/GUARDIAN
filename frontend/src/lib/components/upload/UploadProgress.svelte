<script lang="ts">
  import type { UploadProgress as UploadProgressType } from '$lib/types';
  import Icon from '$lib/components/common/Icon.svelte';
  import { ANALYSIS_STAGES } from '$lib/constants';

  interface Props {
    progress: UploadProgressType;
  }

  let { progress }: Props = $props();

  const currentStage = $derived(ANALYSIS_STAGES.find(stage => stage.key === progress.stage));
  const stageIndex = $derived(ANALYSIS_STAGES.findIndex(stage => stage.key === progress.stage));
  const progressPercent = $derived(Math.min(Math.max(progress.progress, 0), 100));
  
  function getStageStatus(index: number): 'completed' | 'current' | 'pending' {
    if (index < stageIndex) return 'completed';
    if (index === stageIndex) return 'current';
    return 'pending';
  }
</script>

<div class="upload-progress">
  <div class="progress-header">
    <div class="progress-info">
      <h4 class="progress-title">Processing Document</h4>
      <p class="progress-stage">
        {currentStage?.label || 'Processing...'}
        {#if progress.message}
          - {progress.message}
        {/if}
      </p>
    </div>
    <div class="progress-percent">
      {progressPercent}%
    </div>
  </div>

  <div class="progress-bar">
    <div 
      class="progress-fill" 
      style="width: {progressPercent}%"
      class:error={progress.stage === 'error'}
    ></div>
  </div>

  <div class="stage-indicators">
    {#each ANALYSIS_STAGES as stage, index}
      {@const status = getStageStatus(index)}
      <div class="stage-indicator" class:completed={status === 'completed'} class:current={status === 'current'}>
        <div class="stage-icon">
          {#if status === 'completed'}
            <Icon name="check" size={16} />
          {:else if status === 'current'}
            <div class="spinner"></div>
          {:else}
            <div class="stage-dot"></div>
          {/if}
        </div>
        <span class="stage-label">{stage.label}</span>
      </div>
    {/each}
  </div>
</div>

<style>
  .upload-progress {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-6);
    margin-bottom: var(--space-4);
  }

  .progress-header {
    display: flex;
    justify-content: between;
    align-items: flex-start;
    margin-bottom: var(--space-4);
  }

  .progress-info {
    flex: 1;
  }

  .progress-title {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0 0 var(--space-2) 0;
  }

  .progress-stage {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0;
  }

  .progress-percent {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-primary-600);
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background: var(--color-gray-200);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin-bottom: var(--space-6);
  }

  .progress-fill {
    height: 100%;
    background: var(--color-primary-500);
    border-radius: var(--radius-full);
    transition: width var(--transition-normal);
    position: relative;
  }

  .progress-fill.error {
    background: var(--color-error-500);
  }

  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    right: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.2),
      transparent
    );
    animation: shimmer 2s infinite;
  }

  .stage-indicators {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .stage-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
  }

  .stage-indicator.current {
    background: var(--color-primary-50);
    color: var(--color-primary-700);
  }

  .stage-indicator.completed {
    color: var(--color-success-700);
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

  .stage-indicator.completed .stage-icon {
    background: var(--color-success-100);
    color: var(--color-success-600);
  }

  .stage-indicator.current .stage-icon {
    background: var(--color-primary-100);
    color: var(--color-primary-600);
  }

  .stage-dot {
    width: 8px;
    height: 8px;
    background: var(--color-gray-300);
    border-radius: var(--radius-full);
  }

  .stage-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid var(--color-primary-200);
    border-top: 2px solid var(--color-primary-600);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes shimmer {
    0% {
      transform: translateX(-100%);
    }
    100% {
      transform: translateX(100%);
    }
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 640px) {
    .progress-header {
      flex-direction: column;
      gap: var(--space-2);
    }

    .stage-indicators {
      gap: var(--space-2);
    }

    .stage-indicator {
      padding: var(--space-1);
    }
  }
</style>