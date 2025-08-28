<script lang="ts">
  import { page } from '$app/stores';
  import { NAVIGATION_ITEMS } from '$lib/constants';
  import { authState, themeStore } from '$lib/stores';
  import { isProtectedRoute } from '$lib/utils/auth';
  import Icon from './Icon.svelte';
  import UserProfile from '../auth/UserProfile.svelte';
  import GoogleSignIn from '../auth/GoogleSignIn.svelte';
  
  // Convert mobile menu state to Svelte 5 runes
  let mobileMenuOpen = $state(false);
  
  function toggleMobileMenu() {
    mobileMenuOpen = !mobileMenuOpen;
  }
  
  function closeMobileMenu() {
    mobileMenuOpen = false;
  }
  
  // Convert reactive statements to Svelte 5 $derived
  const currentPath = $derived($page.url.pathname);
  // Access reactive authentication state directly
  const authenticated = $derived(authState.authenticated);
  const user = $derived(authState.user);
  const currentTheme = $derived(themeStore.resolved);
  
  function toggleTheme() {
    themeStore.toggle();
  }
  
  // Filter navigation items based on authentication status using $derived
  const visibleNavItems = $derived(NAVIGATION_ITEMS.filter(item => {
    // Show all items if authenticated
    if (authenticated) return true;
    
    // Show only non-protected items if not authenticated
    return !item.protected;
  }));
</script>

