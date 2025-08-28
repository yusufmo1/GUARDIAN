<script lang="ts">
  import { browser } from '$app/environment';
  import Button from '$lib/components/common/Button.svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import GoogleSignIn from '$lib/components/auth/GoogleSignIn.svelte';
  import { goto } from '$app/navigation';
  import { health as healthApi, session as sessionApi, auth as authApi } from '$lib/services/api';
  import { authState } from '$lib/stores';
  import { requireAuthentication } from '$lib/utils/auth';
  import type { HealthResponse } from '$lib/services/api';
  
  // Convert local state to Svelte 5 runes
  let healthStatus = $state<HealthResponse | null>(null);
  let sessionStats = $state<any>(null);
  let authStatus = $state<any>(null);
  let documentStats = $state<any>(null);
  let statusLoading = $state(false);
  
  // Convert reactive statements to Svelte 5 $derived
  // Access reactive authentication state directly
  const authenticated = $derived(authState.authenticated);
  const user = $derived(authState.user);

  // Convert onMount to $effect
  $effect(() => {
    if (!browser) return;
    loadSystemStatus();
  });

  async function loadSystemStatus() {
    try {
      statusLoading = true;

      // Load health status (non-blocking)
      try {
        const healthResponse = await healthApi.check();
        healthStatus = healthResponse.data || null;
      } catch (err) {
        console.warn('Health check failed:', err);
      }

      // Load authentication status (non-blocking)
      if (authenticated) {
        try {
          const authHealthResponse = await authApi.healthCheck();
          authStatus = authHealthResponse.data || null;
        } catch (err) {
          console.warn('Auth health check failed:', err);
        }

        // Load session statistics (non-blocking)
        try {
          const sessionStatsResponse = await sessionApi.getStats();
          sessionStats = sessionStatsResponse.data || null;
        } catch (err) {
          console.warn('Session stats failed:', err);
        }
      } else {
        // Clear auth-specific data when not authenticated
        authStatus = null;
        sessionStats = null;
        documentStats = null;
      }
    } finally {
      statusLoading = false;
    }
  }

  function startAnalysis() {
    if (authenticated) {
      goto('/protocols');
    } else {
      goto('/login?redirect=/protocols');
    }
  }
  
  function viewReports() {
    console.log('Navigating to sample reports...');
    goto('/sample-reports');
  }

  function navigateToSettings() {
    goto('/settings');
  }

  function getStatusColor(status?: string): string {
    switch (status) {
      case 'healthy': return 'var(--color-success-600)';
      case 'degraded': return 'var(--color-warning-600)';
      case 'unhealthy': return 'var(--color-error-600)';
      default: return 'var(--color-gray-600)';
    }
  }

  function getStatusIcon(status?: string): string {
    switch (status) {
      case 'healthy': return 'check';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'info';
    }
  }
</script>

<svelte:head>
  <title>GUARDIAN - Guided Universal Adherence & Regulatory Document Intelligence Network</title>
</svelte:head>

