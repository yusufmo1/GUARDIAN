import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import type { 
  AuthState, 
  User, 
  UserSession, 
  GoogleOAuthInitiateResponse,
  GoogleOAuthCallbackRequest 
} from '$lib/types';
import { auth as authApi, SessionTokenManager } from '$lib/services/api';
import { AUTH_CONFIG } from '$lib/constants';
import { toastStore } from './toast.svelte';

// Initial authentication state
const initialAuthState = {
  authenticated: false,
  user: null as User | null,
  session: null as UserSession | null,
  loading: false,
  error: null as string | null,
  sessionToken: null as string | null
};

// Create reactive authentication state using Svelte 5 runes
// In Svelte 5, we need to export an object with $state properties, not individual $state variables
export const authState = $state({
  authenticated: false,
  user: null as User | null,
  session: null as UserSession | null,
  loading: false,
  error: null as string | null,
  sessionToken: null as string | null,
  initialized: false,
  shouldAutoRefresh: true
});

// Export getter functions for compatibility
export const isAuthenticated = () => authState.authenticated;
export const currentUser = () => authState.user;
export const currentSession = () => authState.session;
export const authLoading = () => authState.loading;
export const authError = () => authState.error;

// Export as function to avoid derived export restriction
export const hasValidSession = () => authState.authenticated && authState.sessionToken !== null;

// Note: All auth effects moved to +layout.svelte
// Store-level effects are not allowed in Svelte 5

