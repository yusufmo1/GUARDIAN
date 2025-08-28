export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  timestamp: number;
}

// Generate unique IDs for toasts
function generateId(): string {
  return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Default duration for auto-removal (in milliseconds)
const DEFAULT_DURATION = 5000;

// Create reactive toast state using Svelte 5 runes
let toasts = $state<ToastMessage[]>([]);

// Derived computations for toast management
export function toastCount() { return toasts.length; }
export function hasToasts() { return toasts.length > 0; }
export function latestToast() { return toasts[toasts.length - 1]; }

// Note: Toast auto-removal effect moved to +layout.svelte
// Store-level effects are not allowed in Svelte 5

// Toast store interface - replaces the old factory pattern
export const toastStore = {
  // Getter for reactive access to toasts
  get toasts(): ToastMessage[] {
    return toasts;
  },
  
  // Add a new toast
  add(toast: Omit<ToastMessage, 'id' | 'timestamp'>): ToastMessage {
    const newToast: ToastMessage = {
      ...toast,
      id: generateId(),
      timestamp: Date.now(),
      duration: toast.duration ?? DEFAULT_DURATION
    };
    
    toasts = [...toasts, newToast];
    return newToast;
  },
  
  // Remove a specific toast by ID
  remove(id: string): void {
    toasts = toasts.filter(t => t.id !== id);
  },
  
  // Clear all toasts
  clear(): void {
    toasts = [];
  },
  
  // Convenience methods for different toast types
  success(title: string, message?: string, duration?: number): ToastMessage {
    return this.add({
      type: 'success',
      title,
      message,
      duration
    });
  },
  
  error(title: string, message?: string, duration?: number): ToastMessage {
    return this.add({
      type: 'error',
      title,
      message,
      duration: duration ?? 8000 // Errors stay longer by default
    });
  },
  
  warning(title: string, message?: string, duration?: number): ToastMessage {
    return this.add({
      type: 'warning',
      title,
      message,
      duration: duration ?? 7000 // Warnings stay a bit longer
    });
  },
  
  info(title: string, message?: string, duration?: number): ToastMessage {
    return this.add({
      type: 'info',
      title,
      message,
      duration
    });
  },
  
  // Update an existing toast
  update(id: string, updates: Partial<Omit<ToastMessage, 'id' | 'timestamp'>>): void {
    toasts = toasts.map(toast => 
      toast.id === id 
        ? { ...toast, ...updates }
        : toast
    );
  },
  
  // Get a specific toast by ID
  getById(id: string): ToastMessage | undefined {
    return toasts.find(t => t.id === id);
  },
  
  // Check if a toast exists
  exists(id: string): boolean {
    return toasts.some(t => t.id === id);
  }
};