<div class="dashboard">
  <div class="hero">
    <div class="hero-content">
      <h1 class="hero-title">
        <Icon name="shield" size={48} color="var(--color-primary-600)" />
        <div class="title-content">
          <span class="title-main">GUARDIAN</span>
          <span class="title-subtitle">Guided Universal Adherence & Regulatory Document Intelligence Network</span>
        </div>
      </h1>
      
      {#if authenticated && user}
        <div class="welcome-section">
          <h2 class="welcome-title">Welcome back, {user.name || user.email}!</h2>
          <p class="welcome-description">
            Your secure pharmaceutical compliance analysis workspace is ready. 
            Continue analyzing protocols or start a new session.
          </p>
        </div>
      {:else}
        <p class="hero-description">
          Automated pharmaceutical protocol compliance analysis against global regulatory standards. 
          Upload your protocols and get comprehensive compliance reports with AI-powered insights.
        </p>
      {/if}
      <div class="hero-actions">
        {#if authenticated}
          <Button variant="primary" size="lg" onclick={() => goto('/ground-truth')}>
            <Icon name="book-open" size={20} />
            Manage Ground Truth
          </Button>
          <Button variant="primary" size="lg" onclick={() => goto('/protocols')}>
            <Icon name="analysis" size={20} />
            Analyze Protocols
          </Button>
          <Button variant="secondary" size="lg" onclick={viewReports}>
            <Icon name="reports" size={20} />
            View Reports
          </Button>
        {:else}
          <Button variant="primary" size="lg" onclick={startAnalysis}>
            <Icon name="login" size={20} />
            Sign In to Start
          </Button>
          <Button variant="secondary" size="lg" onclick={viewReports}>
            View Sample Reports
          </Button>
        {/if}
      </div>
    </div>
  </div>

  <div class="features">
    <div class="section-header">
      <h2>Key Features</h2>
      <p>Comprehensive pharmaceutical compliance analysis powered by AI</p>
    </div>
    
    <div class="features-grid">
      <Card>
        <div class="feature">
          <div class="feature-icon">
            <Icon name="book-open" size={32} color="var(--color-primary-600)" />
          </div>
          <h3>Ground Truth Library</h3>
          <p>
            Upload and manage regulatory standards, analytical methods, 
            and compliance documents as authoritative reference materials.
          </p>
        </div>
      </Card>
      
      <Card>
        <div class="feature">
          <div class="feature-icon">
            <Icon name="analysis" size={32} color="var(--color-secondary-600)" />
          </div>
          <h3>Smart Protocol Analysis</h3>
          <p>
            Analyze pharmaceutical protocols against your ground truth library 
            with AI-powered compliance scoring and detailed gap identification.
          </p>
        </div>
      </Card>
      
      <Card>
        <div class="feature">
          <div class="feature-icon">
            <Icon name="shield" size={32} color="var(--color-warning-600)" />
          </div>
          <h3>Privacy-First Architecture</h3>
          <p>
            All documents stored securely in your personal Google Drive with 
            encrypted processing and zero permanent server storage.
          </p>
        </div>
      </Card>
      
      <Card>
        <div class="feature">
          <div class="feature-icon">
            <Icon name="reports" size={32} color="var(--color-success-600)" />
          </div>
          <h3>Comprehensive Reports</h3>
          <p>
            Generate detailed PDF reports with compliance scores, ground truth references, 
            findings, and visual analytics for regulatory review.
          </p>
        </div>
      </Card>
    </div>
  </div>

  <div class="getting-started">
    <div class="section-header">
      <h2>Getting Started</h2>
      <p>Follow these simple steps to analyze your pharmaceutical protocols</p>
    </div>
    
    <div class="steps">
      <div class="step">
        <div class="step-number">1</div>
        <div class="step-content">
          <h3>Build Ground Truth Library</h3>
          <p>Upload regulatory standards and compliance documents as reference materials</p>
        </div>
      </div>
      
      <div class="step">
        <div class="step-number">2</div>
        <div class="step-content">
          <h3>Upload Your Protocol</h3>
          <p>Upload your pharmaceutical protocol or paste text directly for analysis</p>
        </div>
      </div>
      
      <div class="step">
        <div class="step-number">3</div>
        <div class="step-content">
          <h3>AI-Powered Analysis</h3>
          <p>Our AI compares your protocol against your ground truth library for compliance gaps</p>
        </div>
      </div>
      
      <div class="step">
        <div class="step-number">4</div>
        <div class="step-content">
          <h3>Review & Export</h3>
          <p>Get detailed compliance scores with ground truth references and export comprehensive reports</p>
        </div>
      </div>
    </div>
  </div>

  <!-- System Status Section -->
  <div class="system-status">
    <div class="section-header">
      <h2>System Status</h2>
      <p>Backend integration and system health</p>
    </div>

    <div class="status-grid">
      <Card>
        <div class="status-item">
          <div class="status-header">
            <Icon 
              name={getStatusIcon(healthStatus?.status)} 
              size={24} 
              color={getStatusColor(healthStatus?.status)}
            />
            <h3>Backend Connection</h3>
            {#if !statusLoading}
              <Button 
                variant="secondary" 
                size="sm" 
                onclick={loadSystemStatus}
              >
                <Icon name="refresh" size={14} />
                Refresh
              </Button>
            {/if}
          </div>
          <div class="status-content">
            {#if statusLoading}
              <div class="status-loading">
                <Icon name="loading" size={16} class="spin" />
                Checking status...
              </div>
            {:else if healthStatus}
              <div class="status-info">
                <div class="status-badge" style="color: {getStatusColor(healthStatus.status)}">
                  {healthStatus.status || 'Unknown'}
                </div>
                <div class="status-details">
                  <span>Service: {healthStatus.service}</span>
                  <span>Version: {healthStatus.version || 'Unknown'}</span>
                </div>
              </div>
            {:else}
              <div class="status-error">
                <Icon name="error" size={16} color="var(--color-error-600)" />
                Cannot connect to backend
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onclick={navigateToSettings}
                >
                  <Icon name="settings" size={14} />
                  Check Settings
                </Button>
              </div>
            {/if}
          </div>
        </div>
      </Card>

      <Card>
        <div class="status-item">
          <div class="status-header">
            {#if authenticated}
              <Icon name="user" size={24} color="var(--color-primary-600)" />
              <h3>Session Statistics</h3>
            {:else}
              <Icon name="info" size={24} color="var(--color-gray-600)" />
              <h3>Authentication Required</h3>
            {/if}
          </div>
          <div class="status-content">
            {#if authenticated}
              {#if statusLoading}
                <div class="status-loading">
                  <Icon name="loading" size={16} class="spin" />
                  Loading session stats...
                </div>
              {:else if sessionStats}
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-value">{sessionStats.total_documents || 0}</span>
                    <span class="stat-label">Your Documents</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{sessionStats.processed_documents || 0}</span>
                    <span class="stat-label">Processed</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{sessionStats.active_sessions || 0}</span>
                    <span class="stat-label">Active Sessions</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{sessionStats.analyses_count || 0}</span>
                    <span class="stat-label">Analyses</span>
                  </div>
                </div>
              {:else}
                <div class="status-info">
                  <Icon name="info" size={16} color="var(--color-gray-600)" />
                  No session data yet - start your first analysis!
                </div>
              {/if}
            {:else}
              <div class="auth-required">
                <Icon name="lock" size={16} color="var(--color-gray-600)" />
                <span>Sign in to view your personal statistics and session data</span>
                <GoogleSignIn variant="secondary" size="sm" customText="Sign In" />
              </div>
            {/if}
          </div>
        </div>
      </Card>

      <Card>
        <div class="status-item">
          <div class="status-header">
            <Icon name="activity" size={24} color="var(--color-secondary-600)" />
            <h3>Integration</h3>
          </div>
          <div class="status-content">
            <div class="integration-info">
              <div class="integration-item">
                <Icon name="analysis" size={16} />
                <span>Protocol Analysis API</span>
                <Icon 
                  name={healthStatus?.status === 'healthy' ? 'check' : 'x'} 
                  size={16} 
                  color={healthStatus?.status === 'healthy' ? 'var(--color-success-600)' : 'var(--color-error-600)'}
                />
              </div>
              <div class="integration-item">
                <Icon name="search" size={16} />
                <span>Vector Search</span>
                <Icon 
                  name={healthStatus?.status === 'healthy' ? 'check' : 'x'} 
                  size={16} 
                  color={healthStatus?.status === 'healthy' ? 'var(--color-success-600)' : 'var(--color-error-600)'}
                />
              </div>
              <div class="integration-item">
                <Icon name="upload" size={16} />
                <span>Document Upload</span>
                <Icon 
                  name={healthStatus?.status === 'healthy' ? 'check' : 'x'} 
                  size={16} 
                  color={healthStatus?.status === 'healthy' ? 'var(--color-success-600)' : 'var(--color-error-600)'}
                />
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</div>

<style>
  .dashboard {
    display: flex;
    flex-direction: column;
    gap: var(--space-12);
  }

  .hero {
    text-align: center;
    padding: var(--space-12) 0;
    background: linear-gradient(135deg, var(--color-primary-50) 0%, var(--color-secondary-50) 100%);
    border-radius: var(--radius-2xl);
    margin-bottom: var(--space-8);
  }

  .hero-content {
    max-width: var(--max-width-3xl);
    margin: 0 auto;
    padding: 0 var(--space-6);
  }

  .hero-title {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-4);
    margin-bottom: var(--space-6);
    color: var(--color-text);
  }

  .title-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-2);
  }

  .title-main {
    font-size: var(--font-size-4xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-700);
    letter-spacing: 0.05em;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .title-subtitle {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text-secondary);
    text-align: center;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.8;
    max-width: 400px;
    line-height: var(--line-height-tight);
  }

  .hero-description {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin-bottom: var(--space-8);
    max-width: var(--max-width-2xl);
    margin-left: auto;
    margin-right: auto;
  }

  .hero-actions {
    display: flex;
    gap: var(--space-4);
    justify-content: center;
    flex-wrap: wrap;
  }

  .section-header {
    text-align: center;
    margin-bottom: var(--space-8);
  }

  .section-header h2 {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-4);
  }

  .section-header p {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    max-width: var(--max-width-2xl);
    margin: 0 auto;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-6);
  }

  .feature {
    text-align: center;
  }

  .feature-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    background: var(--color-gray-50);
    border-radius: var(--radius-xl);
    margin: 0 auto var(--space-4);
  }

  .feature h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-3);
  }

  .feature p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
  }

  .steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: var(--space-8);
    max-width: var(--max-width-5xl);
    margin: 0 auto;
  }

  .step {
    display: flex;
    align-items: flex-start;
    gap: var(--space-4);
    text-align: left;
  }

  .step-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: var(--color-primary-500);
    color: white;
    border-radius: var(--radius-full);
    font-weight: var(--font-weight-bold);
    font-size: var(--font-size-lg);
    flex-shrink: 0;
  }

  .step-content h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin-bottom: var(--space-2);
  }

  .step-content p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  /* System Status Styles */
  .system-status {
    margin: var(--space-8) 0;
  }

  .status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: var(--space-6);
  }

  .status-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .status-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .status-header h3 {
    flex: 1;
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .status-content {
    flex: 1;
  }

  .status-loading {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
  }

  .status-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .status-badge {
    font-weight: var(--font-weight-medium);
    text-transform: capitalize;
    font-size: var(--font-size-base);
  }

  .status-details {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
  }

  .status-error {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-4);
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-3);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
  }

  .stat-value {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
  }

  .stat-label {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    text-align: center;
  }

  .integration-info {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .integration-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2) var(--space-3);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
  }

  .integration-item span {
    flex: 1;
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  /* Authentication-aware dashboard styles */
  .welcome-section {
    text-align: center;
    margin: var(--space-4) 0 var(--space-6);
  }

  .welcome-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-700);
    margin: 0 0 var(--space-3) 0;
  }

  .welcome-description {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
    max-width: var(--max-width-2xl);
    margin-left: auto;
    margin-right: auto;
  }

  .auth-required {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    text-align: center;
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
  }

  .auth-required span {
    line-height: var(--line-height-relaxed);
  }

  .status-info {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
    padding: var(--space-2);
  }

  @media (max-width: 768px) {
    .hero-title {
      flex-direction: column;
      gap: var(--space-3);
    }

    .title-main {
      font-size: var(--font-size-3xl);
    }

    .title-subtitle {
      font-size: var(--font-size-xs);
      max-width: 300px;
    }

    .hero-actions {
      flex-direction: column;
      align-items: center;
    }

    .features-grid {
      grid-template-columns: 1fr;
    }

    .steps {
      grid-template-columns: 1fr;
      gap: var(--space-6);
    }

    .step {
      flex-direction: column;
      text-align: center;
    }
  }
</style>