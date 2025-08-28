// Effect tracking utility for debugging infinite loops in Svelte 5
import { browser } from '$app/environment';

interface EffectTrace {
  name: string;
  timestamp: number;
  stack: string;
  component?: string;
}

class EffectTracker {
  private traces: EffectTrace[] = [];
  private effectCounts: Map<string, number> = new Map();
  private warnThreshold = 50;
  private errorThreshold = 100;
  private tracking = false;
  
  startTracking() {
    this.tracking = true;
    this.traces = [];
    this.effectCounts.clear();
    console.log('[EffectTracker] Started tracking effects');
  }
  
  stopTracking() {
    this.tracking = false;
    console.log('[EffectTracker] Stopped tracking effects');
    this.report();
  }
  
  track(name: string, component?: string) {
    if (!this.tracking || !browser) return;
    
    // Get stack trace
    const stack = new Error().stack || '';
    const stackLines = stack.split('\n').slice(2, 5);
    const cleanStack = stackLines
      .map(line => line.trim())
      .filter(line => !line.includes('effect-tracker'))
      .join(' -> ');
    
    // Record trace
    const trace: EffectTrace = {
      name,
      timestamp: Date.now(),
      stack: cleanStack,
      component
    };
    
    this.traces.push(trace);
    if (this.traces.length > 1000) {
      this.traces = this.traces.slice(-500); // Keep last 500
    }
    
    // Update count
    const key = `${name}${component ? `:${component}` : ''}`;
    const count = (this.effectCounts.get(key) || 0) + 1;
    this.effectCounts.set(key, count);
    
    // Check for loops
    if (count === this.warnThreshold) {
      console.warn(`[EffectTracker] Effect "${key}" has run ${count} times - possible loop`, {
        recentTraces: this.getRecentTraces(key, 10)
      });
    }
    
    if (count === this.errorThreshold) {
      console.error(`[EffectTracker] Effect "${key}" has run ${count} times - INFINITE LOOP DETECTED`, {
        allCounts: Object.fromEntries(this.effectCounts),
        recentTraces: this.getRecentTraces(key, 20)
      });
      this.report();
    }
  }
  
  private getRecentTraces(effectKey: string, limit: number): EffectTrace[] {
    return this.traces
      .filter(t => {
        const key = `${t.name}${t.component ? `:${t.component}` : ''}`;
        return key === effectKey;
      })
      .slice(-limit);
  }
  
  report() {
    if (!browser) return;
    
    console.group('[EffectTracker] Effect Report');
    
    // Sort by count
    const sorted = Array.from(this.effectCounts.entries())
      .sort((a, b) => b[1] - a[1]);
    
    console.table(
      sorted.map(([name, count]) => ({
        'Effect Name': name,
        'Run Count': count,
        'Status': count > this.errorThreshold ? '🔴 LOOP' : count > this.warnThreshold ? '🟡 HIGH' : '🟢 OK'
      }))
    );
    
    // Find patterns
    const loopingEffects = sorted.filter(([_, count]) => count > this.warnThreshold);
    if (loopingEffects.length > 0) {
      console.warn('Potentially looping effects:', loopingEffects.map(([name]) => name));
    }
    
    console.groupEnd();
  }
  
  reset() {
    this.traces = [];
    this.effectCounts.clear();
  }
}

// Global instance
export const effectTracker = new EffectTracker();

// Helper function for easy tracking
export function trackEffect(name: string, component?: string) {
  effectTracker.track(name, component);
}

// Auto-start tracking in development
if (browser && import.meta.env.DEV) {
  effectTracker.startTracking();
  
  // Report on page unload
  window.addEventListener('beforeunload', () => {
    effectTracker.report();
  });
  
  // Add to window for console access
  (window as any).effectTracker = effectTracker;
}