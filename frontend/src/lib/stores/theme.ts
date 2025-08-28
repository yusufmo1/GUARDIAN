import { writable, derived } from 'svelte/store';
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
  if (!browser) return 'light';
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

// Create the theme preference store
function createThemeStore() {
  const { subscribe, set, update } = writable<Theme>(getStoredTheme());

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

  // Subscribe to changes and apply theme
  subscribe(preference => {
    if (!browser) return;
    
    // Save to localStorage
    localStorage.setItem(STORAGE_KEY, preference);
    
    // Apply the resolved theme
    const resolved = resolveTheme(preference);
    applyTheme(resolved);
  });

  // Listen for system theme changes
  if (browser) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Use addEventListener with proper typing
    const handleChange = (e: MediaQueryListEvent) => {
      // Get current preference
      const currentPref = getStoredTheme();
      
      // Only update if set to auto
      if (currentPref === 'auto') {
        const newTheme = e.matches ? 'dark' : 'light';
        applyTheme(newTheme);
      }
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange as any);
    }
  }

  return {
    subscribe,
    set: (theme: Theme) => {
      set(theme);
    },
    toggle: () => {
      update(current => {
        const resolved = resolveTheme(current);
        // If auto or light, go to dark. If dark, go to light.
        return resolved === 'dark' ? 'light' : 'dark';
      });
    },
    initialize: () => {
      // Initialize theme on app startup
      const preference = getStoredTheme();
      set(preference);
    }
  };
}

// Create the store
export const themeStore = createThemeStore();

// Derived store for the actual resolved theme (useful for UI)
export const resolvedTheme = derived<typeof themeStore, ResolvedTheme>(
  themeStore,
  ($themeStore) => resolveTheme($themeStore)
);