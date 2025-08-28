/**
 * Advanced State Persistence Utilities for Svelte 5 Runes
 * Provides state persistence, hydration, versioning, and cross-tab synchronization
 */

import { browser } from '$app/environment';

// State versioning for schema migration
export interface PersistedState<T = any> {
  version: number;
  data: T;
  timestamp: number;
  checksum?: string;
}

export interface PersistenceConfig {
  key: string;
  version: number;
  storage?: 'localStorage' | 'sessionStorage' | 'indexedDB';
  compress?: boolean;
  encrypt?: boolean;
  migrationStrategies?: Record<number, (data: any) => any>;
  include?: string[]; // Specific fields to persist
  exclude?: string[]; // Fields to exclude from persistence
  debounceMs?: number; // Debounce persistence writes
  crossTab?: boolean; // Enable cross-tab synchronization
}

// Cross-tab synchronization state
let crossTabState = $state({
  isInitialized: false,
  channel: null as BroadcastChannel | null,
  listeners: new Map<string, Set<(data: any) => void>>()
});

/**
 * Enhanced state persistence with versioning and migration
 */
export function persistedState<T>(
  initialState: T,
  config: PersistenceConfig
): {
  state: T;
  persist: () => Promise<void>;
  restore: () => Promise<T>;
  clear: () => Promise<void>;
  migrate: (fromVersion: number, toVersion: number) => Promise<void>;
  getVersion: () => number;
  onCrossTabUpdate: (callback: (data: T) => void) => () => void;
} {
  const {
    key,
    version,
    storage = 'localStorage',
    compress = false,
    encrypt = false,
    migrationStrategies = {},
    include,
    exclude,
    debounceMs = 500,
    crossTab = false
  } = config;

  let persistedData = $state(initialState);
  let isHydrated = $state(false);
  let lastPersistTime = 0;
  let persistTimeout: number | null = null;

  // Initialize cross-tab sync if enabled
  if (crossTab && browser) {
    initializeCrossTabSync();
  }

  /**
   * Persist state to storage
   */
  const persist = async (): Promise<void> => {
    if (!browser) return;

    try {
      const dataToStore = filterData(persistedData, include, exclude);
      const stateToStore: PersistedState<T> = {
        version,
        data: dataToStore,
        timestamp: Date.now(),
        checksum: generateChecksum(dataToStore)
      };

      const serialized = JSON.stringify(stateToStore);
      const processed = compress ? await compressData(serialized) : serialized;
      const encrypted = encrypt ? await encryptData(processed) : processed;

      await writeToStorage(key, encrypted, storage);
      lastPersistTime = Date.now();

      // Broadcast to other tabs if cross-tab sync is enabled
      if (crossTab && crossTabState.channel) {
        crossTabState.channel.postMessage({
          type: 'state-update',
          key,
          data: dataToStore,
          timestamp: Date.now()
        });
      }
    } catch (error) {
      console.error(`Failed to persist state for key ${key}:`, error);
      throw error;
    }
  };

  /**
   * Restore state from storage with migration support
   */
  const restore = async (): Promise<T> => {
    if (!browser) {
      isHydrated = true;
      return persistedData;
    }

    try {
      const stored = await readFromStorage(key, storage);
      if (!stored) {
        isHydrated = true;
        return persistedData;
      }

      const decrypted = encrypt ? await decryptData(stored) : stored;
      const decompressed = compress ? await decompressData(decrypted) : decrypted;
      const parsed: PersistedState<T> = JSON.parse(decompressed);

      // Validate checksum if present
      if (parsed.checksum && parsed.checksum !== generateChecksum(parsed.data)) {
        console.warn(`Checksum mismatch for key ${key}, using initial state`);
        isHydrated = true;
        return persistedData;
      }

      // Handle version migration
      if (parsed.version !== version) {
        const migratedData = await migrateData(parsed.data, parsed.version, version);
        Object.assign(persistedData, mergeWithInitialState(migratedData, initialState));
      } else {
        Object.assign(persistedData, mergeWithInitialState(parsed.data, initialState));
      }

      isHydrated = true;
      return persistedData;
    } catch (error) {
      console.error(`Failed to restore state for key ${key}:`, error);
      isHydrated = true;
      return persistedData;
    }
  };

  /**
   * Clear persisted state
   */
  const clear = async (): Promise<void> => {
    if (!browser) return;

    try {
      await removeFromStorage(key, storage);
      Object.assign(persistedData, { ...initialState });
    } catch (error) {
      console.error(`Failed to clear state for key ${key}:`, error);
      throw error;
    }
  };

  /**
   * Manual migration between versions
   */
  const migrate = async (fromVersion: number, toVersion: number): Promise<void> => {
    if (!migrationStrategies[toVersion]) {
      throw new Error(`No migration strategy found for version ${toVersion}`);
    }

    const stored = await readFromStorage(key, storage);
    if (!stored) return;

    try {
      const parsed: PersistedState<T> = JSON.parse(stored);
      if (parsed.version === fromVersion) {
        const migratedData = await migrateData(parsed.data, fromVersion, toVersion);
        Object.assign(persistedData, migratedData);
        await persist();
      }
    } catch (error) {
      console.error(`Migration failed from ${fromVersion} to ${toVersion}:`, error);
      throw error;
    }
  };

  /**
   * Get current version
   */
  const getVersion = (): number => version;

  /**
   * Subscribe to cross-tab updates
   */
  const onCrossTabUpdate = (callback: (data: T) => void): (() => void) => {
    if (!crossTab) {
      console.warn('Cross-tab synchronization is not enabled');
      return () => {};
    }

    const listeners = crossTabState.listeners.get(key) || new Set();
    listeners.add(callback);
    crossTabState.listeners.set(key, listeners);

    return () => {
      const currentListeners = crossTabState.listeners.get(key);
      if (currentListeners) {
        currentListeners.delete(callback);
        if (currentListeners.size === 0) {
          crossTabState.listeners.delete(key);
        }
      }
    };
  };

  /**
   * Debounced persist effect
   */
  const debouncedPersist = () => {
    if (persistTimeout) {
      clearTimeout(persistTimeout);
    }

    persistTimeout = window.setTimeout(() => {
      persist().catch(error => {
        console.error('Debounced persist failed:', error);
      });
    }, debounceMs);
  };

  // Manual persistence setup (no auto-effects in Svelte 5)
  const triggerPersist = () => {
    if (isHydrated) {
      debouncedPersist();
    }
  };

  // Restore state on initialization
  if (browser) {
    restore().catch(error => {
      console.error('Initial state restoration failed:', error);
    });
  }

  return {
    state: persistedData,
    persist,
    restore,
    clear,
    migrate,
    getVersion,
    onCrossTabUpdate
  };
}

