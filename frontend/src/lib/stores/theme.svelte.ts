import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'auto';
export type ResolvedTheme = 'light' | 'dark';

const STORAGE_KEY = 'guardian-theme-preference';

// Helper to get system preference
function getSystemTheme(): ResolvedTheme {
  if (!browser) return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

// Helper to get stored preference
function getStoredTheme(): Theme {
  if (!browser) return 'auto';
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'light' || stored === 'dark' || stored === 'auto') {
    return stored;
  }
  return 'auto'; // Default to auto
}

// Helper to resolve actual theme based on preference
function resolveTheme(preference: Theme): ResolvedTheme {
  if (preference === 'auto') {
    return getSystemTheme();
  }
  return preference;
}

// Apply theme to document
function applyTheme(theme: ResolvedTheme) {
  if (!browser) return;
  
  // Apply data-theme attribute to html element
  document.documentElement.setAttribute('data-theme', theme);
  
  // Also update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', theme === 'dark' ? '#0f172a' : '#f8fafc');
  }
}

// Create reactive theme state using Svelte 5 runes
let themePreference = $state<Theme>(getStoredTheme());

// Derived resolved theme
export function resolvedTheme(): ResolvedTheme { return resolveTheme(themePreference); }

// Store internal state to track when to apply theme
let lastAppliedTheme: ResolvedTheme | null = null;

// Theme store interface - replaces the old factory pattern
export const themeStore = {
  // Getters for reactive access
  get current(): Theme {
    return themePreference;
  },
  
  get resolved(): ResolvedTheme {
    return resolvedTheme();
  },
  
  // Methods for theme manipulation
  set(theme: Theme): void {
    themePreference = theme;
    this.applyCurrentTheme();
  },
  
  toggle(): void {
    const resolved = resolveTheme(themePreference);
    // If auto or light, go to dark. If dark, go to light.
    themePreference = resolved === 'dark' ? 'light' : 'dark';
    this.applyCurrentTheme();
  },
  
  initialize(): void {
    // Initialize theme on app startup
    const preference = getStoredTheme();
    themePreference = preference;
    this.applyCurrentTheme();
    this.setupSystemThemeListener();
  },
  
  // Apply current theme to DOM
  applyCurrentTheme(): void {
    if (!browser) return;
    
    const resolved = resolveTheme(themePreference);
    
    // Only apply if theme actually changed
    if (lastAppliedTheme === resolved) return;
    lastAppliedTheme = resolved;
    
    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, themePreference);
    
    // Apply theme to DOM
    applyTheme(resolved);
  },
  
  // Setup system theme change listener
  setupSystemThemeListener(): void {
    if (!browser) return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      // Only update display if set to auto
      if (themePreference === 'auto') {
        const newTheme = e.matches ? 'dark' : 'light';
        applyTheme(newTheme);
      }
    };

    // Add event listener
    mediaQuery.addEventListener('change', handleChange);
  },
  
  setLight(): void {
    themePreference = 'light';
    this.applyCurrentTheme();
  },
  
  setDark(): void {
    themePreference = 'dark';
    this.applyCurrentTheme();
  },
  
  setAuto(): void {
    themePreference = 'auto';
    this.applyCurrentTheme();
  }
};