<script lang="ts">
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { appStore, themeStore, toastStore } from '$lib/stores';
  import type { Theme } from '$lib/stores';
  import { apiClient, health as healthApi, GuardianApiError } from '$lib/services/api';

  // Convert reactive store access to $derived
  const settings = $derived(appStore.settings);
  
  // Convert local state to Svelte 5 runes
  let isDemoMode = $state(false);
  let testingConnection = $state(false);
  let connectionStatus = $state<'unknown' | 'connected' | 'error'>('unknown');
  
  // Convert reactive theme binding to $derived
  const currentTheme = $derived(themeStore.current);

  async function updateApiUrl(url: string) {
    // Update the API client base URL
    apiClient.setBaseUrl(url);
    
    // Test the connection
    await testConnection(url);
    
    // Update settings if successful
    appStore.updateSettings({ apiUrl: url });
    toastStore.success('Settings Updated', 'API URL has been updated');
  }

  async function testConnection(url?: string) {
    try {
      testingConnection = true;
      connectionStatus = 'unknown';
      
      if (url) {
        apiClient.setBaseUrl(url);
      }
      
      const response = await healthApi.check();
      
      if (response.status === 'healthy') {
        connectionStatus = 'connected';
        toastStore.success('Connection Test', 'Successfully connected to GUARDIAN backend');
      } else {
        connectionStatus = 'error';
        toastStore.warning('Connection Test', 'Backend responded but may not be fully operational');
      }
    } catch (error) {
      connectionStatus = 'error';
      if (error instanceof GuardianApiError) {
        toastStore.error('Connection Failed', `Could not connect to backend: ${error.message}`);
      } else {
        toastStore.error('Connection Failed', 'Could not connect to backend server');
      }
    } finally {
      testingConnection = false;
    }
  }

  function resetSettings() {
    appStore.reset();
    toastStore.info('Settings Reset', 'All settings have been reset to defaults');
  }

  function toggleDemoMode() {
    isDemoMode = !isDemoMode;
    toastStore.info('Demo Mode', isDemoMode ? 'Demo mode enabled' : 'Demo mode disabled');
  }

  function handleThemeChange(theme: Theme) {
    themeStore.set(theme);
    toastStore.success('Theme Updated', `Theme changed to ${theme === 'auto' ? 'system preference' : theme}`);
  }

</script>

<svelte:head>
  <title>Settings & Configuration - GUARDIAN</title>
</svelte:head>