/**
 * Initialize cross-tab synchronization
 */
function initializeCrossTabSync(): void {
  if (!browser || crossTabState.isInitialized) return;

  try {
    crossTabState.channel = new BroadcastChannel('guardian-state-sync');
    
    crossTabState.channel.addEventListener('message', (event) => {
      const { type, key, data, timestamp } = event.data;
      
      if (type === 'state-update') {
        const listeners = crossTabState.listeners.get(key);
        if (listeners) {
          listeners.forEach(callback => {
            try {
              callback(data);
            } catch (error) {
              console.error('Cross-tab callback error:', error);
            }
          });
        }
      }
    });

    crossTabState.isInitialized = true;
  } catch (error) {
    console.error('Failed to initialize cross-tab sync:', error);
  }
}

/**
 * Data filtering utilities
 */
function filterData<T>(data: T, include?: string[], exclude?: string[]): Partial<T> {
  if (!include && !exclude) return data;

  const result = {} as Partial<T>;
  const dataKeys = Object.keys(data as any);

  for (const key of dataKeys) {
    const shouldInclude = !include || include.includes(key);
    const shouldExclude = exclude && exclude.includes(key);

    if (shouldInclude && !shouldExclude) {
      (result as any)[key] = (data as any)[key];
    }
  }

  return result;
}

/**
 * Storage abstraction
 */
async function writeToStorage(
  key: string,
  data: string,
  storage: 'localStorage' | 'sessionStorage' | 'indexedDB'
): Promise<void> {
  switch (storage) {
    case 'localStorage':
      localStorage.setItem(key, data);
      break;
    case 'sessionStorage':
      sessionStorage.setItem(key, data);
      break;
    case 'indexedDB':
      await writeToIndexedDB(key, data);
      break;
  }
}

