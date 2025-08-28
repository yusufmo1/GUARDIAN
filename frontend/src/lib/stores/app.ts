import { writable } from 'svelte/store';
import type { AppState, AppSettings } from '$lib/types';

const defaultSettings: AppSettings = {
  apiUrl: '', // Empty string means use relative URLs (proxy in dev)
  theme: 'light',
  notifications: true,
  autoAnalysis: false
};

const defaultAppState: AppState = {
  loading: false,
  error: null,
  settings: defaultSettings,
  user: null
};

function createAppStore() {
  const { subscribe, set, update } = writable<AppState>(defaultAppState);

  return {
    subscribe,
    setLoading: (loading: boolean) => update(state => ({ ...state, loading })),
    setError: (error: string | null) => update(state => ({ ...state, error })),
    clearError: () => update(state => ({ ...state, error: null })),
    updateSettings: (settings: Partial<AppSettings>) => 
      update(state => ({ 
        ...state, 
        settings: { ...state.settings, ...settings } 
      })),
    reset: () => set(defaultAppState)
  };
}

export const appStore = createAppStore();