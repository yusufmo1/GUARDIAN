<script lang="ts">
  import { authStore, authState } from '$lib/stores';
  import Icon from '$lib/components/common/Icon.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import { onMount } from 'svelte';
  
  interface Props {
    showDropdown?: boolean;
    showSessionInfo?: boolean;
    compact?: boolean;
  }
  
  let { 
    showDropdown = true,
    showSessionInfo = false,
    compact = false
  }: Props = $props();
  
  // Convert dropdown state to Svelte 5 runes
  let dropdownOpen = $state(false);
  let dropdownElement = $state<HTMLDivElement>();
  
  // Convert reactive statements to Svelte 5 $derived
  const user = $derived(authState.user);
  const session = $derived(authState.session);
  const isLoading = $derived(authState.loading);
  
  function toggleDropdown() {
    dropdownOpen = !dropdownOpen;
  }
  
  function closeDropdown() {
    dropdownOpen = false;
  }
  
  function handleLogout() {
    closeDropdown();
    authStore.logout();
  }
  
  function handleRefreshTokens() {
    closeDropdown();
    authStore.refreshTokens();
  }
  
  function updateUserData() {
    authStore.updateUserData();
  }
  
  // Close dropdown when clicking outside
  function handleClickOutside(event: MouseEvent) {
    if (dropdownElement && !dropdownElement.contains(event.target as Node)) {
      closeDropdown();
    }
  }
  
  onMount(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  });
  
  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
  
  function getInitials(name: string): string {
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  }
</script>

{#if user}
  <div class="user-profile" class:compact bind:this={dropdownElement}>
    <!-- User Info Display -->
    <button 
      class="user-button" 
      class:dropdown-enabled={showDropdown}
      onclick={showDropdown ? toggleDropdown : undefined}
      disabled={isLoading}
    >
      <div class="user-avatar">
        {getInitials(user.name)}
      </div>
      
      {#if !compact}
        <div class="user-info">
          <div class="user-name">{user.name}</div>
          <div class="user-email">{user.email}</div>
        </div>
      {/if}
      
      {#if showDropdown}
        <Icon 
          name={dropdownOpen ? "chevron-up" : "chevron-down"} 
          size={16} 
          class="dropdown-icon" 
        />
      {/if}
      
      {#if isLoading}
        <Icon name="loading" size={16} class="animate-spin loading-icon" />
      {/if}
    </button>
    
    <!-- Dropdown Menu -->
    {#if showDropdown && dropdownOpen}
      <div class="dropdown-menu">
        <div class="dropdown-header">
          <div class="user-avatar large">
            {getInitials(user.name)}
          </div>
          <div class="user-details">
            <div class="user-name">{user.name}</div>
            <div class="user-email">{user.email}</div>
            {#if user.active_sessions}
              <div class="session-count">
                {user.active_sessions} active session{user.active_sessions !== 1 ? 's' : ''}
              </div>
            {/if}
          </div>
        </div>
        
        {#if showSessionInfo && session}
          <div class="session-info">
            <div class="session-item">
              <Icon name="clock" size={14} />
              <span>Last activity: {formatDate(session.last_activity)}</span>
            </div>
            <div class="session-item">
              <Icon name="calendar" size={14} />
              <span>Session started: {formatDate(session.created_at)}</span>
            </div>
            {#if session.expires_at}
              <div class="session-item">
                <Icon name="warning" size={14} />
                <span>Expires: {formatDate(session.expires_at)}</span>
              </div>
            {/if}
          </div>
        {/if}
        
        <div class="dropdown-actions">
          <a href="/account" class="dropdown-item" onclick={closeDropdown}>
            <Icon name="user" size={16} />
            <span>My Account</span>
          </a>
          
          <button class="dropdown-item" onclick={updateUserData}>
            <Icon name="refresh" size={16} />
            <span>Update Profile</span>
          </button>
          
          <button class="dropdown-item" onclick={handleRefreshTokens}>
            <Icon name="rotate-cw" size={16} />
            <span>Refresh Tokens</span>
          </button>
          
          <a href="/settings" class="dropdown-item" onclick={closeDropdown}>
            <Icon name="settings" size={16} />
            <span>Settings</span>
          </a>
          
          <div class="dropdown-divider"></div>
          
          <button class="dropdown-item logout" onclick={handleLogout}>
            <Icon name="logout" size={16} />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    {/if}
  </div>
{:else}
  <div class="user-profile-placeholder">
    <Icon name="user" size={24} class="placeholder-icon" />
  </div>
{/if}

<style>
  .user-profile {
    position: relative;
    display: flex;
    align-items: center;
  }

  .user-profile.compact {
    max-width: 40px;
  }

  .user-button {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2) var(--space-3);
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: background-color var(--transition-fast);
    width: 100%;
    text-align: left;
  }

  .user-button:hover {
    background: var(--color-gray-100);
  }

  .user-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .user-button.dropdown-enabled {
    cursor: pointer;
  }

  .user-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--color-primary-600);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-bold);
    flex-shrink: 0;
  }

  .user-avatar.large {
    width: 48px;
    height: 48px;
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-bold);
  }

  .user-info {
    flex: 1;
    min-width: 0;
  }

  .user-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .user-email {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dropdown-icon {
    color: var(--color-text-muted);
    transition: transform var(--transition-fast);
  }

  .loading-icon {
    color: var(--color-primary-600);
  }

  .dropdown-menu {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 280px;
    background: var(--color-white);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    z-index: var(--z-dropdown);
    margin-top: var(--space-2);
    overflow: hidden;
  }

  .dropdown-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-bottom: 1px solid var(--color-border);
  }

  .user-details {
    flex: 1;
    min-width: 0;
  }

  .user-details .user-name {
    font-size: var(--font-size-base);
    margin-bottom: var(--space-1);
  }

  .user-details .user-email {
    font-size: var(--font-size-sm);
    margin-bottom: var(--space-1);
  }

  .session-count {
    font-size: var(--font-size-xs);
    color: var(--color-primary-600);
    font-weight: var(--font-weight-medium);
  }

  .session-info {
    padding: var(--space-3) var(--space-4);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-blue-50);
  }

  .session-item {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin-bottom: var(--space-1);
  }

  .session-item:last-child {
    margin-bottom: 0;
  }

  .dropdown-actions {
    padding: var(--space-2);
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    width: 100%;
    padding: var(--space-2) var(--space-3);
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: background-color var(--transition-fast);
    font-size: var(--font-size-sm);
    color: var(--color-text);
    text-align: left;
    text-decoration: none;
  }

  a.dropdown-item {
    text-decoration: none;
  }

  .dropdown-item:hover {
    background: var(--color-gray-100);
    text-decoration: none;
  }

  .dropdown-item.logout {
    color: var(--color-red-600);
  }

  .dropdown-item.logout:hover {
    background: var(--color-red-50);
  }

  .dropdown-divider {
    height: 1px;
    background: var(--color-border);
    margin: var(--space-2) 0;
  }

  .user-profile-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--color-gray-200);
    color: var(--color-text-muted);
  }

  .placeholder-icon {
    opacity: 0.5;
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