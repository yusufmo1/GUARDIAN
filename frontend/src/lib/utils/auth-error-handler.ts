import { authStore } from '$lib/stores';
import { toastStore } from '$lib/stores/toast';
import { goto } from '$app/navigation';
import { AUTH_ROUTES } from '$lib/constants';

export interface AuthErrorContext {
  operation: string;
  route?: string;
  retryable?: boolean;
  redirectToLogin?: boolean;
}

export type AuthErrorCode = 
  | 'AUTH_TOKEN_MISSING'
  | 'AUTH_TOKEN_INVALID' 
  | 'AUTH_TOKEN_EXPIRED'
  | 'AUTH_SESSION_INVALID'
  | 'AUTH_REFRESH_FAILED'
  | 'AUTH_NETWORK_ERROR'
  | 'AUTH_PERMISSION_DENIED'
  | 'AUTH_RATE_LIMITED'
  | 'AUTH_SERVER_ERROR'
  | 'AUTH_USER_NOT_FOUND'
  | 'AUTH_OAUTH_ERROR'
  | 'AUTH_UNKNOWN_ERROR';

export interface AuthError extends Error {
  code: AuthErrorCode;
  status?: number;
  context?: AuthErrorContext;
  details?: any;
}

export class AuthErrorHandler {
  private static retryAttempts = new Map<string, number>();
  private static readonly MAX_RETRIES = 3;
  private static readonly RETRY_DELAY = 2000; // 2 seconds

  /**
   * Handle authentication errors based on error code and context
   */
  static async handleError(error: AuthError): Promise<void> {
    console.error(`Auth Error [${error.code}]:`, error.message, error.context);

    switch (error.code) {
      case 'AUTH_TOKEN_MISSING':
        await this.handleMissingToken(error);
        break;
        
      case 'AUTH_TOKEN_INVALID':
      case 'AUTH_SESSION_INVALID':
        await this.handleInvalidToken(error);
        break;
        
      case 'AUTH_TOKEN_EXPIRED':
        await this.handleExpiredToken(error);
        break;
        
      case 'AUTH_REFRESH_FAILED':
        await this.handleRefreshFailed(error);
        break;
        
      case 'AUTH_NETWORK_ERROR':
        await this.handleNetworkError(error);
        break;
        
      case 'AUTH_PERMISSION_DENIED':
        await this.handlePermissionDenied(error);
        break;
        
      case 'AUTH_RATE_LIMITED':
        await this.handleRateLimited(error);
        break;
        
      case 'AUTH_SERVER_ERROR':
        await this.handleServerError(error);
        break;
        
      case 'AUTH_USER_NOT_FOUND':
        await this.handleUserNotFound(error);
        break;
        
      case 'AUTH_OAUTH_ERROR':
        await this.handleOAuthError(error);
        break;
        
      default:
        await this.handleUnknownError(error);
        break;
    }
  }

  /**
   * Handle missing authentication token
   */
  private static async handleMissingToken(error: AuthError): Promise<void> {
    toastStore.warning(
      'Authentication Required',
      'Please sign in to access this feature.'
    );

    if (error.context?.redirectToLogin !== false) {
      this.redirectToLogin(error.context?.route);
    }
  }

  /**
   * Handle invalid authentication token
   */
  private static async handleInvalidToken(error: AuthError): Promise<void> {
    // Clear invalid session
    await authStore.clearSession();

    toastStore.error(
      'Invalid Session',
      'Your session is invalid. Please sign in again.'
    );

    this.redirectToLogin(error.context?.route);
  }

  /**
   * Handle expired authentication token
   */
  private static async handleExpiredToken(error: AuthError): Promise<void> {
    const operationKey = error.context?.operation || 'default';
    const attempts = this.retryAttempts.get(operationKey) || 0;

    if (attempts < this.MAX_RETRIES && error.context?.retryable !== false) {
      console.log(`Attempting token refresh (attempt ${attempts + 1})`);
      
      try {
        this.retryAttempts.set(operationKey, attempts + 1);
        await authStore.refreshTokens();
        
        toastStore.success(
          'Session Renewed',
          'Your session has been automatically renewed.'
        );
        
        // Clear retry count on success
        this.retryAttempts.delete(operationKey);
        return;
        
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Continue to logout flow
      }
    }

    // Token refresh failed or max retries reached
    this.retryAttempts.delete(operationKey);
    
    toastStore.error(
      'Session Expired',
      'Your session has expired. Please sign in again.'
    );

    await authStore.logout();
  }

  /**
   * Handle token refresh failure
   */
  private static async handleRefreshFailed(error: AuthError): Promise<void> {
    toastStore.error(
      'Session Refresh Failed',
      'Unable to refresh your session. Please sign in again.'
    );

    await authStore.logout();
  }

  /**
   * Handle network errors
   */
  private static async handleNetworkError(error: AuthError): Promise<void> {
    const operationKey = error.context?.operation || 'network';
    const attempts = this.retryAttempts.get(operationKey) || 0;

    if (attempts < this.MAX_RETRIES && error.context?.retryable !== false) {
      this.retryAttempts.set(operationKey, attempts + 1);
      
      toastStore.warning(
        'Connection Issue',
        `Network error occurred. Retrying... (${attempts + 1}/${this.MAX_RETRIES})`
      );

      // Retry after delay
      setTimeout(() => {
        // The calling code should handle retry logic
      }, this.RETRY_DELAY * (attempts + 1)); // Exponential backoff
      
      return;
    }

    // Max retries reached
    this.retryAttempts.delete(operationKey);
    
    toastStore.error(
      'Connection Failed',
      'Unable to connect to the server. Please check your internet connection and try again.'
    );
  }

