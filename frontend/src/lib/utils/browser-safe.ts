// Browser-safe utilities for SvelteKit
// These functions ensure DOM APIs are only used in browser context

import { browser } from '$app/environment';

/**
 * Safely access window.location in SvelteKit
 * Returns current URL info or defaults for SSR
 */
export function getLocationInfo() {
  if (!browser) {
    return {
      pathname: '/',
      search: '',
      href: '',
      hostname: 'localhost'
    };
  }
  
  return {
    pathname: window.location.pathname,
    search: window.location.search, 
    href: window.location.href,
    hostname: window.location.hostname
  };
}

/**
 * Safely navigate using window.location
 * No-op during SSR
 */
export function navigateTo(url: string) {
  if (browser && typeof window !== 'undefined') {
    window.location.href = url;
  }
}

/**
 * Safely access localStorage
 * Returns null during SSR
 */
export function getLocalStorage(key: string): string | null {
  if (!browser || typeof localStorage === 'undefined') {
    return null;
  }
  return localStorage.getItem(key);
}

/**
 * Safely set localStorage
 * No-op during SSR  
 */
export function setLocalStorage(key: string, value: string): void {
  if (browser && typeof localStorage !== 'undefined') {
    localStorage.setItem(key, value);
  }
}

/**
 * Safely access navigator.userAgent
 * Returns default during SSR
 */
export function getUserAgent(): string {
  if (!browser || typeof navigator === 'undefined') {
    return 'SSR';
  }
  return navigator.userAgent;
}

/**
 * Safely check if online
 * Returns true during SSR
 */
export function isOnline(): boolean {
  if (!browser || typeof navigator === 'undefined') {
    return true;
  }
  return navigator.onLine ?? true;
}

/**
 * Safely add event listeners to window
 * No-op during SSR
 */
export function addWindowListener<K extends keyof WindowEventMap>(
  type: K,
  listener: (this: Window, ev: WindowEventMap[K]) => any,
  options?: boolean | AddEventListenerOptions
): () => void {
  if (!browser || typeof window === 'undefined') {
    return () => {}; // Return no-op cleanup function
  }
  
  window.addEventListener(type, listener, options);
  
  // Return cleanup function
  return () => {
    if (browser && typeof window !== 'undefined') {
      window.removeEventListener(type, listener, options);
    }
  };
}

/**
 * Safely copy text to clipboard
 * Falls back to alert if clipboard API not available
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (!browser) {
    return false;
  }
  
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
    
    // Fallback for older browsers
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    const success = document.execCommand('copy');
    document.body.removeChild(textarea);
    return success;
  } catch (error) {
    console.error('Failed to copy text:', error);
    return false;
  }
}