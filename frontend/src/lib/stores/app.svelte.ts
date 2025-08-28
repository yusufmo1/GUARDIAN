import { browser } from '$app/environment';
import type { AppSettings, User } from '$lib/types';

// Default settings configuration
const defaultSettings: AppSettings = {
  apiUrl: 'http://127.0.0.1:5051',
  theme: 'auto', // Updated to use auto as default
  notifications: true,
  autoAnalysis: false
};

const SETTINGS_STORAGE_KEY = 'guardian-app-settings';

// Helper to get stored settings
function getStoredSettings(): AppSettings {
  if (!browser) return defaultSettings;
  
  try {
    const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      // Merge with defaults to ensure all properties exist
      return { ...defaultSettings, ...parsed };
    }
  } catch (error) {
    console.warn('Failed to parse stored settings, using defaults:', error);
  }
  
  return defaultSettings;
}

// Create reactive app state using Svelte 5 runes
let loading = $state(false);
let error = $state<string | null>(null);
let settings = $state<AppSettings>(browser ? getStoredSettings() : defaultSettings);
let user = $state<User | null>(null);

// Derived computations for app state (as getter functions for module exports)
export function isLoading() { return loading; }
export function hasError() { return error !== null; }
export function currentSettings() { return settings; }
export function currentUser() { return user; }
export function isAuthenticated() { return user !== null; }

// Note: Effects moved inside component initialization in +layout.svelte
// Store-level effects are not allowed in Svelte 5

// App store interface - replaces the old factory pattern
export const appStore = {
  // Getters for reactive access
  get loading(): boolean {
    return loading;
  },
  
  get error(): string | null {
    return error;
  },
  
  get settings(): AppSettings {
    return settings;
  },
  
  get user(): User | null {
    return user;
  },
  
  // Loading state management
  setLoading(isLoading: boolean): void {
    loading = isLoading;
  },
  
  startLoading(): void {
    loading = true;
    error = null; // Clear any existing errors when starting new operation
  },
  
  stopLoading(): void {
    loading = false;
  },
  
  // Error state management
  setError(errorMessage: string | null): void {
    error = errorMessage;
    loading = false; // Stop loading when error occurs
  },
  
  clearError(): void {
    error = null;
  },
  
  // User management
  setUser(newUser: User | null): void {
    user = newUser;
  },
  
  // Settings management
  updateSettings(updates: Partial<AppSettings>): void {
    settings = { ...settings, ...updates };
  },
  
  setSetting<K extends keyof AppSettings>(key: K, value: AppSettings[K]): void {
    settings = { ...settings, [key]: value };
  },
  
  resetSettings(): void {
    settings = { ...defaultSettings };
  },
  
  // API URL management
  setApiUrl(url: string): void {
    settings = { ...settings, apiUrl: url };
  },
  
  // Theme management (delegated to theme store)
  setTheme(theme: AppSettings['theme']): void {
    settings = { ...settings, theme };
  },
  
  // Notification preferences
  setNotifications(enabled: boolean): void {
    settings = { ...settings, notifications: enabled };
  },
  
  // Auto-analysis preference
  setAutoAnalysis(enabled: boolean): void {
    settings = { ...settings, autoAnalysis: enabled };
  },
  
  // Complete reset
  reset(): void {
    loading = false;
    error = null;
    settings = { ...defaultSettings };
    user = null;
  },
  
  // State validation
  validate(): boolean {
    try {
      // Validate API URL format
      if (settings.apiUrl) {
        new URL(settings.apiUrl);
      }
      
      // Validate theme value
      const validThemes = ['light', 'dark', 'auto'];
      if (validThemes.indexOf(settings.theme) === -1) {
        return false;
      }
      
      // Validate boolean settings
      if (typeof settings.notifications !== 'boolean' || 
          typeof settings.autoAnalysis !== 'boolean') {
        return false;
      }
      
      return true;
    } catch {
      return false;
    }
  },
  
  // Get current state snapshot
  getSnapshot() {
    return {
      loading,
      error,
      settings: { ...settings },
      user: user ? { ...user } : null
    };
  },
  
  // Initialize app state
  initialize(): void {
    // Load settings from localStorage
    const storedSettings = getStoredSettings();
    settings = storedSettings;
    
    // Validate loaded settings
    if (!this.validate()) {
      console.warn('Invalid settings detected, resetting to defaults');
      this.resetSettings();
    }
  }
};