<nav class="nav-main">
  <div class="nav-container">
    <!-- Left: Logo -->
    <div class="nav-left">
      <a href="/" class="nav-brand" onclick={closeMobileMenu}>
        <Icon name="shield" size={32} />
        <div class="brand-text">
          <span class="brand-name">GUARDIAN</span>
          <span class="brand-tagline">Pharmaceutical Compliance</span>
        </div>
      </a>
    </div>
    
    <!-- Right: Navigation & Authentication -->
    <div class="nav-right">
      <!-- Desktop navigation -->
      <div class="nav-links desktop-nav">
        {#each visibleNavItems as item}
          <a 
            href={item.href} 
            class="nav-link"
            class:active={currentPath === item.href}
            title={item.description || item.label}
          >
            <Icon name={item.icon} size={16} />
            {item.label}
          </a>
        {/each}
      </div>
      
      <!-- Theme toggle -->
      <button 
        class="theme-toggle desktop-nav"
        onclick={toggleTheme}
        aria-label="Toggle theme"
        title="Toggle theme ({currentTheme === 'dark' ? 'Switch to light' : 'Switch to dark'})"
      >
        <Icon name={currentTheme === 'dark' ? 'moon' : 'sun'} size={18} />
      </button>
      
      <!-- Authentication section -->
      <div class="auth-section desktop-nav">
        {#if authenticated && user}
          <UserProfile showDropdown={true} showSessionInfo={false} />
        {:else}
          <GoogleSignIn variant="secondary" size="sm" customText="Sign In" />
        {/if}
      </div>
      
      <!-- Mobile menu button -->
      <button 
        class="mobile-menu-button"
        onclick={toggleMobileMenu}
        aria-label="Toggle menu"
      >
        <Icon name={mobileMenuOpen ? 'close' : 'menu'} size={24} />
      </button>
    </div>
  </div>
  
  <!-- Mobile navigation -->
  {#if mobileMenuOpen}
    <div class="mobile-nav" class:open={mobileMenuOpen}>
      <!-- Mobile authentication section -->
      <div class="mobile-auth-section">
        {#if authenticated && user}
          <UserProfile showDropdown={false} compact={false} />
        {:else}
          <GoogleSignIn variant="primary" size="md" fullWidth={true} customText="Sign in with Google" />
        {/if}
      </div>
      
      <!-- Mobile navigation links -->
      <div class="mobile-nav-links">
        {#each visibleNavItems as item}
          <a 
            href={item.href} 
            class="nav-link mobile-nav-link"
            class:active={currentPath === item.href}
            onclick={closeMobileMenu}
          >
            <Icon name={item.icon} size={20} />
            <div class="mobile-nav-text">
              <span class="nav-label">{item.label}</span>
              {#if item.description}
                <span class="nav-description">{item.description}</span>
              {/if}
            </div>
          </a>
        {/each}
        
        <!-- Theme toggle for mobile -->
        <button 
          class="nav-link mobile-nav-link theme-toggle-mobile"
          onclick={toggleTheme}
          aria-label="Toggle theme"
        >
          <Icon name={currentTheme === 'dark' ? 'moon' : 'sun'} size={20} />
          {currentTheme === 'dark' ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>
    </div>
  {/if}
</nav>

<style>
  .nav-main {
    position: fixed;
    top: var(--space-6);
    left: 0;
    right: 0;
    z-index: var(--z-dropdown);
    padding: 0;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }

  .nav-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--space-3) var(--space-8);
    margin: 0 var(--space-6);
    width: calc(100% - var(--space-12));
    background: #ffffff;
    border-radius: 100px;
    box-shadow: 0 12px 24px -6px rgba(0, 0, 0, 0.08);
    transform: translateZ(0);
    -webkit-transform: translateZ(0);
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    border: 0;
    outline: 0;
  }
  
  .nav-container * {
    border-bottom: none !important;
  }
  
  .nav-container:focus,
  .nav-container:active,
  .nav-container:focus-within {
    outline: none;
    border: 0;
  }
  
  /* Ensure nav element itself has no borders or backgrounds */
  nav {
    background: transparent !important;
    border: none !important;
  }
  
  .nav-main,
  .nav-main * {
    border: 0;
    outline: 0;
  }
  
  /* Ensure only the pill has styling */
  nav > * {
    background: transparent !important;
  }
  
  nav .nav-container {
    background: #ffffff !important;
  }
  
  :global(html[data-theme="dark"]) nav .nav-container {
    background: rgba(17, 24, 39, 0.95) !important;
  }

  .nav-left {
    display: flex;
    align-items: center;
    flex: 0 0 auto;
  }

  .nav-right {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    flex: 0 0 auto;
  }

  .nav-brand {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-600);
    text-decoration: none;
    flex-shrink: 0;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
    line-height: 1.2;
  }

  .brand-name {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-600);
  }

  .brand-tagline {
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .nav-brand:hover {
    text-decoration: none;
    color: var(--color-primary-700);
  }

  .mobile-menu-button {
    display: none;
    background: none;
    border: none;
    color: var(--color-text);
    cursor: pointer;
    padding: var(--space-2);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
  }

  .mobile-menu-button:hover {
    background: var(--color-gray-100);
    transform: scale(1.05);
  }

  .desktop-nav {
    display: flex;
    align-items: center;
    gap: var(--space-6);
  }

  .auth-section {
    margin-left: var(--space-4);
    padding-left: var(--space-4);
    border-left: 1px solid var(--color-border);
  }
  
  .theme-toggle {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--space-2);
    background: none;
    border: none;
    color: var(--color-text-secondary);
    cursor: pointer;
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
  }
  
  .theme-toggle:hover {
    color: var(--color-text);
    background: var(--color-gray-100);
  }
  
  .theme-toggle-mobile {
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
  }

  .nav-link {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-secondary);
    text-decoration: none;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
  }

  .nav-link:hover {
    color: var(--color-text);
    background: var(--color-gray-100);
    text-decoration: none;
  }

  .nav-link.active {
    color: var(--color-primary-600);
    background: var(--color-primary-50);
  }

  .mobile-nav {
    display: none;
    flex-direction: column;
    padding: var(--space-4);
    background: var(--color-surface);
    gap: var(--space-2);
    margin-top: var(--space-2);
    border-radius: var(--radius-xl);
    border: 1px solid var(--color-border);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.95);
    margin-left: var(--space-4);
    margin-right: var(--space-4);
  }
  
  :global(html[data-theme="dark"]) .mobile-nav {
    background: rgba(17, 24, 39, 0.95);
  }

  .mobile-nav-link {
    width: 100%;
    justify-content: flex-start;
    padding: var(--space-3) var(--space-4);
  }

  .mobile-auth-section {
    padding: var(--space-4);
    border-bottom: 1px solid var(--color-border);
    margin-bottom: var(--space-2);
  }

  .mobile-nav-links {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .mobile-nav-text {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    flex: 1;
  }

  .nav-label {
    font-weight: var(--font-weight-medium);
    color: inherit;
  }

  .nav-description {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    line-height: var(--line-height-tight);
    opacity: 0.8;
  }

  @media (max-width: 768px) {
    .nav-main {
      top: var(--space-4);
      padding: 0;
    }
    
    .nav-container {
      padding: var(--space-3) var(--space-4);
      margin: 0 var(--space-3);
      width: calc(100% - var(--space-6));
      border-radius: 100px;
    }

    .mobile-menu-button {
      display: block;
    }

    .desktop-nav {
      display: none;
    }

    .auth-section {
      display: none;
    }

    .mobile-nav {
      display: flex;
      margin-left: var(--space-2);
      margin-right: var(--space-2);
    }

    .mobile-nav.open {
      animation: slide-down 0.2s ease-in-out;
    }

    .brand-tagline {
      display: none;
    }

    .brand-name {
      font-size: var(--font-size-base);
    }
  }

  @keyframes slide-down {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
</style>