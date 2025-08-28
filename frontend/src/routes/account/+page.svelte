<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { authStore, authState, toastStore } from '$lib/stores';
  import { formatDate } from '$lib/utils';
  import { authApi, sessionApi, GuardianApiError } from '$lib/services/api';
  import type { UserSession } from '$lib/types';

  // Convert reactive store access to $derived
  // Access reactive authentication state directly
  const authenticated = $derived(authState.authenticated);
  const user = $derived(authState.user);
  
  // Local state using Svelte 5 runes
  let loading = $state(false);
  let sessions = $state<UserSession[]>([]);
  let sessionStats = $state<any>(null);
  let refreshingTokens = $state(false);
  let loadingSessions = $state(false);
  let loadingStats = $state(false);

  // Redirect if not authenticated
  onMount(() => {
    if (!authenticated) {
      console.log('Account page: Not authenticated, redirecting to login');
      // Defer navigation to break any reactive chains
      queueMicrotask(() => {
        goto('/login?redirect=/account');
      });
      return;
    }
    
    // Load user sessions and stats
    loadUserSessions();
    loadSessionStats();
  });

  // Remove reactive navigation loop - use load function instead
  // The +page.ts load function handles auth redirection

  async function loadUserSessions() {
    try {
      loadingSessions = true;
      const response = await authApi.listSessions();
      
      if (response.success && response.data) {
        sessions = response.data.sessions || [];
      }
    } catch (error) {
      if (error instanceof GuardianApiError) {
        toastStore.error('Failed to Load Sessions', error.message);
      } else {
        toastStore.error('Failed to Load Sessions', 'Could not connect to server');
      }
    } finally {
      loadingSessions = false;
    }
  }

  async function loadSessionStats() {
    try {
      loadingStats = true;
      const response = await sessionApi.getStats();
      
      if (response.success && response.data) {
        sessionStats = response.data;
      }
    } catch (error) {
      console.error('Failed to load session stats:', error);
      // Non-critical error, don't show toast
    } finally {
      loadingStats = false;
    }
  }

  async function handleRefreshTokens() {
    try {
      refreshingTokens = true;
      await authStore.refreshTokens();
      toastStore.success('Tokens Refreshed', 'Your Google Drive tokens have been refreshed');
    } catch (error) {
      toastStore.error('Refresh Failed', 'Failed to refresh tokens. Please try logging in again.');
    } finally {
      refreshingTokens = false;
    }
  }

  async function handleLogout() {
    try {
      loading = true;
      await authStore.logout();
      // authStore.logout handles redirect
    } catch (error) {
      toastStore.error('Logout Failed', 'An error occurred while logging out');
      loading = false;
    }
  }

  function getSessionStatusColor(isActive: boolean): string {
    return isActive ? 'var(--color-success-600)' : 'var(--color-gray-500)';
  }

  function formatStorageSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
  
  function getInitials(name: string): string {
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  }
</script>

<svelte:head>
  <title>Account Settings - GUARDIAN</title>
</svelte:head>

