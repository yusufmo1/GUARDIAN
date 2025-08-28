<script lang="ts">
  import type { Snippet } from 'svelte';
  
  interface Props {
    padding?: 'sm' | 'md' | 'lg';
    hover?: boolean;
    glass?: boolean;
    children?: Snippet;
  }
  
  let { 
    padding = 'md',
    hover = false,
    glass = false,
    children
  }: Props = $props();
  
  const classes = $derived([
    'card',
    `card-${padding}`,
    hover && 'card-hover',
    glass && 'card-glass'
  ].filter(Boolean).join(' '));
</script>

<div class={classes}>
  {@render children?.()}
</div>

<style>
  .card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-normal);
  }

  .card-sm {
    padding: var(--space-4);
  }

  .card-md {
    padding: var(--space-6);
  }

  .card-lg {
    padding: var(--space-8);
  }

  .card-hover:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
  }

  .card-glass {
    background: var(--glass-background-strong);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
  }
</style>