// GUARDIAN Frontend Utility Functions

import type { ComplianceStatus, ComplianceSeverity } from '$lib/types';

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
}

export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  
  return formatDate(date);
}

export function getComplianceColor(status: ComplianceStatus): string {
  switch (status) {
    case 'compliant':
      return 'var(--color-success-600)';
    case 'non-compliant':
      return 'var(--color-error-600)';
    case 'partial':
      return 'var(--color-warning-600)';
    case 'needs-review':
      return 'var(--color-gray-600)';
    default:
      return 'var(--color-gray-600)';
  }
}

export function getSeverityColor(severity: ComplianceSeverity): string {
  switch (severity) {
    case 'critical':
      return 'var(--color-error-600)';
    case 'major':
      return 'var(--color-error-500)';
    case 'minor':
      return 'var(--color-warning-500)';
    case 'info':
      return 'var(--color-primary-500)';
    default:
      return 'var(--color-gray-500)';
  }
}

export function calculateComplianceScore(findings: Array<{ status: ComplianceStatus; severity: ComplianceSeverity }>): number {
  if (findings.length === 0) return 0;

  let totalWeight = 0;
  let compliantWeight = 0;

  findings.forEach(finding => {
    let weight = 1;
    
    // Weight by severity
    switch (finding.severity) {
      case 'critical':
        weight = 4;
        break;
      case 'major':
        weight = 3;
        break;
      case 'minor':
        weight = 2;
        break;
      case 'info':
        weight = 1;
        break;
    }

    totalWeight += weight;

    // Add to compliant weight based on status
    switch (finding.status) {
      case 'compliant':
        compliantWeight += weight;
        break;
      case 'partial':
        compliantWeight += weight * 0.5;
        break;
      case 'non-compliant':
      case 'needs-review':
        // No weight added
        break;
    }
  });

  return Math.round((compliantWeight / totalWeight) * 100);
}

export function getComplianceScoreClass(score: number): string {
  if (score >= 80) return 'high';
  if (score >= 60) return 'medium';
  return 'low';
}

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

export function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function cn(...classes: (string | undefined | null | false)[]): string {
  return classes.filter(Boolean).join(' ');
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

export function isValidPDF(file: File): boolean {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
}

export function validateFileSize(file: File, maxSizeInMB: number = 50): boolean {
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;
  return file.size <= maxSizeInBytes;
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

export function highlightText(text: string, query: string): string {
  if (!query) return text;
  
  const regex = new RegExp(`(${query})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function copyToClipboard(text: string): Promise<void> {
  if (navigator.clipboard) {
    return navigator.clipboard.writeText(text);
  }
  
  // Fallback for older browsers
  const textArea = document.createElement('textarea');
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.select();
  document.execCommand('copy');
  document.body.removeChild(textArea);
  return Promise.resolve();
}

export function downloadFile(content: string, filename: string, contentType: string = 'text/plain'): void {
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function parseErrorMessage(error: unknown): string {
  if (typeof error === 'string') return error;
  if (error instanceof Error) return error.message;
  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message);
  }
  return 'An unknown error occurred';
}