import { authStore, toastStore } from '$lib/stores';
import { AUTH_CONFIG } from '$lib/constants';

export interface SessionTimeoutConfig {
  warningThresholdMs: number; // Time before expiry to show warning
  warningIntervalMs: number;   // How often to check for expiry
  autoLogoutOnExpiry: boolean; // Whether to auto-logout on expiry
}

const DEFAULT_CONFIG: SessionTimeoutConfig = {
  warningThresholdMs: 10 * 60 * 1000, // 10 minutes before expiry
  warningIntervalMs: 60 * 1000,       // Check every minute
  autoLogoutOnExpiry: true
};

export class SessionTimeoutManager {
  private config: SessionTimeoutConfig;
  private warningInterval: NodeJS.Timeout | null = null;
  private warningShown = false;
  private lastWarningTime = 0;
  private isActive = false;

  constructor(config: Partial<SessionTimeoutConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Start monitoring session timeout
   */
  start(): void {
    if (this.isActive) {
      this.stop(); // Stop existing monitoring
    }

    this.isActive = true;
    this.warningShown = false;
    this.lastWarningTime = 0;

    console.log('Session timeout monitoring started');

    // Check immediately
    this.checkSessionTimeout();

    // Set up interval checking
    this.warningInterval = setInterval(() => {
      this.checkSessionTimeout();
    }, this.config.warningIntervalMs);
  }

  /**
   * Stop monitoring session timeout
   */
  stop(): void {
    if (this.warningInterval) {
      clearInterval(this.warningInterval);
      this.warningInterval = null;
    }

    this.isActive = false;
    this.warningShown = false;
    this.lastWarningTime = 0;

    console.log('Session timeout monitoring stopped');
  }

  /**
   * Reset the warning state (call after successful token refresh)
   */
  resetWarning(): void {
    this.warningShown = false;
    this.lastWarningTime = 0;
    console.log('Session timeout warning reset');
  }

  /**
   * Check if session is close to expiry and handle appropriately
   */
  private checkSessionTimeout(): void {
    // Get a snapshot to avoid reactive access in interval
    const snapshot = authStore.getSnapshot();
    const session = snapshot.session;
    
    if (!session?.expires_at) {
      // No session or no expiry time
      return;
    }

    const now = new Date().getTime();
    const expiresAt = new Date(session.expires_at).getTime();
    const timeUntilExpiry = expiresAt - now;

    // Check if session has already expired
    if (timeUntilExpiry <= 0) {
      console.warn('Session has expired');
      this.handleSessionExpiry();
      return;
    }

    // Check if we should show warning
    if (timeUntilExpiry <= this.config.warningThresholdMs) {
      this.handleSessionWarning(timeUntilExpiry);
    }
  }

  /**
   * Handle session expiry
   */
  private handleSessionExpiry(): void {
    this.stop();

    if (this.config.autoLogoutOnExpiry) {
      console.log('Auto-logging out due to session expiry');
      
      toastStore.error(
        'Session Expired',
        'Your session has expired. Please sign in again.',
        8000
      );

      // Logout after a short delay to let the toast show
      setTimeout(() => {
        authStore.logout();
      }, 1000);
    } else {
      toastStore.warning(
        'Session Expired',
        'Your session has expired. Please refresh your tokens or sign in again.',
        0 // Don't auto-dismiss
      );
    }
  }

  /**
   * Handle session warning (when close to expiry)
   */
  private handleSessionWarning(timeUntilExpiry: number): void {
    const now = Date.now();
    
    // Don't show warning too frequently
    if (this.warningShown && (now - this.lastWarningTime) < 2 * 60 * 1000) {
      return; // Wait at least 2 minutes between warnings
    }

    this.warningShown = true;
    this.lastWarningTime = now;

    const minutesLeft = Math.ceil(timeUntilExpiry / (60 * 1000));
    
    console.warn(`Session expires in ${minutesLeft} minutes`);

    toastStore.warning(
      'Session Expiring Soon',
      `Your session will expire in ${minutesLeft} minute${minutesLeft !== 1 ? 's' : ''}. ` +
      'Click here to refresh your session.',
      10000
    );

    // Auto-refresh tokens if we're very close to expiry
    if (timeUntilExpiry <= 5 * 60 * 1000) { // 5 minutes
      console.log('Auto-refreshing tokens due to imminent expiry');
      this.attemptTokenRefresh();
    }
  }

  /**
   * Attempt to refresh authentication tokens
   */
  private async attemptTokenRefresh(): Promise<void> {
    try {
      await authStore.refreshTokens();
      
      toastStore.success(
        'Session Refreshed',
        'Your session has been successfully renewed.',
        4000
      );

      this.resetWarning();
      
    } catch (error) {
      console.error('Failed to refresh tokens:', error);
      
      toastStore.error(
        'Session Refresh Failed',
        'Unable to refresh your session. Please sign in again.',
        8000
      );

      // Don't auto-logout here - let the user decide
    }
  }

  /**
   * Get current session status
   */
  getSessionStatus(): {
    isActive: boolean;
    expiresAt: Date | null;
    timeUntilExpiry: number | null;
    warningShown: boolean;
  } {
    // Get a snapshot to avoid reactive access
    const snapshot = authStore.getSnapshot();
    const session = snapshot.session;
    const expiresAt = session?.expires_at ? new Date(session.expires_at) : null;
    const timeUntilExpiry = expiresAt ? expiresAt.getTime() - new Date().getTime() : null;

    return {
      isActive: this.isActive,
      expiresAt,
      timeUntilExpiry,
      warningShown: this.warningShown
    };
  }
}

// Create global instance
export const sessionTimeoutManager = new SessionTimeoutManager();

/**
 * Setup session timeout monitoring
 * Call this from your main app component or layout
 */
export function setupSessionTimeoutMonitoring(config?: Partial<SessionTimeoutConfig>): () => void {
  const manager = config ? new SessionTimeoutManager(config) : sessionTimeoutManager;
  
  let isManagerRunning = false;
  
  // Check auth status periodically using snapshots to avoid reactive loops
  const checkAuthInterval = setInterval(() => {
    // Get a snapshot to avoid reactive access in interval
    const snapshot = authStore.getSnapshot();
    
    if (snapshot.authenticated && snapshot.session) {
      if (!isManagerRunning) {
        manager.start();
        isManagerRunning = true;
      }
    } else {
      if (isManagerRunning) {
        manager.stop();
        isManagerRunning = false;
      }
    }
  }, 5000); // Check every 5 seconds
  
  // Initial check using snapshot
  const initialSnapshot = authStore.getSnapshot();
  if (initialSnapshot.authenticated && initialSnapshot.session) {
    manager.start();
    isManagerRunning = true;
  }
  
  // Cleanup function
  return () => {
    clearInterval(checkAuthInterval);
    manager.stop();
  };
}

/**
 * Manual session refresh function for UI components
 */
export async function refreshSession(): Promise<boolean> {
  try {
    await authStore.refreshTokens();
    sessionTimeoutManager.resetWarning();
    
    toastStore.success(
      'Session Refreshed',
      'Your session has been successfully renewed.'
    );
    
    return true;
  } catch (error) {
    console.error('Failed to refresh session:', error);
    
    toastStore.error(
      'Refresh Failed',
      'Unable to refresh your session. Please try signing in again.'
    );
    
    return false;
  }
}