<script lang="ts">
  import { onMount } from 'svelte';
  import Icon from './Icon.svelte';
  import Button from './Button.svelte';
  import { toastStore } from '$lib/stores';
  import { GuardianApiError } from '$lib/services/api';

  interface Props {
    error?: Error | null;
    title?: string;
    showDetails?: boolean;
    retryable?: boolean;
    onRetry?: (() => void) | undefined;
  }

  let { 
    error = null,
    title = 'Something went wrong',
    showDetails = false,
    retryable = false,
    onRetry = undefined
  }: Props = $props();

  let expanded = $state(false);

  function handleRetry() {
    if (onRetry) {
      error = null;
      onRetry();
    }
  }

  function copyError() {
    if (error) {
      const errorText = `${error.name}: ${error.message}\n\nStack:\n${error.stack}`;
      navigator.clipboard.writeText(errorText).then(() => {
        toastStore.success('Copied', 'Error details copied to clipboard');
      }).catch(() => {
        toastStore.error('Copy Failed', 'Could not copy to clipboard');
      });
    }
  }

  function getErrorDetails(error: Error) {
    if (error instanceof GuardianApiError) {
      return {
        type: 'API Error',
        status: error.status,
        code: error.code,
        errors: error.errors
      };
    }
    
    return {
      type: error.name || 'Error',
      message: error.message,
      stack: error.stack
    };
  }

  const errorDetails = $derived(error ? getErrorDetails(error) : null);
</script>

{#if error}
  <div class="error-boundary">
    <div class="error-content">
      <div class="error-icon">
        <Icon name="error" size={48} color="var(--color-error-500)" />
      </div>

      <div class="error-text">
        <h3 class="error-title">{title}</h3>
        <p class="error-message">
          {error.message || 'An unexpected error occurred. Please try again or contact support if the problem persists.'}
        </p>

        {#if errorDetails && (errorDetails.status || errorDetails.code)}
          <div class="error-meta">
            {#if errorDetails.status}
              <span class="error-status">Status: {errorDetails.status}</span>
            {/if}
            {#if errorDetails.code}
              <span class="error-code">Code: {errorDetails.code}</span>
            {/if}
          </div>
        {/if}

        {#if errorDetails?.errors && errorDetails.errors.length > 0}
          <div class="error-details">
            <h4>Details:</h4>
            <ul>
              {#each errorDetails.errors as apiError}
                <li>
                  <strong>{apiError.error_type}:</strong> 
                  {apiError.details?.message || 'Unknown error'}
                  {#if apiError.field}
                    <span class="error-field">(Field: {apiError.field})</span>
                  {/if}
                </li>
              {/each}
            </ul>
          </div>
        {/if}
      </div>

      <div class="error-actions">
        {#if retryable && onRetry}
          <Button variant="primary" onclick={handleRetry}>
            <Icon name="refresh" size={16} />
            Try Again
          </Button>
        {/if}

        {#if showDetails}
          <Button 
            variant="secondary" 
            size="sm"
            onclick={() => expanded = !expanded}
          >
            <Icon name={expanded ? 'chevron-up' : 'chevron-down'} size={16} />
            {expanded ? 'Hide' : 'Show'} Details
          </Button>

          <Button 
            variant="secondary" 
            size="sm"
            onclick={copyError}
          >
            <Icon name="copy" size={16} />
            Copy Error
          </Button>
        {/if}
      </div>

      {#if expanded && showDetails}
        <div class="error-stack">
          <h4>Technical Details:</h4>
          <pre class="error-pre">{JSON.stringify({
            name: error.name,
            message: error.message,
            ...(error instanceof GuardianApiError ? {
              status: error.status,
              code: error.code,
              errors: error.errors
            } : {}),
            stack: error.stack
          }, null, 2)}</pre>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .error-boundary {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
    padding: var(--space-8);
  }

  .error-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-6);
    max-width: 600px;
    width: 100%;
    text-align: center;
    padding: var(--space-8);
    background: var(--color-surface);
    border: 1px solid var(--color-error-200);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);
  }

  .error-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 80px;
    height: 80px;
    background: var(--color-error-50);
    border-radius: var(--radius-full);
  }

  .error-text {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    width: 100%;
  }

  .error-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-error-700);
    margin: 0;
  }

  .error-message {
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  .error-meta {
    display: flex;
    justify-content: center;
    gap: var(--space-4);
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin-top: var(--space-2);
  }

  .error-status,
  .error-code {
    padding: var(--space-1) var(--space-2);
    background: var(--color-gray-100);
    border-radius: var(--radius-sm);
    font-family: var(--font-family-mono);
  }

  .error-details {
    text-align: left;
    padding: var(--space-4);
    background: var(--color-error-50);
    border: 1px solid var(--color-error-200);
    border-radius: var(--radius-lg);
    margin-top: var(--space-3);
  }

  .error-details h4 {
    margin: 0 0 var(--space-2) 0;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-error-700);
  }

  .error-details ul {
    margin: 0;
    padding-left: var(--space-4);
    color: var(--color-error-600);
    font-size: var(--font-size-sm);
  }

  .error-details li {
    margin-bottom: var(--space-1);
  }

  .error-field {
    font-style: italic;
    color: var(--color-error-500);
  }

  .error-actions {
    display: flex;
    gap: var(--space-3);
    align-items: center;
    flex-wrap: wrap;
    justify-content: center;
  }

  .error-stack {
    width: 100%;
    text-align: left;
    padding: var(--space-4);
    background: var(--color-gray-50);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    margin-top: var(--space-3);
  }

  .error-stack h4 {
    margin: 0 0 var(--space-3) 0;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
  }

  .error-pre {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    background: var(--color-surface);
    padding: var(--space-3);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border);
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
    max-height: 300px;
    overflow-y: auto;
  }

  @media (max-width: 640px) {
    .error-boundary {
      padding: var(--space-4);
      min-height: 300px;
    }

    .error-content {
      padding: var(--space-6);
    }

    .error-title {
      font-size: var(--font-size-xl);
    }

    .error-actions {
      flex-direction: column;
      width: 100%;
    }

    .error-actions :global(button) {
      width: 100%;
    }

    .error-meta {
      flex-direction: column;
      gap: var(--space-2);
    }
  }
</style>