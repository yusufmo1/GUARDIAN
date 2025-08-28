<script lang="ts">
  import { untrack } from 'svelte';
  import { toastStore } from '$lib/stores/toast';
  import { TOAST_DURATIONS } from '$lib/constants';
  import Icon from './Icon.svelte';
  
  // Track active timeouts to clean them up properly
  const activeTimeouts = new Map<string, number>();
  
  function getToastIcon(type: string) {
    switch (type) {
      case 'success': return 'check';
      case 'error': return 'error';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'info';
    }
  }
  
  function dismissToast(id: string) {
    // Clear timeout if it exists
    const timeoutId = activeTimeouts.get(id);
    if (timeoutId) {
      clearTimeout(timeoutId);
      activeTimeouts.delete(id);
    }
    toastStore.remove(id);
  }
  
  // Effect to handle auto-removal of toasts
  // Using untrack to prevent loops when removing toasts
  $effect(() => {
    const currentToasts = $toastStore;
    
    // Schedule removal for any new toasts
    currentToasts.forEach(toast => {
      if (!activeTimeouts.has(toast.id) && toast.duration && toast.duration > 0) {
        const timeoutId = setTimeout(() => {
          // Use untrack to prevent reactive dependencies
          untrack(() => dismissToast(toast.id));
        }, toast.duration);
        
        activeTimeouts.set(toast.id, timeoutId);
      }
    });
    
    // Clean up timeouts for removed toasts
    activeTimeouts.forEach((timeoutId, toastId) => {
      if (!currentToasts.some(t => t.id === toastId)) {
        clearTimeout(timeoutId);
        activeTimeouts.delete(toastId);
      }
    });
  });
</script>

<div class="toast-container">
  {#each $toastStore as toast (toast.id)}
    <div 
      class="toast toast-{toast.type}"
      role="alert"
      aria-live="polite"
    >
      <div class="toast-icon">
        <Icon name={getToastIcon(toast.type)} size={20} />
      </div>
      
      <div class="toast-content">
        <div class="toast-title">{toast.title}</div>
        {#if toast.message}
          <div class="toast-message">{toast.message}</div>
        {/if}
        
        {#if toast.actions}
          <div class="toast-actions">
            {#each toast.actions as action}
              <button 
                class="toast-action"
                onclick={action.action}
              >
                {action.label}
              </button>
            {/each}
          </div>
        {/if}
      </div>
      
      <button 
        class="toast-close"
        onclick={() => dismissToast(toast.id)}
        aria-label="Close notification"
      >
        <Icon name="close" size={16} />
      </button>
    </div>
  {/each}
</div>

<style>
  .toast-container {
    position: fixed;
    top: var(--space-6);
    right: var(--space-6);
    z-index: var(--z-toast);
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    max-width: 400px;
    width: 100%;
  }

  .toast {
    display: flex;
    align-items: flex-start;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    animation: toast-enter 0.3s ease-out;
  }

  .toast-success {
    border-left: 4px solid var(--color-success-500);
  }

  .toast-error {
    border-left: 4px solid var(--color-error-500);
  }

  .toast-warning {
    border-left: 4px solid var(--color-warning-500);
  }

  .toast-info {
    border-left: 4px solid var(--color-primary-500);
  }

  .toast-icon {
    flex-shrink: 0;
    color: var(--color-text-secondary);
  }

  .toast-success .toast-icon {
    color: var(--color-success-600);
  }

  .toast-error .toast-icon {
    color: var(--color-error-600);
  }

  .toast-warning .toast-icon {
    color: var(--color-warning-600);
  }

  .toast-info .toast-icon {
    color: var(--color-primary-600);
  }

  .toast-content {
    flex: 1;
    min-width: 0;
  }

  .toast-title {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin-bottom: var(--space-1);
  }

  .toast-message {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
  }

  .toast-actions {
    display: flex;
    gap: var(--space-2);
    margin-top: var(--space-3);
  }

  .toast-action {
    background: none;
    border: none;
    color: var(--color-primary-600);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    transition: background-color var(--transition-fast);
  }

  .toast-action:hover {
    background: var(--color-primary-50);
  }

  .toast-close {
    flex-shrink: 0;
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: var(--space-1);
    border-radius: var(--radius-sm);
    transition: all var(--transition-fast);
  }

  .toast-close:hover {
    color: var(--color-text);
    background: var(--color-gray-100);
  }

  @keyframes toast-enter {
    from {
      opacity: 0;
      transform: translateX(100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @media (max-width: 640px) {
    .toast-container {
      top: var(--space-4);
      right: var(--space-4);
      left: var(--space-4);
      max-width: none;
    }
  }
</style>