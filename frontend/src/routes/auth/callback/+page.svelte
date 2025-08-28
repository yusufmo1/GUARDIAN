<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { authStore, authLoading, authError } from '$lib/stores';
  import Icon from '$lib/components/common/Icon.svelte';
  import Card from '$lib/components/common/Card.svelte';
  
  // Convert local state to Svelte 5 runes
  let processing = $state(true);
  let message = $state('Processing authentication...');
  let isError = $state(false);
  
  // Convert reactive statements to Svelte 5 $derived
  const loading = $derived(authLoading);
  const error = $derived(authError);
  
  // Convert onMount to $effect
  $effect(() => {
    if (!browser) return;
    (async () => {
    try {
      // Get OAuth parameters from URL
      const urlParams = $page.url.searchParams;
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');
      
      console.log('OAuth callback received:', { code: !!code, state: !!state, error });
      
      // Handle OAuth error
      if (error) {
        console.error('OAuth error received:', error);
        isError = true;
        message = `Authentication failed: ${error}`;
        
        // Defer navigation to avoid reactive loops
        setTimeout(() => {
          queueMicrotask(() => {
            goto('/login');
          });
        }, 3000);
        return;
      }
      
      // Validate required parameters
      if (!code || !state) {
        console.error('Missing OAuth parameters:', { code: !!code, state: !!state });
        isError = true;
        message = 'Invalid authentication response - missing required parameters';
        
        // Defer navigation to avoid reactive loops
        setTimeout(() => {
          queueMicrotask(() => {
            goto('/login');
          });
        }, 3000);
        return;
      }
      
      console.log('OAuth parameters validated, processing callback...');
      message = 'Authenticating with Google...';
      
      // Handle the OAuth callback
      await authStore.handleGoogleCallback(code, state);
      
      console.log('Authentication successful, redirecting...');
      message = 'Authentication successful! Redirecting...';
      
      // The authStore handles the redirect, so we don't need a fallback here
      // Removing the duplicate goto() call prevents navigation conflicts
      
    } catch (err: any) {
      console.error('OAuth callback processing failed:', err);
      isError = true;
      message = err.message || 'Authentication failed. Please try again.';
      
      setTimeout(() => {
        goto('/login');
      }, 3000);
    } finally {
      processing = false;
    }
    })();
  });
</script>

<svelte:head>
  <title>Authenticating - GUARDIAN</title>
  <meta name="description" content="Processing Google authentication for GUARDIAN" />
</svelte:head>

<div class="callback-page">
  <div class="callback-container">
    <Card>
      <div class="callback-content">
        <!-- Logo -->
        <div class="logo-section">
          <Icon name="shield" size={48} class="logo-icon" />
          <h1 class="app-title">GUARDIAN</h1>
        </div>
        
        <!-- Status -->
        <div class="status-section" class:error={isError}>
          <div class="status-icon">
            {#if isError}
              <Icon name="error" size={32} class="error-icon" />
            {:else if processing || loading}
              <Icon name="loading" size={32} class="loading-icon animate-spin" />
            {:else}
              <Icon name="check" size={32} class="success-icon" />
            {/if}
          </div>
          
          <div class="status-content">
            <h2 class="status-title">
              {#if isError}
                Authentication Failed
              {:else if processing || loading}
                Authenticating
              {:else}
                Success!
              {/if}
            </h2>
            
            <p class="status-message">{message}</p>
            
            {#if error && isError}
              <div class="error-details">
                <Icon name="warning" size={16} />
                <span>{error}</span>
              </div>
            {/if}
          </div>
        </div>
        
        <!-- Progress -->
        {#if processing || loading}
          <div class="progress-section">
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
            <p class="progress-text">
              {#if processing}
                Processing OAuth response...
              {:else if loading}
                Validating session...
              {/if}
            </p>
          </div>
        {/if}
        
        <!-- Actions -->
        {#if isError}
          <div class="actions-section">
            <button 
              class="retry-button"
              onclick={() => goto('/login')}
            >
              <Icon name="arrow-left" size={16} />
              Back to Sign In
            </button>
          </div>
        {/if}
      </div>
    </Card>
  </div>
</div>

<style>
  .callback-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--color-primary-50) 0%, var(--color-blue-50) 100%);
    padding: var(--space-6);
  }

  .callback-container {
    width: 100%;
    max-width: 480px;
  }

  .callback-content {
    padding: var(--space-8) var(--space-6);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-6);
    text-align: center;
  }

  .logo-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-2);
  }

  :global(.logo-icon) {
    color: var(--color-primary-600);
  }

  .app-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-600);
    margin: 0;
    letter-spacing: -0.02em;
  }

  .status-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
  }

  .status-section.error {
    --status-color: var(--color-red-600);
  }

  .status-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: var(--color-primary-50);
  }

  .status-section.error .status-icon {
    background: var(--color-red-50);
  }

  :global(.loading-icon) {
    color: var(--color-primary-600);
  }

  :global(.success-icon) {
    color: var(--color-green-600);
  }

  :global(.error-icon) {
    color: var(--color-red-600);
  }

  .status-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .status-title {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
    margin: 0;
  }

  .status-section.error .status-title {
    color: var(--color-red-600);
  }

  .status-message {
    font-size: var(--font-size-base);
    color: var(--color-text-muted);
    margin: 0;
    line-height: 1.5;
  }

  .error-details {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    padding: var(--space-3);
    background: var(--color-red-50);
    border: 1px solid var(--color-red-200);
    border-radius: var(--radius-md);
    color: var(--color-red-600);
    font-size: var(--font-size-sm);
    margin-top: var(--space-2);
  }

  .progress-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .progress-bar {
    width: 100%;
    height: 4px;
    background: var(--color-gray-200);
    border-radius: 2px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: var(--color-primary-600);
    border-radius: 2px;
    animation: progress 2s ease-in-out infinite;
  }

  .progress-text {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin: 0;
  }

  .actions-section {
    width: 100%;
    margin-top: var(--space-4);
  }

  .retry-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    width: 100%;
    padding: var(--space-3) var(--space-4);
    background: var(--color-primary-600);
    color: var(--color-white);
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: background-color var(--transition-fast);
  }

  .retry-button:hover {
    background: var(--color-primary-700);
  }

  /* Animations */
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @keyframes progress {
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

  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @media (max-width: 480px) {
    .callback-page {
      padding: var(--space-4);
    }
    
    .callback-content {
      padding: var(--space-6) var(--space-4);
    }
  }
</style>