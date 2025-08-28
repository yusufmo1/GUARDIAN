// DOM type augmentations for SvelteKit
// This file extends existing DOM types, it doesn't redeclare them

declare global {
  // Augment existing Navigator interface with optional experimental APIs
  interface Navigator {
    // Clipboard API (experimental, not available in all browsers)
    clipboard?: {
      writeText(text: string): Promise<void>;
      readText?(): Promise<string>;
    };
    
    // Network Information API (experimental)
    connection?: {
      effectiveType: string;
      downlink: number;
      rtt: number;
      saveData: boolean;
    };
  }

  // Augment existing Window interface if needed
  interface Window {
    // Add custom window properties here if needed
    // Example: gtag?: (...args: any[]) => void;
  }
}

export {};