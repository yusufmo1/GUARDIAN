import DOMPurify from 'dompurify';
import { browser } from '$app/environment';

/**
 * Security utility functions for GUARDIAN frontend
 * Implements Frontend Data Flow Requirements for security measures
 */

// Configure DOMPurify for safe HTML sanitization
const configureDOMPurify = () => {
  if (!browser) return;
  
  // Configure allowed tags and attributes
  DOMPurify.setConfig({
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'blockquote', 'code', 'pre'],
    ALLOWED_ATTR: ['class'],
    ALLOW_DATA_ATTR: false,
    FORBID_SCRIPT: true,
    FORBID_TAGS: ['script', 'object', 'embed', 'form', 'input', 'button'],
    FORBID_ATTR: ['onclick', 'onerror', 'onload', 'onmouseover', 'onfocus', 'onblur'],
    USE_PROFILES: { html: true }
  });
};

// Initialize DOMPurify configuration
if (browser) {
  configureDOMPurify();
}

/**
 * Sanitizes HTML content to prevent XSS attacks
 * @param html - Raw HTML string to sanitize
 * @returns Sanitized HTML string safe for rendering
 */
export function sanitizeHtml(html: string): string {
  if (!browser) return html;
  
  return DOMPurify.sanitize(html, {
    RETURN_DOM: false,
    RETURN_DOM_FRAGMENT: false,
    RETURN_DOM_IMPORT: false
  });
}

/**
 * Sanitizes plain text and converts newlines to safe HTML
 * @param text - Plain text to sanitize
 * @returns Sanitized HTML with safe line breaks
 */
export function sanitizeText(text: string): string {
  if (!browser) return text;
  
  // Escape HTML characters first
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
  
  // Convert newlines to <br> tags and sanitize
  const withBreaks = escaped.replace(/\n/g, '<br>');
  
  return sanitizeHtml(withBreaks);
}

/**
 * Input validation requirements from Frontend Data Flow Requirements
 */
export const ValidationRequirements = {
  fileUpload: {
    maxSize: 50 * 1024 * 1024, // 50MB
    allowedTypes: ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    allowedExtensions: ['.pdf', '.txt', '.docx'],
    scanForMalware: false // Client-side scanning not practical
  },
  
  userInput: {
    sanitizeHtml: true,
    maxLength: 10000, // 10KB maximum input
    allowedCharacters: /^[\w\s\p{P}\p{S}\p{N}\p{L}]*$/u // Unicode letters, numbers, punctuation, symbols, whitespace
  },
  
  apiResponses: {
    validateSchema: true,
    sanitizeContent: true,
    timeoutMs: 30000 // 30 seconds
  }
} as const;

/**
 * Validates user input according to security requirements
 * @param input - User input to validate
 * @param options - Validation options
 * @returns Validation result with sanitized input
 */
export interface InputValidationOptions {
  maxLength?: number;
  allowedCharacters?: RegExp;
  sanitizeHtml?: boolean;
}

export interface ValidationResult {
  isValid: boolean;
  sanitizedInput: string;
  errors: string[];
}

export function validateUserInput(
  input: string, 
  options: InputValidationOptions = {}
): ValidationResult {
  const config = {
    maxLength: options.maxLength || ValidationRequirements.userInput.maxLength,
    allowedCharacters: options.allowedCharacters || ValidationRequirements.userInput.allowedCharacters,
    sanitizeHtml: options.sanitizeHtml !== false
  };
  
  const errors: string[] = [];
  let sanitizedInput = input;
  
  // Length validation
  if (input.length > config.maxLength) {
    errors.push(`Input exceeds maximum length of ${config.maxLength} characters`);
  }
  
  // Character validation
  if (!config.allowedCharacters.test(input)) {
    errors.push('Input contains invalid characters');
  }
  
  // HTML sanitization
  if (config.sanitizeHtml) {
    sanitizedInput = sanitizeText(input);
  }
  
  return {
    isValid: errors.length === 0,
    sanitizedInput,
    errors
  };
}

/**
 * Validates file upload according to security requirements
 * @param file - File to validate
 * @returns Validation result
 */
export interface FileValidationResult {
  isValid: boolean;
  errors: string[];
}

