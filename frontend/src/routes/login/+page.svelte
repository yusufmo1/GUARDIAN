<script lang="ts">
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { authState, authError } from '$lib/stores';
  import GoogleSignIn from '$lib/components/auth/GoogleSignIn.svelte';
  import Card from '$lib/components/common/Card.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  
  // Convert reactive statements to Svelte 5 $derived
  // Access reactive authentication state directly
  const authenticated = $derived(authState.authenticated);
  const error = authError;
  
  // Navigation guard to prevent infinite loops
  let hasRedirected = $state(false);
  
  // Fix reactive navigation loop - add guard to prevent multiple redirects
  $effect(() => {
    if (!browser || hasRedirected) return;
    if (authenticated) {
      hasRedirected = true;
      const redirectUrl = $page.url.searchParams.get('redirect') || '/';
      console.log('Login page: User authenticated, redirecting to:', redirectUrl);
      goto(redirectUrl);
    }
  });
</script>

<svelte:head>
  <title>Sign In - GUARDIAN</title>
  <meta name="description" content="Sign in to GUARDIAN pharmaceutical compliance analysis platform" />
</svelte:head>

<div class="login-page">
  <div class="login-container">
    <!-- Header -->
    <div class="login-header">
      <div class="logo-section">
        <Icon name="shield" size={48} class="logo-icon" />
        <h1 class="app-title">GUARDIAN</h1>
        <p class="app-subtitle">Pharmaceutical Compliance Analysis</p>
      </div>
    </div>
    
    <!-- Login Card -->
    <Card>
      <div class="login-content">
        <div class="welcome-section">
          <h2 class="welcome-title">Welcome Back</h2>
          <p class="welcome-text">
            Sign in to access your pharmaceutical compliance analysis dashboard
          </p>
        </div>
        
        <!-- Google Sign-In -->
        <div class="signin-section">
          <GoogleSignIn 
            variant="primary" 
            size="lg" 
            fullWidth={true}
            customText="Sign in with Google"
          />
          
          {#if error}
            <div class="error-message">
              <Icon name="error" size={16} />
              <span>{error}</span>
            </div>
          {/if}
        </div>
        
        <!-- Features -->
        <div class="features-section">
          <h3 class="features-title">What you'll get access to:</h3>
          <ul class="features-list">
            <li class="feature-item">
              <Icon name="analysis" size={16} />
              <span>AI-powered protocol compliance analysis</span>
            </li>
            <li class="feature-item">
              <Icon name="file-text" size={16} />
              <span>Document processing and vector search</span>
            </li>
            <li class="feature-item">
              <Icon name="reports" size={16} />
              <span>Professional compliance reports</span>
            </li>
            <li class="feature-item">
              <Icon name="chat" size={16} />
              <span>Interactive analysis chat</span>
            </li>
            <li class="feature-item">
              <Icon name="shield" size={16} />
              <span>Secure Google Drive integration</span>
            </li>
          </ul>
        </div>
      </div>
    </Card>
    
    <!-- Footer -->
    <div class="login-footer">
      <p class="footer-text">
        By signing in, you agree to our 
        <a href="/terms" class="footer-link">Terms of Service</a> and 
        <a href="/privacy" class="footer-link">Privacy Policy</a>
      </p>
      <p class="footer-info">
        Powered by Queen Mary University of London
      </p>
    </div>
  </div>
</div>

<style>
  .login-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--color-primary-50) 0%, var(--color-blue-50) 100%);
    padding: var(--space-6);
  }

  .login-container {
    width: 100%;
    max-width: 420px;
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .login-header {
    text-align: center;
    margin-bottom: var(--space-4);
  }

  .logo-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-2);
  }

  :global(.logo-icon) {
    color: var(--color-primary-600);
  }

  .app-title {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-primary-600);
    margin: 0;
    letter-spacing: -0.02em;
  }

  .app-subtitle {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin: 0;
    font-weight: var(--font-weight-medium);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .login-content {
    padding: var(--space-8) var(--space-6);
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }

  .welcome-section {
    text-align: center;
  }

  .welcome-title {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-text);
    margin: 0 0 var(--space-2) 0;
  }

  .welcome-text {
    font-size: var(--font-size-base);
    color: var(--color-text-muted);
    margin: 0;
    line-height: 1.5;
  }

  .signin-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-3);
    background: var(--color-red-50);
    border: 1px solid var(--color-red-200);
    border-radius: var(--radius-md);
    color: var(--color-red-600);
    font-size: var(--font-size-sm);
  }

  .features-section {
    margin-top: var(--space-4);
    padding-top: var(--space-4);
    border-top: 1px solid var(--color-border);
  }

  .features-title {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0 0 var(--space-3) 0;
  }

  .features-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .feature-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
  }

  .feature-item :global(svg) {
    color: var(--color-primary-600);
    flex-shrink: 0;
  }

  .login-footer {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .footer-text {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin: 0;
    line-height: 1.4;
  }

  .footer-link {
    color: var(--color-primary-600);
    text-decoration: none;
    font-weight: var(--font-weight-medium);
  }

  .footer-link:hover {
    text-decoration: underline;
  }

  .footer-info {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin: 0;
    font-weight: var(--font-weight-medium);
  }

  @media (max-width: 480px) {
    .login-page {
      padding: var(--space-4);
    }
    
    .login-content {
      padding: var(--space-6) var(--space-4);
    }
    
    .app-title {
      font-size: var(--font-size-2xl);
    }
  }
</style>