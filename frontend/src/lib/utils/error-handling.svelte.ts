/**
 * Advanced Error Handling Utilities for Svelte 5 Runes
 * Provides error boundaries, retry logic, and structured error management
 */

import { browser } from '$app/environment';
import { toastStore } from '$lib/stores/toast';

// Error types for categorization
export enum ErrorType {
  NETWORK = 'network',
  VALIDATION = 'validation',
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  SERVER = 'server',
  CLIENT = 'client',
  UNKNOWN = 'unknown'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface AppError {
  id: string;
  type: ErrorType;
  severity: ErrorSeverity;
  message: string;
  details?: any;
  timestamp: number;
  context?: Record<string, any>;
  recovered?: boolean;
  retryCount?: number;
}

// Global error state
let errorState = $state({
  errors: [] as AppError[],
  isRecovering: false,
  lastErrorTime: 0,
  errorCounts: new Map<ErrorType, number>()
});

/**
 * Create a structured error object
 */
export function createError(
  message: string,
  type: ErrorType = ErrorType.UNKNOWN,
  severity: ErrorSeverity = ErrorSeverity.MEDIUM,
  details?: any,
  context?: Record<string, any>
): AppError {
  const error: AppError = {
    id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type,
    severity,
    message,
    details,
    timestamp: Date.now(),
    context,
    recovered: false,
    retryCount: 0
  };

  // Log error for debugging
  if (browser) {
    console.error(`[${type.toUpperCase()}] ${message}`, { error, details, context });
  }

  return error;
}

/**
 * Global error boundary for error collection and handling
 */
export function errorBoundary() {
  const addError = (error: AppError) => {
    errorState.errors.push(error);
    errorState.lastErrorTime = Date.now();
    
    // Update error counts
    const currentCount = errorState.errorCounts.get(error.type) || 0;
    errorState.errorCounts.set(error.type, currentCount + 1);
    
    // Auto-clean old errors (keep last 50)
    if (errorState.errors.length > 50) {
      errorState.errors = errorState.errors.slice(-50);
    }
    
    // Show appropriate user notification
    showErrorNotification(error);
  };

  const removeError = (errorId: string) => {
    const index = errorState.errors.findIndex(e => e.id === errorId);
    if (index !== -1) {
      errorState.errors.splice(index, 1);
    }
  };

  const markAsRecovered = (errorId: string) => {
    const error = errorState.errors.find(e => e.id === errorId);
    if (error) {
      error.recovered = true;
    }
  };

  const clearErrors = (type?: ErrorType) => {
    if (type) {
      errorState.errors = errorState.errors.filter(e => e.type !== type);
    } else {
      errorState.errors = [];
      errorState.errorCounts.clear();
    }
  };

  const getErrorsByType = (type: ErrorType) => {
    return errorState.errors.filter(e => e.type === type);
  };

  const getRecentErrors = (minutes: number = 5) => {
    const cutoff = Date.now() - (minutes * 60 * 1000);
    return errorState.errors.filter(e => e.timestamp > cutoff);
  };

  return {
    // State access
    errors: () => errorState.errors,
    isRecovering: () => errorState.isRecovering,
    errorCounts: () => Object.fromEntries(errorState.errorCounts),
    
    // Error management
    addError,
    removeError,
    markAsRecovered,
    clearErrors,
    getErrorsByType,
    getRecentErrors
  };
}

/**
 * Retry mechanism with exponential backoff
 */
export function withRetry<T>(
  operation: () => Promise<T>,
  options: {
    maxRetries?: number;
    baseDelay?: number;
    maxDelay?: number;
    backoffFactor?: number;
    retryCondition?: (error: any) => boolean;
    onRetry?: (attempt: number, error: any) => void;
    context?: Record<string, any>;
  } = {}
): Promise<T> {
  const {
    maxRetries = 3,
    baseDelay = 1000,
    maxDelay = 10000,
    backoffFactor = 2,
    retryCondition = (error) => !isNonRetryableError(error),
    onRetry,
    context = {}
  } = options;

  return new Promise(async (resolve, reject) => {
    let lastError: any;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const result = await operation();
        resolve(result);
        return;
      } catch (error) {
        lastError = error;
        
        // Don't retry on last attempt or if error is non-retryable
        if (attempt === maxRetries || !retryCondition(error)) {
          const appError = createError(
            `Operation failed after ${attempt + 1} attempts: ${error.message}`,
            categorizeError(error),
            attempt === maxRetries ? ErrorSeverity.HIGH : ErrorSeverity.MEDIUM,
            { originalError: error, attempts: attempt + 1 },
            context
          );
          
          errorBoundary().addError(appError);
          reject(error);
          return;
        }
        
        // Calculate delay with exponential backoff
        const delay = Math.min(
          baseDelay * Math.pow(backoffFactor, attempt),
          maxDelay
        );
        
        // Call retry callback if provided
        if (onRetry) {
          onRetry(attempt + 1, error);
        }
        
        // Wait before retrying
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  });
}

/**
 * Error recovery effect that handles automatic recovery
 */
export function errorRecovery(
  errorProvider: () => AppError | null,
  recoveryActions: {
    [key in ErrorType]?: () => Promise<boolean> | boolean;
  },
  options: {
    autoRecover?: boolean;
    recoveryDelay?: number;
    maxRecoveryAttempts?: number;
  } = {}
) {
  const { autoRecover = true, recoveryDelay = 2000, maxRecoveryAttempts = 3 } = options;
  let recoveryAttempts = 0;

  $effect(() => {
    const error = errorProvider();
    
    if (!error || error.recovered || !autoRecover) return;
    
    const recoveryAction = recoveryActions[error.type];
    if (!recoveryAction || recoveryAttempts >= maxRecoveryAttempts) return;

    const attemptRecovery = async () => {
      errorState.isRecovering = true;
      recoveryAttempts++;
      
      try {
        const recovered = await recoveryAction();
        
        if (recovered) {
          errorBoundary().markAsRecovered(error.id);
          recoveryAttempts = 0;
          
          toastStore.add({
            type: 'success',
            title: 'Recovered from error',
            description: 'The application has automatically recovered from the previous error.'
          });
        }
      } catch (recoveryError) {
        console.warn('Recovery attempt failed:', recoveryError);
      } finally {
        errorState.isRecovering = false;
      }
    };

    // Delay recovery attempt
    const timeout = setTimeout(attemptRecovery, recoveryDelay);
    
    return () => clearTimeout(timeout);
  });
}

/**
 * Structured error logging with context
 */
export function logError(
  error: Error | AppError,
  context?: Record<string, any>,
  level: 'error' | 'warn' | 'info' = 'error'
): void {
  if (!browser) return;

  const logData = {
    timestamp: new Date().toISOString(),
    error: error instanceof Error ? {
      name: error.name,
      message: error.message,
      stack: error.stack
    } : error,
    context,
    userAgent: navigator.userAgent,
    url: window.location.href
  };

  // Log to console
  console[level]('[Error Logger]', logData);
  
  // In production, this could send to an error tracking service
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost') {
    // Example: Send to error tracking service
    // sendToErrorTracker(logData);
  }
}