  /**
   * Handle permission denied errors
   */
  private static async handlePermissionDenied(error: AuthError): Promise<void> {
    toastStore.error(
      'Access Denied',
      'You do not have permission to perform this action.'
    );

    // Don't logout for permission errors - user might have access to other features
  }

  /**
   * Handle rate limiting errors
   */
  private static async handleRateLimited(error: AuthError): Promise<void> {
    const retryAfter = error.details?.retryAfter || 60; // seconds
    
    toastStore.warning(
      'Rate Limited',
      `Too many requests. Please wait ${retryAfter} seconds before trying again.`,
      retryAfter * 1000
    );
  }

  /**
   * Handle server errors
   */
  private static async handleServerError(error: AuthError): Promise<void> {
    toastStore.error(
      'Server Error',
      'A server error occurred. Please try again later or contact support if the issue persists.'
    );
  }

  /**
   * Handle user not found errors
   */
  private static async handleUserNotFound(error: AuthError): Promise<void> {
    await authStore.clearSession();
    
    toastStore.error(
      'Account Not Found',
      'Your account could not be found. Please sign in again.'
    );

    this.redirectToLogin(error.context?.route);
  }

  /**
   * Handle OAuth-specific errors
   */
  private static async handleOAuthError(error: AuthError): Promise<void> {
    const oauthErrors: Record<string, string> = {
      'access_denied': 'Authentication was cancelled.',
      'invalid_request': 'Invalid authentication request.',
      'invalid_scope': 'Invalid permissions requested.',
      'server_error': 'Google authentication server error.',
      'temporarily_unavailable': 'Google authentication temporarily unavailable.'
    };

    const userMessage = oauthErrors[error.details?.error] || 
                       'Google authentication failed. Please try again.';

    toastStore.error(
      'Google Sign-In Failed',
      userMessage
    );

    if (error.context?.redirectToLogin !== false) {
      // Defer navigation to break any reactive chains
      queueMicrotask(() => {
        goto(AUTH_ROUTES.LOGIN);
      });
    }
  }

  /**
   * Handle unknown errors
   */
  private static async handleUnknownError(error: AuthError): Promise<void> {
    console.error('Unknown auth error:', error);
    
    toastStore.error(
      'Authentication Error',
      'An unexpected authentication error occurred. Please try again.'
    );

    // Don't automatically logout for unknown errors
  }

  /**
   * Redirect to login page with current route as return destination
   */
  private static redirectToLogin(currentRoute?: string): void {
    const redirectUrl = currentRoute || window.location.pathname + window.location.search;
    const loginUrl = `${AUTH_ROUTES.LOGIN}?redirect=${encodeURIComponent(redirectUrl)}`;
    
    console.log('Redirecting to login:', loginUrl);
    // Defer navigation to break any reactive chains
    queueMicrotask(() => {
      goto(loginUrl);
    });
  }

  /**
   * Create an auth error with standardized structure
   */
  static createError(
    code: AuthErrorCode,
    message: string,
    context?: AuthErrorContext,
    status?: number,
    details?: any
  ): AuthError {
    const error = new Error(message) as AuthError;
    error.code = code;
    error.context = context;
    error.status = status;
    error.details = details;
    return error;
  }

  /**
   * Clear retry attempts for a specific operation
   */
  static clearRetryAttempts(operation: string): void {
    this.retryAttempts.delete(operation);
  }

  /**
   * Clear all retry attempts
   */
  static clearAllRetryAttempts(): void {
    this.retryAttempts.clear();
  }
}

/**
 * Convert API errors to auth errors
 */
export function convertApiErrorToAuthError(
  error: any,
  context?: AuthErrorContext
): AuthError {
  // Handle GuardianApiError
  if (error.status && error.code) {
    const authCode = mapStatusToAuthCode(error.status, error.code);
    return AuthErrorHandler.createError(
      authCode,
      error.message || 'Authentication error',
      context,
      error.status,
      error.errors
    );
  }

  // Handle network errors
  if (error.name === 'TypeError' || error.message?.includes('fetch')) {
    return AuthErrorHandler.createError(
      'AUTH_NETWORK_ERROR',
      'Network connection failed',
      context
    );
  }

  // Handle unknown errors
  return AuthErrorHandler.createError(
    'AUTH_UNKNOWN_ERROR',
    error.message || 'Unknown authentication error',
    context
  );
}

/**
 * Map HTTP status codes and error codes to auth error codes
 */
function mapStatusToAuthCode(status: number, code?: string): AuthErrorCode {
  if (code) {
    const codeMap: Record<string, AuthErrorCode> = {
      'AUTH_TOKEN_MISSING': 'AUTH_TOKEN_MISSING',
      'AUTH_TOKEN_INVALID': 'AUTH_TOKEN_INVALID',
      'AUTH_TOKEN_EXPIRED': 'AUTH_TOKEN_EXPIRED',
      'AUTH_SESSION_INVALID': 'AUTH_SESSION_INVALID',
      'OAUTH_ERROR': 'AUTH_OAUTH_ERROR'
    };
    
    if (codeMap[code]) {
      return codeMap[code];
    }
  }

  const statusMap: Record<number, AuthErrorCode> = {
    401: 'AUTH_TOKEN_INVALID',
    403: 'AUTH_PERMISSION_DENIED',
    404: 'AUTH_USER_NOT_FOUND',
    429: 'AUTH_RATE_LIMITED',
    500: 'AUTH_SERVER_ERROR',
    502: 'AUTH_SERVER_ERROR',
    503: 'AUTH_SERVER_ERROR',
    504: 'AUTH_SERVER_ERROR'
  };

  return statusMap[status] || 'AUTH_UNKNOWN_ERROR';
}