<div class="account-page">
  <div class="page-header">
    <h1>Account Settings</h1>
    <p>Manage your GUARDIAN account, sessions, and Google Drive integration</p>
  </div>

  {#if authenticated && user}
    <div class="account-sections">
      <!-- User Information Section -->
      <section class="account-section">
        <Card>
          <h2>
            <Icon name="user" size={20} />
            User Information
          </h2>
          
          <div class="user-info">
            <div class="user-avatar">
              {#if user.picture}
                <img src={user.picture} alt="{user.name} avatar" />
              {:else}
                {getInitials(user.name)}
              {/if}
            </div>
            
            <div class="user-details">
              <div class="detail-item">
                <span class="detail-label">Name</span>
                <span class="detail-value">{user.name || 'Not provided'}</span>
              </div>
              
              <div class="detail-item">
                <span class="detail-label">Email</span>
                <span class="detail-value">{user.email}</span>
              </div>
              
              <div class="detail-item">
                <span class="detail-label">User ID</span>
                <span class="detail-value mono">{user.id}</span>
              </div>
              
              <div class="detail-item">
                <span class="detail-label">Account Created</span>
                <span class="detail-value">{user.created_at ? formatDate(new Date(user.created_at)) : 'Unknown'}</span>
              </div>
            </div>
          </div>
        </Card>
      </section>

      <!-- Google Drive Integration Section -->
      <section class="account-section">
        <Card>
          <h2>
            <Icon name="cloud" size={20} />
            Google Drive Integration
          </h2>
          
          <div class="integration-info">
            <div class="integration-status">
              <Icon name="check-circle" size={20} color="var(--color-success-600)" />
              <span>Connected to Google Drive</span>
            </div>
            
            <p class="integration-description">
              Your documents and analysis results are securely stored in your personal Google Drive 
              under the <code>GUARDIAN_Data</code> folder. All data remains private and under your control.
            </p>
            
            {#if sessionStats}
              <div class="storage-stats">
                <h3>Storage Usage</h3>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-label">Documents</span>
                    <span class="stat-value">{sessionStats.total_documents || 0}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Total Size</span>
                    <span class="stat-value">{formatStorageSize(sessionStats.total_storage_bytes || 0)}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Vector Databases</span>
                    <span class="stat-value">{sessionStats.vector_db_count || 0}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">Reports Generated</span>
                    <span class="stat-value">{sessionStats.reports_generated || 0}</span>
                  </div>
                </div>
              </div>
            {/if}
            
            <div class="integration-actions">
              <Button 
                variant="secondary" 
                size="sm"
                loading={refreshingTokens}
                onclick={handleRefreshTokens}
              >
                <Icon name="refresh" size={16} />
                Refresh Tokens
              </Button>
              <Button 
                variant="secondary" 
                size="sm"
                onclick={() => window.open('https://drive.google.com', '_blank')}
              >
                <Icon name="external-link" size={16} />
                Open Google Drive
              </Button>
            </div>
          </div>
        </Card>
      </section>

      <!-- Active Sessions Section -->
      <section class="account-section">
        <Card>
          <div class="section-header">
            <h2>
              <Icon name="activity" size={20} />
              Active Sessions
            </h2>
            <Button 
              variant="secondary" 
              size="sm"
              onclick={loadUserSessions}
              loading={loadingSessions}
            >
              <Icon name="refresh" size={16} />
              Refresh
            </Button>
          </div>
          
          {#if loadingSessions}
            <div class="loading-state">
              <Icon name="loader" size={24} />
              <p>Loading sessions...</p>
            </div>
          {:else if sessions.length > 0}
            <div class="sessions-list">
              {#each sessions as session (session.id)}
                <div class="session-item">
                  <div class="session-icon">
                    <Icon 
                      name={session.is_current ? "monitor" : "smartphone"} 
                      size={20} 
                      color={getSessionStatusColor(session.is_active)}
                    />
                  </div>
                  
                  <div class="session-info">
                    <div class="session-device">
                      {session.user_agent ? session.user_agent.split(' ')[0] : 'Unknown Device'}
                      {#if session.is_current}
                        <span class="current-badge">Current</span>
                      {/if}
                    </div>
                    <div class="session-meta">
                      <span>Created: {formatDate(new Date(session.created_at))}</span>
                      {#if session.expires_at}
                        <span>Expires: {formatDate(new Date(session.expires_at))}</span>
                      {/if}
                    </div>
                  </div>
                  
                  <div class="session-status">
                    <span 
                      class="status-badge"
                      style="color: {getSessionStatusColor(session.is_active)}"
                    >
                      {session.is_active ? 'Active' : 'Expired'}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="empty-state">
              <p>No active sessions found</p>
            </div>
          {/if}
        </Card>
      </section>

      <!-- Privacy & Security Section -->
      <section class="account-section">
        <Card>
          <h2>
            <Icon name="shield" size={20} />
            Privacy & Security
          </h2>
          
          <div class="privacy-info">
            <div class="privacy-item">
              <Icon name="lock" size={18} color="var(--color-success-600)" />
              <div>
                <h4>End-to-End Privacy</h4>
                <p>Your documents and analysis results are never stored on our servers. 
                   All data is processed temporarily and immediately saved to your Google Drive.</p>
              </div>
            </div>
            
            <div class="privacy-item">
              <Icon name="database" size={18} color="var(--color-success-600)" />
              <div>
                <h4>Data Ownership</h4>
                <p>You maintain complete ownership and control of your data. 
                   We only store minimal metadata required for authentication.</p>
              </div>
            </div>
            
            <div class="privacy-item">
              <Icon name="key" size={18} color="var(--color-success-600)" />
              <div>
                <h4>Secure Authentication</h4>
                <p>We use Google OAuth 2.0 for secure authentication. 
                   Your Google credentials are never stored or accessible to us.</p>
              </div>
            </div>
          </div>
        </Card>
      </section>

      <!-- Account Actions Section -->
      <section class="account-section">
        <Card>
          <h2>
            <Icon name="settings" size={20} />
            Account Actions
          </h2>
          
          <div class="account-actions">
            <div class="action-item">
              <div class="action-info">
                <h4>Sign Out</h4>
                <p>Sign out of your GUARDIAN account on this device</p>
              </div>
              <Button 
                variant="secondary"
                onclick={handleLogout}
                loading={loading}
              >
                <Icon name="logout" size={16} />
                Sign Out
              </Button>
            </div>
            
            <div class="action-item danger">
              <div class="action-info">
                <h4>Delete Account</h4>
                <p>Permanently delete your GUARDIAN account and remove all metadata. 
                   Your Google Drive data will remain intact.</p>
              </div>
              <Button 
                variant="error"
                disabled={true}
              >
                <Icon name="trash" size={16} />
                Delete Account
              </Button>
            </div>
          </div>
        </Card>
      </section>
    </div>
  {:else}
    <!-- Not authenticated state -->
    <div class="auth-required">
      <Card>
        <div class="auth-required-content">
          <Icon name="lock" size={48} color="var(--color-gray-400)" />
          <h3>Authentication Required</h3>
          <p>Please sign in to view your account settings.</p>
          <Button variant="primary" onclick={() => goto('/login?redirect=/account')}>
            <Icon name="login" size={16} />
            Sign In to Continue
          </Button>
        </div>
      </Card>
    </div>
  {/if}
</div>

<style>
  .account-page {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .page-header {
    text-align: center;
    margin-bottom: var(--space-4);
  }

  .page-header h1 {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-4);
  }

  .page-header p {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
  }

  .account-sections {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
  }

  .account-section h2 {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-6);
    color: var(--color-text);
  }

  /* User Information Styles */
  .user-info {
    display: flex;
    gap: var(--space-6);
    align-items: flex-start;
  }

  .user-avatar {
    width: 80px;
    height: 80px;
    border-radius: var(--radius-full);
    overflow: hidden;
    background: var(--color-primary-600);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
  }

  .user-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .user-details {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--space-4);
  }

  .detail-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .detail-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    font-weight: var(--font-weight-medium);
  }

  .detail-value {
    font-size: var(--font-size-base);
    color: var(--color-text);
  }

  .detail-value.mono {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);
  }

  /* Google Drive Integration Styles */
  .integration-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .integration-status {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
    background: var(--color-success-50);
    border: 1px solid var(--color-success-200);
    border-radius: var(--radius-lg);
    font-weight: var(--font-weight-medium);
    color: var(--color-success-700);
  }

  .integration-description {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  .integration-description code {
    font-family: var(--font-family-mono);
    font-size: var(--font-size-sm);
    padding: 2px 6px;
    background: var(--color-gray-100);
    border-radius: var(--radius-sm);
  }

  .storage-stats {
    background: var(--color-gray-50);
    padding: var(--space-4);
    border-radius: var(--radius-lg);
    margin: var(--space-4) 0;
  }

  .storage-stats h3 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-3);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: var(--space-4);
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .stat-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
  }

  .stat-value {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
  }

  .integration-actions {
    display: flex;
    gap: var(--space-3);
    margin-top: var(--space-4);
  }

  /* Sessions Section Styles */
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
  }

  .sessions-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .session-item {
    display: flex;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-3);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .session-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: var(--color-surface);
    border-radius: var(--radius-lg);
    flex-shrink: 0;
  }

  .session-info {
    flex: 1;
    min-width: 0;
  }

  .session-device {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  .current-badge {
    font-size: var(--font-size-xs);
    padding: 2px 8px;
    background: var(--color-primary-100);
    color: var(--color-primary-700);
    border-radius: var(--radius-full);
    font-weight: var(--font-weight-medium);
  }

  .session-meta {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    display: flex;
    gap: var(--space-3);
    flex-wrap: wrap;
  }

  .status-badge {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    text-transform: capitalize;
  }

  /* Privacy Section Styles */
  .privacy-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .privacy-item {
    display: flex;
    gap: var(--space-4);
    align-items: flex-start;
  }

  .privacy-item h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-2);
    color: var(--color-text);
  }

  .privacy-item p {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  /* Account Actions Styles */
  .account-actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .action-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .action-item.danger {
    background: var(--color-error-50);
    border-color: var(--color-error-200);
  }

  .action-info h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-1);
    color: var(--color-text);
  }

  .action-info p {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0;
  }

  /* Loading and Empty States */
  .loading-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-8);
    text-align: center;
    color: var(--color-text-muted);
  }

  .loading-state {
    gap: var(--space-3);
  }

  /* Auth Required State */
  .auth-required {
    max-width: var(--max-width-2xl);
    margin: 0 auto;
  }

  .auth-required-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
  }

  .auth-required-content h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
    margin: 0;
  }

  .auth-required-content p {
    color: var(--color-text-secondary);
    margin: 0;
    max-width: 400px;
    line-height: var(--line-height-relaxed);
  }

  /* Responsive Design */
  @media (max-width: 768px) {
    .page-header h1 {
      font-size: var(--font-size-2xl);
    }

    .user-info {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .user-details {
      grid-template-columns: 1fr;
    }

    .integration-actions {
      flex-direction: column;
    }

    .action-item {
      flex-direction: column;
      gap: var(--space-3);
      text-align: center;
    }

    .session-item {
      flex-direction: column;
      text-align: center;
    }

    .privacy-item {
      flex-direction: column;
      text-align: center;
      align-items: center;
    }
  }
</style>