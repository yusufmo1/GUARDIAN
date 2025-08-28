<script lang="ts">
  import { authStore, authLoading, authError } from '$lib/stores';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  
  interface Props {
    variant?: 'primary' | 'secondary';
    size?: 'sm' | 'md' | 'lg';
    fullWidth?: boolean;
    showIcon?: boolean;
    customText?: string;
  }
  
  let { 
    variant = 'primary',
    size = 'md', 
    fullWidth = false,
    showIcon = true,
    customText = ''
  }: Props = $props();
  
  // Convert reactive statements to Svelte 5 $derived
  const isLoading = $derived(authLoading());
  const error = $derived(authError());
  
  function handleGoogleSignIn() {
    authStore.clearError();
    authStore.initiateGoogleAuth();
  }
</script>

<div class="google-signin">
  <Button
    variant={variant}
    size={size}
    fullWidth={fullWidth}
    loading={isLoading}
    disabled={isLoading}
    onclick={handleGoogleSignIn}
    class="google-signin-button"
  >
    {#if showIcon && !isLoading}
      <div class="google-icon">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M17.64 9.20454C17.64 8.56636 17.5827 7.95273 17.4764 7.36364H9V10.8455H13.8436C13.635 11.9709 13.0009 12.9232 12.0477 13.5614V15.8195H14.9564C16.6582 14.2527 17.64 11.9455 17.64 9.20454Z" fill="#4285F4"/>
          <path d="M9 18C11.43 18 13.4673 17.1941 14.9564 15.8195L12.0477 13.5614C11.2418 14.1014 10.2109 14.4205 9 14.4205C6.65591 14.4205 4.67182 12.8373 3.96409 10.71H0.957275V13.0418C2.43818 15.9832 5.48182 18 9 18Z" fill="#34A853"/>
          <path d="M3.96409 10.71C3.78409 10.17 3.68182 9.59318 3.68182 9C3.68182 8.40682 3.78409 7.83 3.96409 7.29V4.95818H0.957275C0.347727 6.17318 0 7.54773 0 9C0 10.4523 0.347727 11.8268 0.957275 13.0418L3.96409 10.71Z" fill="#FBBC05"/>
          <path d="M9 3.57955C10.3214 3.57955 11.5077 4.03364 12.4405 4.92545L15.0218 2.34409C13.4632 0.891818 11.4259 0 9 0C5.48182 0 2.43818 2.01682 0.957275 4.95818L3.96409 7.29C4.67182 5.16273 6.65591 3.57955 9 3.57955Z" fill="#EA4335"/>
        </svg>
      </div>
    {/if}
    
    {#if isLoading}
      <Icon name="loading" size={16} class="animate-spin" />
      Signing in...
    {:else}
      {customText || 'Sign in with Google'}
    {/if}
  </Button>
  
  {#if error}
    <div class="error-message">
      <Icon name="error" size={16} />
      <span>{error}</span>
    </div>
  {/if}
</div>

<style>
  .google-signin {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  :global(.google-signin-button) {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    position: relative;
    border: 1px solid var(--color-gray-300);
    background: var(--color-white);
    color: var(--color-gray-700);
    font-weight: var(--font-weight-medium);
    transition: all var(--transition-fast);
  }

  :global(.google-signin-button:hover) {
    background: var(--color-gray-50);
    border-color: var(--color-gray-400);
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  :global(.google-signin-button:active) {
    transform: translateY(0);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }

  :global(.google-signin-button:disabled) {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .google-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-3);
    background: var(--color-red-50);
    border: 1px solid var(--color-red-200);
    border-radius: var(--radius-md);
    color: var(--color-red-600);
    font-size: var(--font-size-sm);
  }

  /* Variant overrides */
  :global(.google-signin-button.variant-primary) {
    background: var(--color-primary-600);
    border-color: var(--color-primary-600);
    color: var(--color-white);
  }

  :global(.google-signin-button.variant-primary:hover) {
    background: var(--color-primary-700);
    border-color: var(--color-primary-700);
  }

  /* Animations */
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }
</style>