/**
 * Utility functions for error categorization
 */
function categorizeError(error: any): ErrorType {
  if (!error) return ErrorType.UNKNOWN;
  
  const message = error.message?.toLowerCase() || '';
  const status = error.status || error.code;
  
  // Network errors
  if (message.includes('network') || message.includes('fetch') || !navigator.onLine) {
    return ErrorType.NETWORK;
  }
  
  // Authentication errors
  if (status === 401 || message.includes('unauthorized') || message.includes('authentication')) {
    return ErrorType.AUTHENTICATION;
  }
  
  // Authorization errors
  if (status === 403 || message.includes('forbidden') || message.includes('authorization')) {
    return ErrorType.AUTHORIZATION;
  }
  
  // Validation errors
  if (status === 400 || message.includes('validation') || message.includes('invalid')) {
    return ErrorType.VALIDATION;
  }
  
  // Server errors
  if (status >= 500 || message.includes('server error') || message.includes('internal error')) {
    return ErrorType.SERVER;
  }
  
  // Client errors
  if (status >= 400 && status < 500) {
    return ErrorType.CLIENT;
  }
  
  return ErrorType.UNKNOWN;
}

function isNonRetryableError(error: any): boolean {
  const status = error.status || error.code;
  const message = error.message?.toLowerCase() || '';
  
  // Don't retry authentication/authorization errors
  if (status === 401 || status === 403) return true;
  
  // Don't retry validation errors
  if (status === 400 || message.includes('validation')) return true;
  
  // Don't retry not found errors
  if (status === 404) return true;
  
  return false;
}

function showErrorNotification(error: AppError): void {
  // Don't show notifications for low severity or recovered errors
  if (error.severity === ErrorSeverity.LOW || error.recovered) return;
  
  // Don't spam notifications - limit to one per minute for same type
  const recentSimilarErrors = errorState.errors.filter(e => 
    e.type === error.type && 
    e.timestamp > Date.now() - 60000 &&
    e.id !== error.id
  );
  
  if (recentSimilarErrors.length > 0) return;
  
  const toastType = error.severity === ErrorSeverity.CRITICAL ? 'error' : 'warning';
  
  toastStore.add({
    type: toastType,
    title: getErrorTitle(error.type),
    description: error.message,
    duration: error.severity === ErrorSeverity.CRITICAL ? 0 : 5000 // Critical errors stay until dismissed
  });
}

function getErrorTitle(type: ErrorType): string {
  switch (type) {
    case ErrorType.NETWORK:
      return 'Connection Error';
    case ErrorType.AUTHENTICATION:
      return 'Authentication Required';
    case ErrorType.AUTHORIZATION:
      return 'Access Denied';
    case ErrorType.VALIDATION:
      return 'Validation Error';
    case ErrorType.SERVER:
      return 'Server Error';
    case ErrorType.CLIENT:
      return 'Application Error';
    default:
      return 'Unexpected Error';
  }
}

// Export error state for components
export { errorState };

// Initialize global error boundary
export const globalErrorBoundary = errorBoundary();