// Authentication store interface
export const authStore = {
  // Getters for reactive access
  get authenticated(): boolean {
    return authState.authenticated;
  },
  
  get user(): User | null {
    return authState.user;
  },
  
  get session(): UserSession | null {
    return authState.session;
  },
  
  get loading(): boolean {
    return authState.loading;
  },
  
  get error(): string | null {
    return authState.error;
  },
  
  get sessionToken(): string | null {
    return authState.sessionToken;
  },
  
  // Core authentication methods
  async initialize(): Promise<void> {
    if (!browser) return;
    
    console.log('Initializing authentication store...');
    
    // Use setTimeout to break out of reactive context
    await new Promise(resolve => setTimeout(resolve, 0));
    
    authState.loading = true;
    authState.error = null;
    
    try {
      // Check if we have a stored session token
      const storedToken = SessionTokenManager.getToken();
      
      if (!storedToken) {
        console.log('No stored session token found');
        setTimeout(() => {
          authState.authenticated = false;
          authState.user = null;
          authState.session = null;
          authState.sessionToken = null;
          authState.loading = false;
        }, 0);
        return;
      }

      console.log('Found stored session token, validating...');
      
      // Validate the stored session token
      const response = await authApi.validateSession();
      
      if (response.success && response.data) {
        console.log('Session validation successful');
        
        // Load user data from localStorage if available
        const storedUserData = localStorage.getItem(AUTH_CONFIG.USER_DATA_KEY);
        const userData = storedUserData ? JSON.parse(storedUserData) : response.data.user;
        
        setTimeout(() => {
          authState.authenticated = true;
          authState.user = userData;
          authState.session = response.data.session;
          authState.sessionToken = storedToken;
          authState.error = null;
        }, 0);
        
        // Update stored user data
        localStorage.setItem(AUTH_CONFIG.USER_DATA_KEY, JSON.stringify(userData));
        
        console.log('User authenticated:', userData.email);
        
      } else {
        console.warn('Session validation failed, clearing stored data');
        await this.clearSession();
      }
      
    } catch (authError) {
      console.error('Authentication initialization failed:', authError);
      
      // Clear invalid session data
      await this.clearSession();
      
      authState.error = 'Failed to validate session';
    } finally {
      setTimeout(() => {
        authState.loading = false;
      }, 0);
    }
  },

  async initiateGoogleAuth(): Promise<void> {
    if (!browser) return;
    
    console.log('Initiating Google OAuth flow...');
    
    authState.loading = true;
    authState.error = null;
    
    try {
      const response = await authApi.initiateGoogleAuth();
      
      if (response.success && response.data) {
        console.log('OAuth URL generated, redirecting to Google...');
        
        // Store the OAuth state for validation
        sessionStorage.setItem('oauth_state', response.data.state);
        
        // Store current URL for redirect after authentication
        const currentUrl = window.location.pathname + window.location.search;
        localStorage.setItem(AUTH_CONFIG.REDIRECT_URL_KEY, currentUrl);
        
        // Redirect to Google OAuth
        window.location.href = response.data.authorization_url;
        
      } else {
        throw new Error(response.message || 'Failed to initiate OAuth');
      }
      
    } catch (authError: any) {
      console.error('Failed to initiate Google auth:', authError);
      
      authState.loading = false;
      authState.error = authError.message || 'Failed to start authentication';
      
      toastStore.error('Authentication Error', 'Failed to start Google authentication');
    }
  },

  async handleGoogleCallback(code: string, state: string): Promise<void> {
    if (!browser) return;
    
    console.log('Handling Google OAuth callback...');
    
    authState.loading = true;
    authState.error = null;
    
    try {
      // Validate OAuth state
      const storedState = sessionStorage.getItem('oauth_state');
      if (storedState !== state) {
        throw new Error('Invalid OAuth state - possible CSRF attack');
      }
      
      // Exchange authorization code for session token
      const callbackRequest: GoogleOAuthCallbackRequest = { code, state };
      const response = await authApi.handleGoogleCallback(callbackRequest);
      
      if (response.success && response.data) {
        console.log('Google OAuth callback successful');
        
        // Store session token and user data
        SessionTokenManager.setToken(response.data.session_token);
        localStorage.setItem(AUTH_CONFIG.USER_DATA_KEY, JSON.stringify(response.data.user));
        
        // Update store state
        authState.authenticated = true;
        authState.user = response.data.user;
        authState.session = response.data.session;
        authState.sessionToken = response.data.session_token;
        authState.error = null;
        
        // Clean up OAuth state
        sessionStorage.removeItem('oauth_state');
        
        console.log('User logged in:', response.data.user.email);
        
        toastStore.success('Welcome!', `Successfully signed in as ${response.data.user.email}`);
        
        // Redirect to intended destination or dashboard
        const redirectUrl = localStorage.getItem(AUTH_CONFIG.REDIRECT_URL_KEY) || '/';
        localStorage.removeItem(AUTH_CONFIG.REDIRECT_URL_KEY);
        
        // Defer navigation to break reactive chain
        queueMicrotask(() => {
          goto(redirectUrl);
        });
        
      } else {
        throw new Error(response.message || 'Authentication failed');
      }
      
    } catch (authError: any) {
      console.error('Google OAuth callback failed:', authError);
      
      // Clean up OAuth state
      sessionStorage.removeItem('oauth_state');
      
      authState.error = authError.message || 'Authentication failed';
      
      toastStore.error('Authentication Failed', authError.message || 'Failed to complete Google authentication');
      
      // Redirect to login page - defer to break reactive chain
      queueMicrotask(() => {
        goto('/login');
      });
    } finally {
      authState.loading = false;
    }
  },

  async logout(logoutSessionToken?: string): Promise<void> {
    console.log('Logging out user...');
    
    authState.loading = true;
    
    try {
      // Use provided token or current session token
      const tokenToLogout = logoutSessionToken || authState.sessionToken;
      
      // Call logout API
      await authApi.logout(tokenToLogout || undefined);
      
      console.log('Logout API call successful');
      
    } catch (logoutError) {
      console.warn('Logout API call failed (continuing with local cleanup):', logoutError);
    }
    
    // Always clear local session data regardless of API call result
    await this.clearSession();
    
    toastStore.success('Logged Out', 'You have been successfully logged out');
    
    // Redirect to login page - defer to break reactive chain
    queueMicrotask(() => {
      goto('/login');
    });
  },

  async clearSession(): Promise<void> {
    if (!browser) return;
    
    console.log('Clearing session data...');
    
    // Clear stored tokens and data
    SessionTokenManager.removeToken();
    localStorage.removeItem(AUTH_CONFIG.USER_DATA_KEY);
    localStorage.removeItem(AUTH_CONFIG.REDIRECT_URL_KEY);
    sessionStorage.removeItem('oauth_state');
    
    // Clear all user-specific stores - use setTimeout to break out of reactive context
    setTimeout(async () => {
      try {
        const [
          { documentStore },
          { analysisStore },
          { chatStore },
          { appStore }
        ] = await Promise.all([
          import('./documents'),
          import('./analysis'),
          import('./chat'),
          import('./app.svelte')
        ]);
        
        console.log('Clearing user-specific store data...');
        documentStore.clearAll();
        analysisStore.clearAll();
        chatStore.clearAll();
        appStore.reset();
      } catch (clearError) {
        console.warn('Failed to clear some stores:', clearError);
      }
    }, 0);
    
    // Reset store state - use setTimeout to break out of reactive context
    setTimeout(() => {
      authState.authenticated = false;
      authState.user = null;
      authState.session = null;
      authState.loading = false;
      authState.error = null;
      authState.sessionToken = null;
    }, 0);
    authState.shouldAutoRefresh = false;
    
    console.log('Session cleared and all user data reset');
  },

  async refreshTokens(): Promise<void> {
    console.log('Refreshing authentication tokens...');
    
    try {
      await authApi.refreshTokens();
      console.log('Tokens refreshed successfully');
      
      toastStore.success('Tokens Refreshed', 'Your session has been refreshed');
      
    } catch (refreshError: any) {
      console.error('Failed to refresh tokens:', refreshError);
      
      toastStore.error('Refresh Failed', 'Failed to refresh session tokens');
      
      // If refresh fails, logout user
      await this.logout();
    }
  },

  async updateUserData(): Promise<void> {
    if (!browser) return;
    
    console.log('Updating user data...');
    
    try {
      const response = await authApi.getCurrentUser();
      
      if (response.success && response.data) {
        // Update user data in store and localStorage
        localStorage.setItem(AUTH_CONFIG.USER_DATA_KEY, JSON.stringify(response.data));
        
        authState.user = response.data;
        
        console.log('User data updated');
      }
      
    } catch (updateError: any) {
      console.error('Failed to update user data:', updateError);
      
      // If user data fetch fails, the session might be invalid
      if (updateError.status === 401) {
        await this.logout();
      }
    }
  },

  // Utility methods
  setError(newError: string | null): void {
    authState.error = newError;
  },

  clearError(): void {
    authState.error = null;
  },

  setLoading(isLoading: boolean): void {
    authState.loading = isLoading;
  },

  // Authentication guard helper
  requireAuth(): boolean {
    if (!authState.authenticated) {
      console.log('Authentication required, redirecting to login...');
      
      if (browser) {
        // Store current URL for redirect after login
        const currentUrl = window.location.pathname + window.location.search;
        localStorage.setItem(AUTH_CONFIG.REDIRECT_URL_KEY, currentUrl);
        
        // Defer navigation to break reactive chain
        queueMicrotask(() => {
          goto('/login');
        });
      }
      
      return false;
    }
    
    return true;
  },

  // State management helpers
  getSnapshot() {
    return {
      authenticated: authState.authenticated,
      user: authState.user ? { ...authState.user } : null,
      session: authState.session ? { ...authState.session } : null,
      loading: authState.loading,
      error: authState.error,
      sessionToken: authState.sessionToken
    };
  },

  // Reset to initial state (for testing)
  reset(): void {
    authState.authenticated = false;
    authState.user = null;
    authState.session = null;
    authState.loading = false;
    authState.error = null;
    authState.sessionToken = null;
    authState.shouldAutoRefresh = true;
    authState.initialized = false;
  }
};