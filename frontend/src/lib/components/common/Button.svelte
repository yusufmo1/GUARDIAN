<script lang="ts">
  import type { ButtonProps } from '$lib/types';
  import type { Snippet } from 'svelte';
  import Icon from './Icon.svelte';
  
  type ButtonVariant = 'primary' | 'secondary' | 'success' | 'warning' | 'error';
  type ButtonSize = 'sm' | 'md' | 'lg';
  
  interface Props {
    variant?: ButtonVariant;
    size?: ButtonSize;
    disabled?: boolean;
    loading?: boolean;
    fullWidth?: boolean;
    href?: string;
    type?: 'button' | 'submit' | 'reset';
    title?: string;
    onclick?: (event: MouseEvent) => void;
    children?: Snippet;
  }
  
  let { 
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    fullWidth = false,
    href,
    type = 'button',
    title,
    onclick,
    children
  }: Props = $props();
  
  function handleClick(event: MouseEvent) {
    if (disabled || loading) {
      event.preventDefault();
      return;
    }
    onclick?.(event);
  }
  
  const classes = $derived([
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    disabled && 'btn-disabled',
    loading && 'btn-loading',
    fullWidth && 'btn-full-width'
  ].filter(Boolean).join(' '));
</script>

{#if href}
  <a 
    {href}
    {title}
    class={classes}
    class:disabled
    onclick={handleClick}
    role="button"
    tabindex={disabled ? -1 : 0}
  >
    {#if loading}
      <Icon name="loading" size={16} class="spin" />
    {/if}
    {@render children?.()}
  </a>
{:else}
  <button 
    {type}
    {title}
    class={classes}
    {disabled}
    onclick={handleClick}
  >
    {#if loading}
      <Icon name="loading" size={16} class="spin" />
    {/if}
    {@render children?.()}
  </button>
{/if}

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    font-family: inherit;
    font-weight: var(--font-weight-medium);
    line-height: 1;
    border: 1px solid transparent;
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: all var(--transition-fast);
    text-decoration: none;
    position: relative;
    overflow: hidden;
  }

  .btn:focus {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
  }

  .btn:disabled,
  .btn.disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  /* Sizes */
  .btn-sm {
    padding: var(--space-2) var(--space-3);
    font-size: var(--font-size-xs);
  }

  .btn-md {
    padding: var(--space-3) var(--space-4);
    font-size: var(--font-size-sm);
  }

  .btn-lg {
    padding: var(--space-4) var(--space-6);
    font-size: var(--font-size-base);
  }

  /* Variants */
  .btn-primary {
    background: var(--color-primary-600);
    color: white;
    border-color: var(--color-primary-600);
  }

  .btn-primary:hover:not(:disabled):not(.disabled) {
    background: var(--color-primary-700);
    border-color: var(--color-primary-700);
    text-decoration: none;
  }

  .btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border-color: var(--color-border);
  }

  .btn-secondary:hover:not(:disabled):not(.disabled) {
    background: var(--color-gray-100);
    text-decoration: none;
  }

  .btn-success {
    background: var(--color-success-600);
    color: white;
    border-color: var(--color-success-600);
  }

  .btn-success:hover:not(:disabled):not(.disabled) {
    background: var(--color-success-700);
    border-color: var(--color-success-700);
    text-decoration: none;
  }

  .btn-warning {
    background: var(--color-warning-600);
    color: white;
    border-color: var(--color-warning-600);
  }

  .btn-warning:hover:not(:disabled):not(.disabled) {
    background: var(--color-warning-700);
    border-color: var(--color-warning-700);
    text-decoration: none;
  }

  .btn-error {
    background: var(--color-error-600);
    color: white;
    border-color: var(--color-error-600);
  }

  .btn-error:hover:not(:disabled):not(.disabled) {
    background: var(--color-error-700);
    border-color: var(--color-error-700);
    text-decoration: none;
  }

  /* Full width */
  .btn-full-width {
    width: 100%;
  }

  /* Loading state */
  .btn-loading {
    cursor: wait;
  }

  /* Loading spinner styles are now handled by the Icon component */
</style>