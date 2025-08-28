// Global ambient type declarations for SvelteKit
// This file provides proper DOM type declarations that work with SvelteKit's SSR

/// <reference types="@sveltejs/kit" />

// Global DOM API types - these should be available in browser context
declare global {
  // Browser-specific APIs that may not be fully typed
  interface Window {
    // Standard DOM APIs - these should already be available via DOM lib
    // Only declare if you need to extend existing interfaces
    
    // Example custom extensions (uncomment if needed):
    // webkitSpeechRecognition?: any;
    // mozRequestAnimationFrame?: (callback: FrameRequestCallback) => number;
  }

  interface Navigator {
    // Ensure clipboard API is properly typed (it's still experimental in some browsers)
    clipboard?: {
      writeText(text: string): Promise<void>;
      readText?(): Promise<string>;
    };
    
    // Connection API (experimental)
    connection?: {
      effectiveType: string;
      downlink: number;
    };
  }

  // Custom error types for better error handling
  interface ApiError extends Error {
    status?: number;
    code?: string;
    details?: unknown;
  }

  // Global utility types
  type Nullable<T> = T | null;
  type Optional<T> = T | undefined;
  type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
  };
}

// Re-export to make this an ambient module
export {};