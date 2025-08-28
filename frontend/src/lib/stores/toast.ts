import { writable } from 'svelte/store';
import type { ToastMessage } from '$lib/types';
import { generateId } from '$lib/utils';
import { TOAST_DURATIONS } from '$lib/constants';

function createToastStore() {
  const { subscribe, set, update } = writable<ToastMessage[]>([]);

  return {
    subscribe,
    
    add: (toast: Omit<ToastMessage, 'id' | 'timestamp'>) => {
      const newToast: ToastMessage = {
        ...toast,
        id: generateId(),
        timestamp: Date.now()
      };
      
      update(toasts => [...toasts, newToast]);
      
      // Auto-remove toast after duration
      const duration = toast.duration || TOAST_DURATIONS[toast.type.toUpperCase() as keyof typeof TOAST_DURATIONS] || TOAST_DURATIONS.INFO;
      
      setTimeout(() => {
        update(toasts => toasts.filter(t => t.id !== newToast.id));
      }, duration);
      
      return newToast.id;
    },
    
    remove: (id: string) =>
      update(toasts => toasts.filter(toast => toast.id !== id)),
    
    clear: () => set([]),
    
    // Convenience methods
    success: (title: string, message?: string, duration?: number) =>
      update(toasts => {
        const newToast: ToastMessage = {
          id: generateId(),
          type: 'success',
          title,
          message,
          duration,
          timestamp: Date.now()
        };
        
        const finalDuration = duration || TOAST_DURATIONS.SUCCESS;
        setTimeout(() => {
          update(toasts => toasts.filter(t => t.id !== newToast.id));
        }, finalDuration);
        
        return [...toasts, newToast];
      }),
    
    error: (title: string, message?: string, duration?: number) =>
      update(toasts => {
        const newToast: ToastMessage = {
          id: generateId(),
          type: 'error',
          title,
          message,
          duration,
          timestamp: Date.now()
        };
        
        const finalDuration = duration || TOAST_DURATIONS.ERROR;
        setTimeout(() => {
          update(toasts => toasts.filter(t => t.id !== newToast.id));
        }, finalDuration);
        
        return [...toasts, newToast];
      }),
    
    warning: (title: string, message?: string, duration?: number) =>
      update(toasts => {
        const newToast: ToastMessage = {
          id: generateId(),
          type: 'warning',
          title,
          message,
          duration,
          timestamp: Date.now()
        };
        
        const finalDuration = duration || TOAST_DURATIONS.WARNING;
        setTimeout(() => {
          update(toasts => toasts.filter(t => t.id !== newToast.id));
        }, finalDuration);
        
        return [...toasts, newToast];
      }),
    
    info: (title: string, message?: string, duration?: number) =>
      update(toasts => {
        const newToast: ToastMessage = {
          id: generateId(),
          type: 'info',
          title,
          message,
          duration,
          timestamp: Date.now()
        };
        
        const finalDuration = duration || TOAST_DURATIONS.INFO;
        setTimeout(() => {
          update(toasts => toasts.filter(t => t.id !== newToast.id));
        }, finalDuration);
        
        return [...toasts, newToast];
      })
  };
}

export const toastStore = createToastStore();