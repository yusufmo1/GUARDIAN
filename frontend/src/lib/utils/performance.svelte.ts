// GUARDIAN Performance Utilities for Svelte 5 Runes
// Optimized performance helpers for reactive computations and effects

import { browser } from '$app/environment';

// Performance metrics tracking (non-reactive for Svelte 5 compatibility)
let performanceMetrics = {
  derivedComputations: new Map<string, { count: number; totalTime: number; avgTime: number }>(),
  effectExecutions: new Map<string, { count: number; totalTime: number }>(),
  lastUpdate: Date.now()
};

/**
 * Create a simple memoized function (non-reactive)
 * For reactive memoization, use $derived directly in components
 */
export function memoized<T>(
  computeFn: () => T,
  dependencies: () => any[],
  options: {
    name?: string;
    maxAge?: number;
    maxEntries?: number;
  } = {}
): () => T {
  const { name = 'unnamed', maxAge = 30000, maxEntries = 50 } = options;
  let cache = new Map<string, { value: T; timestamp: number; hits: number }>();
  let lastKey = '';

  return () => {
    const startTime = performance.now();
    const currentDeps = dependencies();
    const key = JSON.stringify(currentDeps);
    
    // Check if cached and still valid
    if (key === lastKey && cache.has(key)) {
      const cached = cache.get(key)!;
      if (Date.now() - cached.timestamp < maxAge) {
        cached.hits++;
        if (browser) {
          updatePerformanceMetric(name, performance.now() - startTime);
        }
        return cached.value;
      }
    }
    
    // Clean up old entries
    if (cache.size >= maxEntries) {
      const entries = Array.from(cache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      const toDelete = entries.slice(0, Math.floor(maxEntries / 2));
      toDelete.forEach(([key]) => cache.delete(key));
    }
    
    // Compute new value
    const value = computeFn();
    cache.set(key, {
      value,
      timestamp: Date.now(),
      hits: 1
    });
    
    lastKey = key;
    
    if (browser) {
      updatePerformanceMetric(name, performance.now() - startTime);
    }
    
    return value;
  };
}

/**
 * Create a debounced effect
 */
export function debouncedEffect(
  effectFn: () => (() => void) | void,
  delay: number = 300,
  options: {
    name?: string;
    immediate?: boolean;
  } = {}
): { trigger: () => void; cleanup: () => void } {
  const { name = 'unnamed', immediate = false } = options;
  let timeoutId: number | null = null;
  let cleanup: (() => void) | null = null;

  const executeEffect = () => {
    const startTime = performance.now();
    
    if (cleanup) {
      cleanup();
      cleanup = null;
    }
    
    const result = effectFn();
    if (typeof result === 'function') {
      cleanup = result;
    }
    
    if (browser) {
      updateEffectMetric(name, performance.now() - startTime);
    }
  };

  // Execute immediately if requested
  if (immediate) {
    executeEffect();
  }

  // Set up debounced execution
  const trigger = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    timeoutId = window.setTimeout(executeEffect, delay);
  };

  // Return both trigger and cleanup functions
  const cleanupFn = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    if (cleanup) {
      cleanup();
      cleanup = null;
    }
  };

  return { trigger, cleanup: cleanupFn };
}

/**
 * Create a virtual list for large datasets
 */
export function createVirtualList<T>(options: {
  items: () => T[];
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}) {
  const { items, itemHeight, containerHeight, overscan = 5 } = options;
  
  let scrollTop = $state(0);
  
  const visibleRange = $derived(() => {
    const itemList = items();
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(itemList.length - 1, startIndex + visibleCount + overscan * 2);
    
    return { startIndex, endIndex, visibleCount };
  });
  
  const visibleItems = $derived(() => {
    const range = visibleRange();
    const itemList = items();
    return itemList.slice(range.startIndex, range.endIndex + 1).map((item, index) => ({
      item,
      index: range.startIndex + index,
      offsetY: (range.startIndex + index) * itemHeight
    }));
  });
  
  const totalHeight = $derived(() => items().length * itemHeight);
  
  return {
    get scrollTop() { return scrollTop; },
    set scrollTop(value: number) { scrollTop = value; },
    get visibleItems() { return visibleItems(); },
    get totalHeight() { return totalHeight(); },
    get visibleRange() { return visibleRange(); }
  };
}

/**
 * Batch multiple state updates for performance
 */
export function batchUpdates<T>(updates: () => T): T {
  // In Svelte 5, state updates are already batched automatically
  // This function exists for API compatibility
  return updates();
}

/**
 * Throttle function calls
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func.apply(null, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Debounce function calls
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout>;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(null, args), wait);
  };
}

// Performance tracking helpers
function updatePerformanceMetric(name: string, executionTime: number) {
  const metric = performanceMetrics.derivedComputations.get(name) || {
    count: 0,
    totalTime: 0,
    avgTime: 0
  };
  
  metric.count++;
  metric.totalTime += executionTime;
  metric.avgTime = metric.totalTime / metric.count;
  
  performanceMetrics.derivedComputations.set(name, metric);
  performanceMetrics.lastUpdate = Date.now();
}

function updateEffectMetric(name: string, executionTime: number) {
  const metric = performanceMetrics.effectExecutions.get(name) || {
    count: 0,
    totalTime: 0
  };
  
  metric.count++;
  metric.totalTime += executionTime;
  
  performanceMetrics.effectExecutions.set(name, metric);
  performanceMetrics.lastUpdate = Date.now();
}

/**
 * Get performance metrics for debugging
 */
export function getPerformanceMetrics() {
  return {
    derivedComputations: Object.fromEntries(performanceMetrics.derivedComputations),
    effectExecutions: Object.fromEntries(performanceMetrics.effectExecutions),
    lastUpdate: performanceMetrics.lastUpdate
  };
}

/**
 * Reset performance metrics
 */
export function resetPerformanceMetrics() {
  performanceMetrics.derivedComputations.clear();
  performanceMetrics.effectExecutions.clear();
  performanceMetrics.lastUpdate = Date.now();
}

// Export performance metrics for debugging
export { performanceMetrics };