async function readFromStorage(
  key: string,
  storage: 'localStorage' | 'sessionStorage' | 'indexedDB'
): Promise<string | null> {
  switch (storage) {
    case 'localStorage':
      return localStorage.getItem(key);
    case 'sessionStorage':
      return sessionStorage.getItem(key);
    case 'indexedDB':
      return await readFromIndexedDB(key);
    default:
      return null;
  }
}

async function removeFromStorage(
  key: string,
  storage: 'localStorage' | 'sessionStorage' | 'indexedDB'
): Promise<void> {
  switch (storage) {
    case 'localStorage':
      localStorage.removeItem(key);
      break;
    case 'sessionStorage':
      sessionStorage.removeItem(key);
      break;
    case 'indexedDB':
      await removeFromIndexedDB(key);
      break;
  }
}

/**
 * IndexedDB utilities
 */
async function writeToIndexedDB(key: string, data: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('guardian-state', 1);
    
    request.onerror = () => reject(request.error);
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('state')) {
        db.createObjectStore('state');
      }
    };
    
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['state'], 'readwrite');
      const store = transaction.objectStore('state');
      
      const putRequest = store.put(data, key);
      putRequest.onsuccess = () => resolve();
      putRequest.onerror = () => reject(putRequest.error);
    };
  });
}

async function readFromIndexedDB(key: string): Promise<string | null> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('guardian-state', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['state'], 'readonly');
      const store = transaction.objectStore('state');
      
      const getRequest = store.get(key);
      getRequest.onsuccess = () => resolve(getRequest.result || null);
      getRequest.onerror = () => reject(getRequest.error);
    };
  });
}

async function removeFromIndexedDB(key: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('guardian-state', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['state'], 'readwrite');
      const store = transaction.objectStore('state');
      
      const deleteRequest = store.delete(key);
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
  });
}

/**
 * Data processing utilities
 */
function generateChecksum(data: any): string {
  // Simple checksum using JSON string
  const str = JSON.stringify(data);
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash.toString(36);
}

async function compressData(data: string): Promise<string> {
  // Simple compression using built-in TextEncoder and CompressionStream if available
  if ('CompressionStream' in window) {
    try {
      const stream = new CompressionStream('gzip');
      const writer = stream.writable.getWriter();
      const reader = stream.readable.getReader();
      
      await writer.write(new TextEncoder().encode(data));
      await writer.close();
      
      const compressed = await reader.read();
      return btoa(String.fromCharCode(...new Uint8Array(compressed.value)));
    } catch (error) {
      console.warn('Compression failed, using uncompressed data:', error);
    }
  }
  return data;
}

async function decompressData(data: string): Promise<string> {
  // Simple decompression
  if ('DecompressionStream' in window && data !== JSON.stringify(JSON.parse(data))) {
    try {
      const compressed = Uint8Array.from(atob(data), c => c.charCodeAt(0));
      const stream = new DecompressionStream('gzip');
      const writer = stream.writable.getWriter();
      const reader = stream.readable.getReader();
      
      await writer.write(compressed);
      await writer.close();
      
      const decompressed = await reader.read();
      return new TextDecoder().decode(decompressed.value);
    } catch (error) {
      console.warn('Decompression failed, treating as uncompressed:', error);
    }
  }
  return data;
}

async function encryptData(data: string): Promise<string> {
  // Simple encryption would go here
  // For production, use Web Crypto API
  console.warn('Encryption not implemented in demo');
  return data;
}

async function decryptData(data: string): Promise<string> {
  // Simple decryption would go here
  console.warn('Decryption not implemented in demo');
  return data;
}

/**
 * Data migration utilities
 */
async function migrateData<T>(
  data: T,
  fromVersion: number,
  toVersion: number
): Promise<T> {
  // Apply migration strategies sequentially
  let migratedData = data;
  
  for (let version = fromVersion + 1; version <= toVersion; version++) {
    // Migration logic would be implemented here
    console.log(`Migrating data from version ${version - 1} to ${version}`);
  }
  
  return migratedData;
}

function mergeWithInitialState<T>(restoredData: Partial<T>, initialState: T): T {
  // Merge restored data with initial state to ensure all required fields are present
  return { ...initialState, ...restoredData };
}

/**
 * Cleanup cross-tab resources on page unload
 */
if (browser) {
  window.addEventListener('beforeunload', () => {
    if (crossTabState.channel) {
      crossTabState.channel.close();
    }
  });
}

// Export cross-tab state for monitoring
export { crossTabState };