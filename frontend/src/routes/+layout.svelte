<script lang="ts">
  import type { Snippet } from 'svelte';
  import { browser } from '$app/environment';
  import { page } from '$app/stores';
  import '../lib/styles/theme.css';
  import '../lib/styles/components.css';
  import Navigation from '$lib/components/common/Navigation.svelte';
  import Toast from '$lib/components/common/Toast.svelte';
  import { authStore, themeStore, appStore, toastStore } from '$lib/stores';
  import { setupSessionManagement } from '$lib/utils/auth';
  import { setupSessionTimeoutMonitoring } from '$lib/utils/session-timeout';
  
  interface Props {
    children?: Snippet;
  }
  
  let { children }: Props = $props();
  
  // Single non-reactive initialization flag
  let layoutInitialized = false;
  
  // SINGLE CONSOLIDATED EFFECT - prevents all reactive loops
  $effect(() => {
    if (!browser || layoutInitialized) return;
    
    // Set flag IMMEDIATELY before any async operations
    layoutInitialized = true;
    
    console.log('Initializing GUARDIAN frontend...');
    
    // ALL initialization in one synchronous block
    // 1. Theme initialization (synchronous)
    themeStore.initialize();
    
    // 2. Settings initialization (synchronous)
    try {
      const saved = localStorage.getItem('guardian_settings');
      if (saved) {
        console.log('Settings loaded from localStorage');
      }
    } catch (error) {
      console.warn('Failed to load settings:', error);
    }
    
    // 3. Session management setup (synchronous)
    const sessionCleanup = setupSessionManagement();
    
    // 4. Store cleanup functions for later
    (window as any).__guardianCleanup = { sessionCleanup };
    
    // 5. Auth initialization LAST and ASYNC (won't trigger re-runs)
    // Use setTimeout to break out of reactive context completely
    setTimeout(() => {
      authStore.initialize().catch(error => {
        console.error('Failed to initialize auth store:', error);
      });
    }, 0);
    
    // Return cleanup function directly
    return () => {
      if ((window as any).__guardianCleanup) {
        (window as any).__guardianCleanup.sessionCleanup?.();
        delete (window as any).__guardianCleanup;
      }
    };
  });

  // Toast auto-removal is handled by the toast store itself
</script>

<svelte:head>
  <title>GUARDIAN - Pharmaceutical Compliance Analysis</title>
  <meta name="description" content="Automated pharmaceutical protocol compliance analysis against global regulatory standards" />
</svelte:head>

<div class="app">
  <Navigation />
  
  <main class="main-content">
    {@render children?.()}
  </main>
  
  <Toast />
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--color-background);
    position: relative;
    overflow-x: hidden;
  }
  
  /* Pharmaceutical background pattern */
  .app::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: -1;
    background: 
      /* Base color */
      linear-gradient(to bottom, #fafbfd 0%, #f8f9fc 100%),
      /* Subtle molecular grid pattern */
      linear-gradient(90deg, transparent 0%, transparent 49.5%, rgba(59, 130, 246, 0.02) 49.5%, rgba(59, 130, 246, 0.02) 50.5%, transparent 50.5%, transparent 100%),
      linear-gradient(0deg, transparent 0%, transparent 49.5%, rgba(59, 130, 246, 0.02) 49.5%, rgba(59, 130, 246, 0.02) 50.5%, transparent 50.5%, transparent 100%);
    background-size: 100% 100%, 60px 60px, 60px 60px;
    background-position: 0 0, -30px -30px, -30px -30px;
  }
  
  /* Subtle molecular dots at intersections */
  .app::after {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: -1;
    background-image: 
      radial-gradient(circle at center, rgba(59, 130, 246, 0.06) 2px, transparent 2px);
    background-size: 60px 60px;
    background-position: 0 0;
    opacity: 0.6;
  }
  
  /* Dark mode pharmaceutical background */
  :global(html[data-theme="dark"]) .app::before {
    background: 
      /* Base color */
      linear-gradient(to bottom, #0f1114 0%, #0a0b0e 100%),
      /* Subtle molecular grid pattern */
      linear-gradient(90deg, transparent 0%, transparent 49.5%, rgba(59, 130, 246, 0.03) 49.5%, rgba(59, 130, 246, 0.03) 50.5%, transparent 50.5%, transparent 100%),
      linear-gradient(0deg, transparent 0%, transparent 49.5%, rgba(59, 130, 246, 0.03) 49.5%, rgba(59, 130, 246, 0.03) 50.5%, transparent 50.5%, transparent 100%);
  }
  
  :global(html[data-theme="dark"]) .app::after {
    background-image: 
      radial-gradient(circle at center, rgba(99, 102, 241, 0.08) 2px, transparent 2px);
    opacity: 0.4;
  }

  .main-content {
    flex: 1;
    padding: calc(var(--space-20) + var(--space-8)) var(--space-6) var(--space-6);
    max-width: var(--max-width-7xl);
    margin: 0 auto;
    width: 100%;
  }

  /* Full width layout for protocol analysis results */
  :global(body.showing-protocol-analysis) .main-content {
    max-width: none !important;
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }

  @media (max-width: 768px) {
    .main-content {
      padding: calc(var(--space-20) + var(--space-4)) var(--space-4) var(--space-4);
    }
  }
</style>