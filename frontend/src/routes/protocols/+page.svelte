<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import DualInputInterface from '$lib/components/input/DualInputInterface.svelte';
  import ProtocolAnalysisResults from '$lib/components/analysis/ProtocolAnalysisResults.svelte';
  import GroundTruthReferences from '$lib/components/analysis/GroundTruthReferences.svelte';
  import { authState, toastStore } from '$lib/stores';
  import { session as sessionApi, GuardianApiError } from '$lib/services/api';
  import { requireAuthentication } from '$lib/utils/auth';
  import type { ProtocolAnalysisResult, DocumentInfo, SessionStats } from '$lib/types';

  // Svelte 5 runes for reactive state management
  let loading = $state(false);
  let sessionInitialized = $state(false);
  let initializingSession = $state(false);
  let analysisInProgress = $state(false);
  let navigationInProgress = $state(false);
  let pageInitialized = $state(false);

  // Analysis state
  let currentAnalysis = $state<ProtocolAnalysisResult | null>(null);
  let analysisError = $state<string | null>(null);
  let groundTruthDocuments = $state<DocumentInfo[]>([]);
  let sessionStats = $state<SessionStats | null>(null);

  // Input tracking
  let lastAnalyzedText = $state<string>('');
  let lastAnalyzedFile = $state<File | null>(null);

  // Derived reactive values
  const isAuthenticated = $derived(authState.authenticated);
  const user = $derived(authState.user);
  const hasGroundTruth = $derived(groundTruthDocuments.length > 0);
  const hasAnalysisResults = $derived(currentAnalysis !== null);
  const canAnalyze = $derived(sessionInitialized && !analysisInProgress);

  // Handle initial page load
  onMount(() => {
    if (pageInitialized) return;
    pageInitialized = true;
    
    setTimeout(async () => {
      try {
        console.log('Protocol Analysis page: Checking authentication state...');
        
        // Wait for auth to complete if still loading
        if (authState.loading) {
          console.log('Protocol Analysis page: Authentication still loading, waiting...');
          
          let attempts = 0;
          while (attempts < 20) {
            await new Promise(resolve => setTimeout(resolve, 100));
            if (!authState.loading) break;
            attempts++;
          }
        }
        
        if (authState.authenticated) {
          console.log('Protocol Analysis page: Authenticated, initializing session');
          await initializeSession();
          await loadGroundTruthStatus();
        } else if (!navigationInProgress) {
          console.log('Protocol Analysis page: Not authenticated, redirecting to login');
          navigationInProgress = true;
          goto('/login?redirect=/protocols');
        }
      } catch (error) {
        console.error('Protocol Analysis page initialization error:', error);
      }
    }, 0);
  });

  async function initializeSession() {
    if (sessionInitialized || initializingSession) return;
    
    try {
      initializingSession = true;
      console.log('Initializing session for protocol analysis...');
      
      const response = await sessionApi.initialize();
      
      if (response.success) {
        sessionInitialized = true;
        console.log('Session initialized successfully:', response.data);
        toastStore.success('Session Ready', 'Ready to analyze protocols against your ground truth library');
      } else {
        throw new Error('Failed to initialize session');
      }
    } catch (error) {
      console.error('Session initialization error:', error);
      if (error instanceof GuardianApiError) {
        toastStore.error('Session Error', error.message);
      } else {
        toastStore.error('Session Error', 'Failed to initialize analysis session. Please refresh the page.');
      }
    } finally {
      initializingSession = false;
    }
  }

  async function loadGroundTruthStatus() {
    if (!isAuthenticated) return;
    
    try {
      loading = true;
      
      // Load session stats to check ground truth availability
      const statsResponse = await sessionApi.getStats();
      if (statsResponse.success && statsResponse.data) {
        sessionStats = statsResponse.data;
        console.log('Protocol analysis session stats:', statsResponse.data);
      }

      // Load ground truth documents for reference
      const driveResponse = await sessionApi.listDriveFiles('document');
      if (driveResponse.success && driveResponse.data) {
        // TODO: Filter for ground truth documents only when backend supports it
        groundTruthDocuments = driveResponse.data.files || [];
        console.log('Available ground truth documents:', groundTruthDocuments.length);
        
        if (groundTruthDocuments.length === 0) {
          toastStore.info('No Ground Truth', 'Upload ground truth documents first to enable comprehensive compliance analysis');
        }
      }
      
    } catch (error) {
      console.error('Error loading ground truth status:', error);
      if (error instanceof GuardianApiError) {
        toastStore.error('Failed to Load Ground Truth', error.message);
      } else {
        toastStore.error('Failed to Load Ground Truth', 'Could not check ground truth document availability');
      }
    } finally {
      loading = false;
    }
  }

  async function handleTextAnalysis(event: CustomEvent<{ text: string, options: any }>) {
    if (!isAuthenticated || !sessionInitialized) {
      toastStore.error('Session Error', 'Please ensure session is initialized');
      return;
    }

    const { text, options } = event.detail;
    
    // Avoid duplicate analysis
    if (text === lastAnalyzedText && !analysisError) {
      console.log('Skipping duplicate text analysis');
      return;
    }

    try {
      analysisInProgress = true;
      analysisError = null;
      currentAnalysis = null;
      lastAnalyzedText = text;
      
      console.log('Analyzing protocol text against ground truth library...');
      toastStore.info('Analysis Started', 'Analyzing protocol against your ground truth library');
      
      const analysisRequest = {
        protocol_text: text,
        analysis_options: {
          include_compliance_check: options.includeCompliance ?? true,
          include_terminology_review: options.includeTerminology ?? true,
          include_missing_elements: options.includeMissingElements ?? true,
          ground_truth_only: true // Analyze against ground truth documents only
        }
      };

      const response = await sessionApi.analyzeProtocol(analysisRequest);
      
      if (response.success && response.data) {
        currentAnalysis = response.data;
        toastStore.success('Analysis Complete', 'Protocol analysis completed successfully');
        console.log('Protocol analysis results:', response.data);
      } else {
        throw new Error('Analysis failed - no results returned');
      }
      
    } catch (error) {
      console.error('Protocol text analysis error:', error);
      analysisError = error instanceof GuardianApiError ? error.message : 'Analysis failed unexpectedly';
      toastStore.error('Analysis Failed', analysisError);
    } finally {
      analysisInProgress = false;
    }
  }

  async function handleFileAnalysis(event: CustomEvent<{ files: File[], options: any }>) {
    if (!isAuthenticated || !sessionInitialized) {
      toastStore.error('Session Error', 'Please ensure session is initialized');
      return;
    }

    const { files, options } = event.detail;
    const file = files[0]; // Handle single file for now
    
    // Avoid duplicate analysis
    if (file === lastAnalyzedFile && !analysisError) {
      console.log('Skipping duplicate file analysis');
      return;
    }

    try {
      analysisInProgress = true;
      analysisError = null;
      currentAnalysis = null;
      lastAnalyzedFile = file;
      
      console.log(`Uploading and analyzing protocol file: ${file.name}`);
      toastStore.info('Upload Started', `Processing ${file.name} for analysis`);
      
      // Upload file first
      const uploadResponse = await sessionApi.uploadDocuments([file]);
      
      if (uploadResponse.success) {
        toastStore.success('Upload Complete', 'File uploaded, starting analysis...');
        
        // TODO: Implement file-based analysis once backend supports it
        // For now, we'll show a placeholder message
        toastStore.info('Analysis Processing', 'File analysis will be available soon. Use text input for immediate analysis.');
      }
      
    } catch (error) {
      console.error('Protocol file analysis error:', error);
      analysisError = error instanceof GuardianApiError ? error.message : 'File analysis failed unexpectedly';
      toastStore.error('Analysis Failed', analysisError);
    } finally {
      analysisInProgress = false;
    }
  }

  function handleAnalysisError(event: CustomEvent<{ message: string }>) {
    const { message } = event.detail;
    analysisError = message;
    toastStore.error('Analysis Error', message);
  }

  function clearAnalysis() {
    currentAnalysis = null;
    analysisError = null;
    lastAnalyzedText = '';
    lastAnalyzedFile = null;
  }

  function navigateToGroundTruth() {
    goto('/ground-truth');
  }

  async function refreshGroundTruth() {
    await loadGroundTruthStatus();
    toastStore.success('Refreshed', 'Ground truth status updated');
  }

  function generateReport() {
    if (!currentAnalysis) return;
    
    // TODO: Implement report generation
    toastStore.info('Report Generation', 'Report generation will be available soon');
    console.log('Generating report for analysis:', currentAnalysis);
  }