export function validateFileUpload(file: File): FileValidationResult {
  const errors: string[] = [];
  const config = ValidationRequirements.fileUpload;
  
  // Size validation
  if (file.size > config.maxSize) {
    errors.push(`File size ${formatFileSize(file.size)} exceeds maximum of ${formatFileSize(config.maxSize)}`);
  }
  
  // Type validation
  const isValidType = config.allowedTypes.includes(file.type);
  const extension = `.${file.name.split('.').pop()?.toLowerCase()}`;
  const isValidExtension = config.allowedExtensions.includes(extension);
  
  if (!isValidType && !isValidExtension) {
    errors.push(`File type "${file.type}" is not allowed. Allowed types: ${config.allowedExtensions.join(', ')}`);
  }
  
  // Basic filename validation
  if (file.name.length > 255) {
    errors.push('Filename too long (maximum 255 characters)');
  }
  
  // Check for suspicious filenames
  const suspiciousPatterns = [/\.exe$/i, /\.bat$/i, /\.cmd$/i, /\.scr$/i, /\.vbs$/i, /\.js$/i];
  if (suspiciousPatterns.some(pattern => pattern.test(file.name))) {
    errors.push('Suspicious file type detected');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
}

/**
 * Formats file size in human-readable format
 * @param bytes - File size in bytes
 * @returns Formatted file size string
 */
function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB'];
  let size = bytes;
  let unitIndex = 0;
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

/**
 * Generates secure random string for CSRF tokens and nonces
 * @param length - Length of random string
 * @returns Base64 encoded random string
 */
export function generateSecureRandom(length: number = 32): string {
  if (!browser) return '';
  
  const array = new Uint8Array(length);
  crypto.getRandomValues(array);
  
  return btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}

/**
 * Encrypts sensitive data before storing in localStorage
 * @param data - Data to encrypt
 * @param key - Encryption key
 * @returns Encrypted data string
 */
export async function encryptForStorage(data: string, key: string): Promise<string> {
  if (!browser) return data;
  
  try {
    // Use Web Crypto API for encryption
    const encoder = new TextEncoder();
    const keyData = encoder.encode(key.padEnd(32, '0').slice(0, 32));
    
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM' },
      false,
      ['encrypt']
    );
    
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const dataBuffer = encoder.encode(data);
    
    const encrypted = await crypto.subtle.encrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      dataBuffer
    );
    
    // Combine IV and encrypted data
    const combined = new Uint8Array(iv.length + encrypted.byteLength);
    combined.set(iv);
    combined.set(new Uint8Array(encrypted), iv.length);
    
    return btoa(String.fromCharCode(...combined));
  } catch (error) {
    console.warn('Encryption failed, storing as plain text:', error);
    return data;
  }
}

/**
 * Decrypts data from localStorage
 * @param encryptedData - Encrypted data string
 * @param key - Decryption key
 * @returns Decrypted data string
 */
export async function decryptFromStorage(encryptedData: string, key: string): Promise<string> {
  if (!browser) return encryptedData;
  
  try {
    const combined = new Uint8Array(
      atob(encryptedData).split('').map(char => char.charCodeAt(0))
    );
    
    const iv = combined.slice(0, 12);
    const encrypted = combined.slice(12);
    
    const encoder = new TextEncoder();
    const keyData = encoder.encode(key.padEnd(32, '0').slice(0, 32));
    
    const cryptoKey = await crypto.subtle.importKey(
      'raw',
      keyData,
      { name: 'AES-GCM' },
      false,
      ['decrypt']
    );
    
    const decrypted = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv },
      cryptoKey,
      encrypted
    );
    
    return new TextDecoder().decode(decrypted);
  } catch (error) {
    console.warn('Decryption failed, returning as plain text:', error);
    return encryptedData;
  }
}

/**
 * Validates API response integrity
 * @param response - API response to validate
 * @returns True if response is valid
 */
export function validateApiResponse(response: any): boolean {
  // Basic structure validation
  if (typeof response !== 'object' || response === null) {
    return false;
  }
  
  // Check for XSS in response data
  const jsonString = JSON.stringify(response);
  const xssPatterns = [
    /<script[\s\S]*?>[\s\S]*?<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /<iframe[\s\S]*?>/gi
  ];
  
  return !xssPatterns.some(pattern => pattern.test(jsonString));
}

/**
 * Content Security Policy configuration
 */
export const CSP_CONFIG = {
  'default-src': "'self'",
  'script-src': "'self' 'unsafe-inline'", // Allow inline scripts for Svelte
  'style-src': "'self' 'unsafe-inline'", // Allow inline styles
  'img-src': "'self' data: https:",
  'connect-src': "'self' ws: wss:",
  'font-src': "'self'",
  'object-src': "'none'",
  'base-uri': "'self'",
  'form-action': "'self'"
};

/**
 * Security headers configuration
 */
export const SECURITY_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
};

/**
 * Rate limiting for client-side requests
 */
class RateLimiter {
  private requestCounts = new Map<string, { count: number; resetTime: number }>();
  
  isAllowed(key: string, maxRequests: number = 100, windowMs: number = 60000): boolean {
    const now = Date.now();
    const record = this.requestCounts.get(key);
    
    if (!record || now > record.resetTime) {
      this.requestCounts.set(key, { count: 1, resetTime: now + windowMs });
      return true;
    }
    
    if (record.count >= maxRequests) {
      return false;
    }
    
    record.count++;
    return true;
  }
  
  reset(key: string): void {
    this.requestCounts.delete(key);
  }
}

export const rateLimiter = new RateLimiter();