import { writable, derived, get } from 'svelte/store';
import type { 
  AuthState, 
  User, 
  UserSession, 
  GoogleOAuthInitiateResponse,
  GoogleOAuthCallbackRequest 
} from '$lib/types';
import { auth as authApi, SessionTokenManager } from '$lib/services/api';
import { AUTH_CONFIG } from '$lib/constants';
import { goto } from '$app/navigation';
import { toastStore } from './toast';

// Initial authentication state
const initialAuthState: AuthState = {
  authenticated: false,
  user: null,
  session: null,
  loading: false,
  error: null,
  sessionToken: null
};

// Create the main authentication store
function createAuthStore() {
  const { subscribe, set, update } = writable<AuthState>(initialAuthState);

  return {
    subscribe,
    
    // Actions
    async initialize() {
      console.log('Initializing authentication store...');
      
      update(state => ({ ...state, loading: true, error: null }));
      
      try {
        // Check if we have a stored session token
        const storedToken = SessionTokenManager.getToken();
        
        if (!storedToken) {
          console.log('No stored session token found');
          update(state => ({ 
            ...state, 
            loading: false, 
            authenticated: false,
            user: null,
            session: null,
            sessionToken: null
          }));
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
          
          update(state => ({
            ...state,
            authenticated: true,
            user: userData,
            session: response.data.session,
            sessionToken: storedToken,
            loading: false,
            error: null
          }));
          
          // Set current user in all stores for user isolation
          const { documentStore } = await import('./documents');
          const { analysisStore } = await import('./analysis');
          const { chatStore } = await import('./chat');
          
          console.log('Setting user context in all stores...');
          documentStore.setCurrentUser(userData.id);
          analysisStore.setCurrentUser(userData.id);
          chatStore.setCurrentUser(userData.id);
          
          // Update stored user data
          localStorage.setItem(AUTH_CONFIG.USER_DATA_KEY, JSON.stringify(userData));
          
          console.log('User authenticated:', userData.email);
          
        } else {
          console.warn('Session validation failed, clearing stored data');
          await this.clearSession();
        }
        
      } catch (error) {
        console.error('Authentication initialization failed:', error);
        
        // Clear invalid session data
        await this.clearSession();
        
        update(state => ({
          ...state,
          loading: false,
          error: 'Failed to validate session'
        }));
      }
    },

    async initiateGoogleAuth() {
      console.log('Initiating Google OAuth flow...');
      
      update(state => ({ ...state, loading: true, error: null }));
      
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
        
      } catch (error: any) {
        console.error('Failed to initiate Google auth:', error);
        
        update(state => ({
          ...state,
          loading: false,
          error: error.message || 'Failed to start authentication'
        }));
        
        toastStore.add({
          type: 'error',
          title: 'Authentication Error',
          message: 'Failed to start Google authentication'
        });
      }
    },

    async handleGoogleCallback(code: string, state: string) {
      console.log('Handling Google OAuth callback...');
      
      update(s => ({ ...s, loading: true, error: null }));
      
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
          update(s => ({
            ...s,
            authenticated: true,
            user: response.data.user,
            session: response.data.session,
            sessionToken: response.data.session_token,
            loading: false,
            error: null
          }));
          
          // Set current user in all stores for user isolation
          const { documentStore } = await import('./documents');
          const { analysisStore } = await import('./analysis');
          const { chatStore } = await import('./chat');
          
          console.log('Setting user context in all stores...');
          documentStore.setCurrentUser(response.data.user.id);
          analysisStore.setCurrentUser(response.data.user.id);
          chatStore.setCurrentUser(response.data.user.id);
          
          // Clean up OAuth state
          sessionStorage.removeItem('oauth_state');
          
          console.log('User logged in:', response.data.user.email);
          
          toastStore.add({
            type: 'success',
            title: 'Welcome!',
            message: `Successfully signed in as ${response.data.user.email}`
          });
          
          // Redirect to intended destination or dashboard
          const redirectUrl = localStorage.getItem(AUTH_CONFIG.REDIRECT_URL_KEY) || '/';
          localStorage.removeItem(AUTH_CONFIG.REDIRECT_URL_KEY);
          
          goto(redirectUrl);
          
        } else {
          throw new Error(response.message || 'Authentication failed');
        }
        
      } catch (error: any) {
        console.error('Google OAuth callback failed:', error);
        
        // Clean up OAuth state
        sessionStorage.removeItem('oauth_state');
        
        update(state => ({
          ...state,
          loading: false,
          error: error.message || 'Authentication failed'
        }));
        
        toastStore.add({
          type: 'error',
          title: 'Authentication Failed',
          message: error.message || 'Failed to complete Google authentication'
        });
        
        // Redirect to login page
        goto('/login');
      }
    },

    async logout(sessionToken?: string) {
      console.log('Logging out user...');
      
      update(state => ({ ...state, loading: true }));
      
      try {
        // Use provided token or current session token
        const tokenToLogout = sessionToken || get(authStore).sessionToken;
        
        // Call logout API
        await authApi.logout(tokenToLogout || undefined);
        
        console.log('Logout API call successful');
        
      } catch (error) {
        console.warn('Logout API call failed (continuing with local cleanup):', error);
      }
      
      // Always clear local session data regardless of API call result
      await this.clearSession();
      
      toastStore.add({
        type: 'success',
        title: 'Logged Out',
        message: 'You have been successfully logged out'
      });
      
      // Redirect to login page
      goto('/login');
    },

    async clearSession() {
      console.log('Clearing session data...');
      
      // Clear stored tokens and data
      SessionTokenManager.removeToken();
      localStorage.removeItem(AUTH_CONFIG.USER_DATA_KEY);
      localStorage.removeItem(AUTH_CONFIG.REDIRECT_URL_KEY);
      sessionStorage.removeItem('oauth_state');
      
      // Clear all user-specific stores
      // Import these stores dynamically to avoid circular dependencies
      const { documentStore } = await import('./documents');
      const { analysisStore } = await import('./analysis');
      const { chatStore } = await import('./chat');
      const { appStore } = await import('./app');
      
      console.log('Clearing user-specific store data...');
      documentStore.clearAll();
      analysisStore.clearAll();
      chatStore.clearAll();
      appStore.reset();
      
      // Reset store state
      update(state => ({
        ...initialAuthState,
        loading: false
      }));
      
      console.log('Session cleared and all user data reset');
    },

    async refreshTokens() {
      console.log('Refreshing authentication tokens...');
      
      try {
        await authApi.refreshTokens();
        console.log('Tokens refreshed successfully');
        
        toastStore.add({
          type: 'success',
          title: 'Tokens Refreshed',
          message: 'Your session has been refreshed'
        });
        
      } catch (error: any) {
        console.error('Failed to refresh tokens:', error);
        
        toastStore.add({
          type: 'error',
          title: 'Refresh Failed',
          message: 'Failed to refresh session tokens'
        });
        
        // If refresh fails, logout user
        await this.logout();
      }
    },

    async updateUserData() {
      console.log('Updating user data...');
      
      try {
        const response = await authApi.getCurrentUser();
        
        if (response.success && response.data) {
          // Update user data in store and localStorage
          localStorage.setItem(AUTH_CONFIG.USER_DATA_KEY, JSON.stringify(response.data));
          
          update(state => ({
            ...state,
            user: response.data
          }));
          
          console.log('User data updated');
        }
        
      } catch (error: any) {
        console.error('Failed to update user data:', error);
        
        // If user data fetch fails, the session might be invalid
        if (error.status === 401) {
          await this.logout();
        }
      }
    },

    // Utility methods
    setError(error: string | null) {
      update(state => ({ ...state, error }));
    },

    clearError() {
      update(state => ({ ...state, error: null }));
    },

    setLoading(loading: boolean) {
      update(state => ({ ...state, loading }));
    }
  };
}

// Create the store instance
export const authStore = createAuthStore();

// Derived stores for easy access to specific auth state
export const isAuthenticated = derived(
  authStore,
  $auth => $auth.authenticated
);

export const currentUser = derived(
  authStore,
  $auth => $auth.user
);

export const currentSession = derived(
  authStore,
  $auth => $auth.session
);

export const authLoading = derived(
  authStore,
  $auth => $auth.loading
);

export const authError = derived(
  authStore,
  $auth => $auth.error
);

// Authentication guard helper
export function requireAuth() {
  const auth = get(authStore);
  
  if (!auth.authenticated) {
    console.log('Authentication required, redirecting to login...');
    
    // Store current URL for redirect after login
    const currentUrl = window.location.pathname + window.location.search;
    localStorage.setItem(AUTH_CONFIG.REDIRECT_URL_KEY, currentUrl);
    
    goto('/login');
    return false;
  }
  
  return true;
}

// Auto-initialize authentication on store creation
if (typeof window !== 'undefined') {
  authStore.initialize();
}