</script>

<svelte:head>
  <title>Protocol Analysis - GUARDIAN</title>
</svelte:head>

<div class="protocols-page">
  <div class="page-header">
    <div class="header-content">
      <h1>
        <Icon name="analysis" size={32} color="var(--color-primary-600)" />
        Protocol Analysis
      </h1>
      {#if isAuthenticated && user}
        <p>Welcome back, {user.name || user.email}! Analyze your pharmaceutical protocols against your ground truth library for comprehensive compliance insights.</p>
      {:else}
        <p>Upload protocol documents or paste text directly for AI-powered compliance analysis against regulatory standards and compliance guidelines.</p>
      {/if}
    </div>
    
    <div class="header-actions">
      <Button variant="secondary" onclick={navigateToGroundTruth}>
        <Icon name="book-open" size={16} />
        Manage Ground Truth
      </Button>
    </div>
  </div>

  <!-- Ground Truth Status Card -->
  {#if isAuthenticated && sessionInitialized}
    <Card>
      <div class="ground-truth-status">
        <div class="status-header">
          <Icon name="shield" size={20} color="var(--color-primary-600)" />
          <h3>Ground Truth Library Status</h3>
          <Button variant="secondary" size="sm" onclick={refreshGroundTruth} disabled={loading}>
            <Icon name="refresh" size={14} class={loading ? "animate-spin" : ""} />
            Refresh
          </Button>
        </div>
        
        <div class="status-content">
          {#if hasGroundTruth}
            <div class="status-success">
              <Icon name="check" size={16} color="var(--color-success-600)" />
              <span class="status-text">
                {groundTruthDocuments.length} ground truth document{groundTruthDocuments.length === 1 ? '' : 's'} available
              </span>
              {#if sessionStats}
                <div class="status-details">
                  <span>{sessionStats.total_chunks} text sections indexed</span>
                  <span>{sessionStats.vector_count} vectors ready for analysis</span>
                </div>
              {/if}
            </div>
          {:else}
            <div class="status-warning">
              <Icon name="warning" size={16} color="var(--color-warning-600)" />
              <span class="status-text">No ground truth documents available</span>
              <Button variant="primary" size="sm" onclick={navigateToGroundTruth}>
                <Icon name="plus" size={14} />
                Upload Ground Truth
              </Button>
            </div>
          {/if}
        </div>
      </div>
    </Card>
  {/if}

  <!-- Main Analysis Interface -->
  <section class="analysis-section">
    <Card>
      {#if isAuthenticated}
        {#if initializingSession}
          <div class="session-initializing">
            <Icon name="loading" size={48} color="var(--color-primary-600)" class="animate-spin" />
            <h3>Initializing Analysis Session</h3>
            <p>Setting up your secure protocol analysis workspace...</p>
          </div>
        {:else if sessionInitialized}
          <DualInputInterface
            disabled={!canAnalyze}
            {analysisInProgress}
            hasGroundTruth={hasGroundTruth}
            on:textAnalysis={handleTextAnalysis}
            on:fileAnalysis={handleFileAnalysis}
            on:error={handleAnalysisError}
          />
        {:else}
          <div class="session-error">
            <Icon name="error" size={48} color="var(--color-error-600)" />
            <h3>Session Initialization Failed</h3>
            <p>Unable to initialize analysis session. Please refresh the page and try again.</p>
            <Button variant="primary" onclick={() => window.location.reload()}>
              <Icon name="refresh" size={16} />
              Refresh Page
            </Button>
          </div>
        {/if}
      {:else}
        <div class="auth-required">
          <Icon name="lock" size={48} color="var(--color-gray-400)" />
          <h3>Authentication Required</h3>
          <p>Please sign in to analyze your pharmaceutical protocols against regulatory standards.</p>
          <Button variant="primary" onclick={() => {
            if (!navigationInProgress) {
              navigationInProgress = true;
              goto('/login?redirect=/protocols');
            }
          }}>
            <Icon name="login" size={16} />
            Sign In to Continue
          </Button>
        </div>
      {/if}
    </Card>
  </section>

  <!-- Analysis Results Section -->
  {#if hasAnalysisResults || analysisError}
    <section class="results-section">
      {#if analysisError}
        <Card>
          <div class="analysis-error">
            <div class="error-header">
              <Icon name="error" size={24} color="var(--color-error-600)" />
              <h3>Analysis Failed</h3>
            </div>
            <p class="error-message">{analysisError}</p>
            <div class="error-actions">
              <Button variant="primary" onclick={clearAnalysis}>
                <Icon name="refresh" size={16} />
                Try Again
              </Button>
              <Button variant="secondary" onclick={navigateToGroundTruth}>
                <Icon name="book-open" size={16} />
                Check Ground Truth
              </Button>
            </div>
          </div>
        </Card>
      {/if}

      {#if currentAnalysis}
        <div class="results-layout">
          <!-- Main Analysis Results -->
          <div class="main-results">
            <ProtocolAnalysisResults 
              analysis={currentAnalysis}
              groundTruthDocuments={groundTruthDocuments}
              on:generateReport={generateReport}
              on:clearAnalysis={clearAnalysis}
            />
          </div>
          
          <!-- Ground Truth References Sidebar -->
          {#if currentAnalysis.similar_sections && currentAnalysis.similar_sections.length > 0}
            <div class="references-sidebar">
              <GroundTruthReferences 
                similarSections={currentAnalysis.similar_sections}
                groundTruthDocuments={groundTruthDocuments}
              />
            </div>
          {/if}
        </div>
      {/if}
    </section>
  {/if}

  <!-- Information Section -->
  <section class="info-section">
    <Card>
      <div class="info-content">
        <h3>
          <Icon name="info" size={20} />
          Protocol Analysis Features
        </h3>
        <div class="info-grid">
          <div class="info-item">
            <Icon name="edit" size={24} color="var(--color-primary-600)" />
            <div>
              <h4>Text Input Analysis</h4>
              <p>Paste protocol text directly for immediate analysis with real-time validation and formatting suggestions.</p>
            </div>
          </div>
          <div class="info-item">
            <Icon name="upload" size={24} color="var(--color-secondary-600)" />
            <div>
              <h4>File Upload Processing</h4>
              <p>Upload PDF, DOCX, or TXT files for automated text extraction and comprehensive protocol analysis.</p>
            </div>
          </div>
          <div class="info-item">
            <Icon name="search" size={24} color="var(--color-warning-600)" />
            <div>
              <h4>Ground Truth Matching</h4>
              <p>Advanced AI comparison against your regulatory standards and compliance reference library.</p>
            </div>
          </div>
          <div class="info-item">
            <Icon name="reports" size={24} color="var(--color-success-600)" />
            <div>
              <h4>Detailed Reporting</h4>
              <p>Generate comprehensive compliance reports with ground truth references, findings, and recommendations.</p>
            </div>
          </div>
        </div>
      </div>
    </Card>
  </section>
</div>

<style>
  .protocols-page {
    display: flex;
    flex-direction: column;
    gap: var(--space-8);
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-6);
    margin-bottom: var(--space-4);
  }

  .header-content {
    flex: 1;
  }

  .header-content h1 {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--space-4);
    color: var(--color-text);
  }

  .header-content p {
    font-size: var(--font-size-lg);
    color: var(--color-text-secondary);
    max-width: var(--max-width-2xl);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }

  .header-actions {
    flex-shrink: 0;
  }

  .ground-truth-status {
    padding: var(--space-4);
  }

  .status-header {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }

  .status-header h3 {
    flex: 1;
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .status-content {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .status-success,
  .status-warning {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    border-radius: var(--radius-md);
    flex-wrap: wrap;
  }

  .status-success {
    background: var(--color-success-50);
    border: 1px solid var(--color-success-200);
  }

  .status-warning {
    background: var(--color-warning-50);
    border: 1px solid var(--color-warning-200);
  }

  .status-text {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    flex: 1;
  }

  .status-details {
    display: flex;
    gap: var(--space-4);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    width: 100%;
    margin-top: var(--space-2);
  }

  .session-initializing,
  .session-error,
  .auth-required {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-8);
    text-align: center;
    min-height: 300px;
    justify-content: center;
  }

  .session-initializing h3,
  .session-error h3,
  .auth-required h3 {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .session-initializing p,
  .session-error p,
  .auth-required p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
    max-width: 400px;
  }

  .results-layout {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: var(--space-6);
    align-items: start;
  }

  .main-results {
    min-width: 0;
  }

  .references-sidebar {
    position: sticky;
    top: var(--space-4);
  }

  .analysis-error {
    padding: var(--space-6);
    text-align: center;
  }

  .error-header {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }

  .error-header h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-error-700);
  }

  .error-message {
    color: var(--color-error-600);
    margin: 0 0 var(--space-6) 0;
    line-height: var(--line-height-relaxed);
  }

  .error-actions {
    display: flex;
    gap: var(--space-3);
    justify-content: center;
    flex-wrap: wrap;
  }

  .info-section {
    margin-top: var(--space-8);
  }

  .info-content {
    padding: var(--space-6);
  }

  .info-content h3 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-6) 0;
    color: var(--color-text);
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--space-6);
  }

  .info-item {
    display: flex;
    gap: var(--space-3);
    align-items: flex-start;
  }

  .info-item h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-medium);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .info-item p {
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  /* Loading animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 1024px) {
    .results-layout {
      grid-template-columns: 1fr;
      gap: var(--space-4);
    }

    .references-sidebar {
      position: static;
    }
  }

  @media (max-width: 768px) {
    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-4);
    }

    .header-content h1 {
      font-size: var(--font-size-2xl);
      flex-direction: column;
      gap: var(--space-2);
      text-align: center;
    }

    .status-details {
      flex-direction: column;
      gap: var(--space-1);
    }

    .info-grid {
      grid-template-columns: 1fr;
    }

    .error-actions {
      flex-direction: column;
      width: 100%;
    }
  }
</style>