<div class="settings-page">
  <div class="page-header">
    <h1>Settings & Configuration</h1>
    <p>Configure GUARDIAN application settings and preferences</p>
  </div>

  <div class="settings-sections">
    <!-- Application Settings -->
    <section class="settings-section">
      <Card>
        <h2>
          <Icon name="settings" size={20} />
          Application Settings
        </h2>
        
        <div class="setting-group">
          <label for="api-url">Backend API URL</label>
          <div class="input-group">
            <input
              id="api-url"
              type="url"
              bind:value={settings.apiUrl}
              placeholder="Leave empty for development proxy"
            />
            <Button 
              variant="secondary" 
              size="sm"
              loading={testingConnection}
              onclick={() => testConnection()}
            >
              <Icon name="activity" size={16} />
              Test
            </Button>
            <Button 
              variant="primary" 
              size="sm"
              disabled={testingConnection}
              onclick={() => updateApiUrl(settings.apiUrl)}
            >
              <Icon name="save" size={16} />
              Update
            </Button>
          </div>
          <div class="setting-status">
            {#if connectionStatus === 'connected'}
              <div class="status-indicator status-success">
                <Icon name="check" size={14} />
                Connected to backend
              </div>
            {:else if connectionStatus === 'error'}
              <div class="status-indicator status-error">
                <Icon name="x" size={14} />
                Cannot connect to backend
              </div>
            {:else}
              <div class="status-indicator status-unknown">
                <Icon name="info" size={14} />
                Connection status unknown
              </div>
            {/if}
          </div>
          <p class="setting-help">URL of the GUARDIAN backend API server (leave empty to use proxy in development)</p>
        </div>

        <div class="setting-group">
          <h3 class="setting-label">Theme Preference</h3>
          <div class="radio-group">
            <label class="radio-option">
              <input 
                type="radio" 
                checked={currentTheme === 'light'} 
                onchange={() => handleThemeChange('light')}
              />
              <Icon name="sun" size={16} />
              Light
            </label>
            <label class="radio-option">
              <input 
                type="radio" 
                checked={currentTheme === 'dark'} 
                onchange={() => handleThemeChange('dark')}
              />
              <Icon name="moon" size={16} />
              Dark
            </label>
            <label class="radio-option">
              <input 
                type="radio" 
                checked={currentTheme === 'auto'} 
                onchange={() => handleThemeChange('auto')}
              />
              <Icon name="monitor" size={16} />
              Auto
            </label>
          </div>
        </div>

        <div class="setting-group">
          <div class="checkbox-group">
            <label class="checkbox-option">
              <input type="checkbox" bind:checked={settings.notifications} />
              <Icon name="info" size={16} />
              Enable notifications
            </label>
            <label class="checkbox-option">
              <input type="checkbox" bind:checked={settings.autoAnalysis} />
              <Icon name="activity" size={16} />
              Auto-start analysis on upload
            </label>
            <label class="checkbox-option">
              <input type="checkbox" bind:checked={isDemoMode} onchange={toggleDemoMode} />
              <Icon name="eye" size={16} />
              Demo mode
            </label>
          </div>
        </div>

        <div class="setting-actions">
          <Button variant="error" onclick={resetSettings}>
            <Icon name="refresh" size={16} />
            Reset to Defaults
          </Button>
        </div>
      </Card>
    </section>

  </div>
</div>

<style>
  .settings-page {
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

  .settings-sections {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
  }

  .settings-section h2 {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-6);
    color: var(--color-text);
  }


  .setting-group {
    margin-bottom: var(--space-6);
  }

  .setting-group label {
    display: block;
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin-bottom: var(--space-2);
  }

  .setting-label {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin-bottom: var(--space-3);
  }

  .input-group {
    display: flex;
    gap: var(--space-2);
    align-items: center;
  }

  .input-group input {
    flex: 1;
    padding: var(--space-3) var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
  }

  .input-group input:focus {
    outline: none;
    border-color: var(--color-primary-500);
  }

  .setting-help {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin-top: var(--space-2);
    margin-bottom: 0;
  }

  .setting-status {
    margin-top: var(--space-2);
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
  }

  .status-success {
    color: var(--color-success-700);
    background: var(--color-success-50);
    border: 1px solid var(--color-success-200);
  }

  .status-error {
    color: var(--color-error-700);
    background: var(--color-error-50);
    border: 1px solid var(--color-error-200);
  }

  .status-unknown {
    color: var(--color-gray-700);
    background: var(--color-gray-50);
    border: 1px solid var(--color-gray-200);
  }

  .radio-group {
    display: flex;
    gap: var(--space-4);
    flex-wrap: wrap;
  }

  .radio-option {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    cursor: pointer;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    transition: background-color var(--transition-fast);
  }

  .radio-option:hover {
    background: var(--color-gray-50);
  }

  .checkbox-group {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .checkbox-option {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    cursor: pointer;
    padding: var(--space-2) var(--space-3);
    border-radius: var(--radius-md);
    transition: background-color var(--transition-fast);
  }

  .checkbox-option:hover {
    background: var(--color-gray-50);
  }

  .setting-actions {
    display: flex;
    gap: var(--space-3);
    margin-top: var(--space-6);
    padding-top: var(--space-6);
    border-top: 1px solid var(--color-border);
  }


  @media (max-width: 768px) {
    .radio-group {
      flex-direction: column;
    }

    .input-group {
      flex-direction: column;
      align-items: stretch;
    }

  }
</style>