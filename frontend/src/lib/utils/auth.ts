import { goto } from '$app/navigation';
import { page } from '$app/stores';
import { authStore, authState } from '$lib/stores';
import { AUTH_CONFIG, AUTH_ROUTES } from '$lib/constants';

/**
 * Authentication guard for protecting routes
 * Redirects to login if user is not authenticated
 */
export function requireAuthentication(): boolean {
  const authenticated = authState.authenticated;
  
  if (!authenticated) {
    // Store current URL for redirect after login
    // For SvelteKit stores, we need to handle this differently
    // We'll get the URL from the global window object instead
    const redirectUrl = window.location.pathname + window.location.search;
    
    console.log('Authentication required, redirecting to login...', { redirectUrl });
    
    localStorage.setItem(AUTH_CONFIG.REDIRECT_URL_KEY, redirectUrl);
    
    // Defer navigation to break any reactive chains
    queueMicrotask(() => {
      goto(AUTH_ROUTES.LOGIN);
    });
    
    return false;
  }
  
  return true;
}

/**
 * Check if user is authenticated (non-blocking)
 */
export function isUserAuthenticated(): boolean {
  return authState.authenticated;
}

/**
 * Get current authenticated user
 */
export function getCurrentUser() {
  return authStore.user;
}

/**
 * Get current session information
 */
export function getCurrentSession() {
  return authStore.session;
}

/**
 * Check if user has a valid session token
 */
export function hasValidSession(): boolean {
  return authStore.authenticated && !!authStore.sessionToken;
}

/**
 * Logout current user
 */
export function logout(): void {
  authStore.logout();
}

/**
 * Redirect to login page with current URL as return destination
 */
export function redirectToLogin(): void {
  const redirectUrl = window.location.pathname + window.location.search;
  
  localStorage.setItem(AUTH_CONFIG.REDIRECT_URL_KEY, redirectUrl);
  
  // Defer navigation to break any reactive chains
  queueMicrotask(() => {
    goto(AUTH_ROUTES.LOGIN);
  });
}

/**
 * Initialize authentication and redirect if needed
 * Use this in +layout.svelte or +page.svelte for protected pages
 */
export async function initializeAuth(): Promise<boolean> {
  console.log('Initializing authentication...');
  
  // Initialize auth store if not already done
  await authStore.initialize();
  
  // Check if user is authenticated
  return requireAuthentication();
}

/**
 * Route guard function for use in load functions
 * Example usage in +page.ts:
 * 
 * import { requireAuthLoad } from '$lib/utils/auth';
 * export const load = requireAuthLoad;
 */
export function requireAuthLoad() {
  return async ({ url }: { url: URL }) => {
    const authenticated = authState.authenticated;
    
    if (!authenticated) {
      const redirectUrl = url.pathname + url.search;
      localStorage.setItem(AUTH_CONFIG.REDIRECT_URL_KEY, redirectUrl);
      
      throw new Error(`redirect:${AUTH_ROUTES.LOGIN}`);
    }
    
    return {};
  };
}

/**
 * Check if a route is protected based on navigation items
 */
export function isProtectedRoute(pathname: string): boolean {
  // Import here to avoid circular dependency
  import('$lib/constants').then(({ NAVIGATION_ITEMS }) => {
    const navItem = NAVIGATION_ITEMS.find(item => item.href === pathname);
    return navItem?.protected ?? false;
  });
  
  // Default protected routes
  const protectedPaths = ['/', '/analysis', '/reports', '/settings', '/profile'];
  return protectedPaths.includes(pathname);
}

/**
 * Session validation helper
 * Checks if session is still valid and refreshes if needed
 */
export async function validateAndRefreshSession(): Promise<boolean> {
  if (!authStore.sessionToken) {
    return false;
  }
  
  try {
    // Try to validate current session
    const response = await fetch('/auth/validate', {
      headers: {
        'Authorization': `Bearer ${authStore.sessionToken}`
      }
    });
    
    if (response.ok) {
      return true;
    }
    
    // If validation fails, try to refresh tokens
    if (response.status === 401) {
      console.log('Session expired, attempting token refresh...');
      await authStore.refreshTokens();
      return true;
    }
    
    return false;
    
  } catch (error) {
    console.error('Session validation failed:', error);
    return false;
  }
}

/**
 * Auto-refresh session tokens before expiry
 * Call this periodically or on app focus
 */
export async function autoRefreshTokens(): Promise<void> {
  // Get a snapshot of the current auth state to avoid reactive access
  const snapshot = authStore.getSnapshot();
  
  if (!snapshot.authenticated || !snapshot.session) {
    return;
  }
  
  // Check if session is close to expiry
  const expiresAt = new Date(snapshot.session.expires_at);
  const now = new Date();
  const timeUntilExpiry = expiresAt.getTime() - now.getTime();
  
  // Refresh tokens if they expire within the threshold
  if (timeUntilExpiry < AUTH_CONFIG.TOKEN_REFRESH_THRESHOLD_MS) {
    console.log('Session expiring soon, refreshing tokens...');
    await authStore.refreshTokens();
  }
}

/**
 * Handle authentication errors globally
 */
export function handleAuthError(error: any): void {
  if (error.status === 401 || error.code === 'AUTH_TOKEN_INVALID') {
    console.log('Authentication error, logging out user...');
    authStore.logout();
  }
}

/**
 * Setup automatic session management (Svelte 5 compatible)
 * Call this in your main app component
 */
export function setupSessionManagement(): () => void {
  // Auto-refresh tokens periodically
  const refreshInterval = setInterval(autoRefreshTokens, 5 * 60 * 1000); // Every 5 minutes
  
  // Refresh tokens on window focus
  const handleFocus = () => autoRefreshTokens();
  window.addEventListener('focus', handleFocus);
  
  // Cleanup function
  return () => {
    clearInterval(refreshInterval);
    window.removeEventListener('focus', handleFocus);
  };
}