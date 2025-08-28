import { browser } from '$app/environment';
import { authStore } from '$lib/stores/auth.svelte';
import { documentStore } from '$lib/stores/documents.svelte';
import { analysisStore } from '$lib/stores/analysis.svelte';
import { chatStore } from '$lib/stores/chat.svelte';
import { reportStore } from '$lib/stores/report.svelte';
import { toastStore } from '$lib/stores/toast.svelte';

export interface WebSocketEvents {
  // Document events
  'document.upload.progress': (data: UploadProgressData) => void;
  'document.processing.complete': (data: DocumentProcessedData) => void;
  'document.error': (data: ErrorData) => void;

  // Analysis events
  'analysis.started': (data: AnalysisStartedData) => void;
  'analysis.progress': (data: AnalysisProgressData) => void;
  'analysis.complete': (data: AnalysisCompleteData) => void;

  // Chat events
  'chat.message.partial': (data: PartialMessageData) => void;
  'chat.message.complete': (data: CompleteMessageData) => void;

  // Session events
  'session.expiry.warning': (data: ExpiryWarningData) => void;
  'session.expired': (data: SessionExpiredData) => void;

  // Report events
  'report.generation.progress': (data: ReportProgressData) => void;
  'report.generation.complete': (data: ReportCompleteData) => void;

  // System events
  'system.notification': (data: SystemNotificationData) => void;
  'error.critical': (data: CriticalErrorData) => void;
}

export interface UploadProgressData {
  documentId: string;
  progress: number;
  stage: 'uploading' | 'processing' | 'embedding' | 'indexing';
  totalBytes?: number;
  loadedBytes?: number;
}

export interface DocumentProcessedData {
  documentId: string;
  status: 'completed' | 'failed';
  chunks?: number;
  embeddings?: number;
  error?: string;
}

export interface ErrorData {
  documentId: string;
  error: string;
  code: string;
  recoverable: boolean;
}

export interface AnalysisStartedData {
  analysisId: string;
  documentId: string;
  estimatedDuration: number;
}

export interface AnalysisProgressData {
  analysisId: string;
  progress: number;
  stage: 'search' | 'llm_analysis' | 'compliance_check' | 'report_generation';
  currentStep?: string;
}

export interface AnalysisCompleteData {
  analysisId: string;
  result: {
    complianceScore: number;
    findings: Array<{
      section: string;
      status: 'compliant' | 'non_compliant' | 'warning';
      description: string;
    }>;
  };
}

export interface PartialMessageData {
  sessionId: string;
  messageId: string;
  content: string;
  isComplete: boolean;
}

export interface CompleteMessageData {
  sessionId: string;
  messageId: string;
  content: string;
  timestamp: string;
}

export interface ExpiryWarningData {
  expiresAt: string;
  minutesRemaining: number;
}

export interface SessionExpiredData {
  reason: 'timeout' | 'logout' | 'token_invalid';
  redirectUrl?: string;
}

export interface ReportProgressData {
  reportId: string;
  progress: number;
  stage: 'generating' | 'rendering' | 'saving';
}

export interface ReportCompleteData {
  reportId: string;
  downloadUrl: string;
  filename: string;
  size: number;
}

export interface SystemNotificationData {
  type: 'info' | 'warning' | 'error';
  title: string;
  message: string;
  persistent?: boolean;
}

export interface CriticalErrorData {
  code: string;
  message: string;
  action: 'reload' | 'logout' | 'contact_support';
}

export type WebSocketEventType = keyof WebSocketEvents;

interface QueuedMessage {
  type: WebSocketEventType;
  data: any;
  timestamp: number;
}

class GuardianWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private heartbeatTimeout: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isAuthenticated = false;
  private messageQueue: QueuedMessage[] = [];
  private eventHandlers = new Map<WebSocketEventType, Set<Function>>();

  constructor() {
    this.url = this.getWebSocketUrl();
  }

  private getWebSocketUrl(): string {
    if (!browser) return '';
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const port = '5051'; // Backend WebSocket port
    
    return `${protocol}//${host}:${port}/ws`;
  }

  async connect(): Promise<void> {
    if (!browser || this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return;
    }

    const sessionToken = authStore.sessionToken;
    if (!sessionToken) {
      console.warn('Cannot connect WebSocket: No session token');
      return;
    }

    this.isConnecting = true;

    try {
      console.log('Connecting to WebSocket...', this.url);
      
      this.ws = new WebSocket(`${this.url}?token=${encodeURIComponent(sessionToken)}`);
      
      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  private handleOpen(event: Event): void {
    console.log('WebSocket connected successfully');
    this.isConnecting = false;
    this.isAuthenticated = true;
    this.reconnectAttempts = 0;
    
    this.startHeartbeat();
    this.processMessageQueue();
    
    toastStore.success('Real-time connection established');
  }

  private handleMessage(event: MessageEvent): void {
    try {
      const message = JSON.parse(event.data);
      
      if (message.type === 'heartbeat') {
        this.handleHeartbeat();
        return;
      }

      if (message.type === 'auth.success') {
        this.isAuthenticated = true;
        console.log('WebSocket authenticated successfully');
        return;
      }

      if (message.type === 'auth.failed') {
        console.error('WebSocket authentication failed');
        this.disconnect();
        return;
      }

      // Handle application events
      this.handleApplicationEvent(message.type, message.data);

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  private handleApplicationEvent(type: WebSocketEventType, data: any): void {
    console.log(`Received event: ${type}`, data);

    // Update stores based on event type
    switch (type) {
      case 'document.upload.progress':
        this.handleDocumentUploadProgress(data);
        break;
      
      case 'document.processing.complete':
        this.handleDocumentProcessingComplete(data);
        break;
      
      case 'analysis.started':
        this.handleAnalysisStarted(data);
        break;
      
      case 'analysis.progress':
        this.handleAnalysisProgress(data);
        break;
      
      case 'analysis.complete':
        this.handleAnalysisComplete(data);
        break;
      
      case 'chat.message.partial':
        this.handleChatMessagePartial(data);
        break;
      
      case 'chat.message.complete':
        this.handleChatMessageComplete(data);
        break;
      
      case 'report.generation.progress':
        this.handleReportProgress(data);
        break;
      
      case 'report.generation.complete':
        this.handleReportComplete(data);
        break;
      
      case 'session.expiry.warning':
        this.handleSessionExpiryWarning(data);
        break;
      
      case 'session.expired':
        this.handleSessionExpired(data);
        break;
      
      case 'system.notification':
        this.handleSystemNotification(data);
        break;
      
      case 'error.critical':
        this.handleCriticalError(data);
        break;
    }

    // Trigger custom event handlers
    const handlers = this.eventHandlers.get(type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${type}:`, error);
        }
      });
    }
  }

  private handleDocumentUploadProgress(data: UploadProgressData): void {
    // Update document store with real-time progress
    documentStore.updateUploadProgress(data.documentId, data.progress, data.stage);
  }

  private handleDocumentProcessingComplete(data: DocumentProcessedData): void {
    if (data.status === 'completed') {
      documentStore.markDocumentProcessed(data.documentId);
      toastStore.success('Document processing completed!');
    } else {
      documentStore.markDocumentError(data.documentId, data.error || 'Processing failed');
      toastStore.error(`Document processing failed: ${data.error}`);
    }
  }

  private handleAnalysisStarted(data: AnalysisStartedData): void {
    analysisStore.setAnalysisProgress(data.analysisId, 0, 'search');
    toastStore.info('Analysis started...');
  }

  private handleAnalysisProgress(data: AnalysisProgressData): void {
    analysisStore.setAnalysisProgress(data.analysisId, data.progress, data.stage);
  }

  private handleAnalysisComplete(data: AnalysisCompleteData): void {
    analysisStore.completeAnalysis(data.analysisId, data.result);
    toastStore.success('Analysis completed!');
  }

  private handleChatMessagePartial(data: PartialMessageData): void {
    chatStore.updateStreamingMessage(data.sessionId, data.messageId, data.content);
  }

  private handleChatMessageComplete(data: CompleteMessageData): void {
    chatStore.completeStreamingMessage(data.sessionId, data.messageId, data.content);
  }

  private handleReportProgress(data: ReportProgressData): void {
    // reportStore.updateGenerationProgress(data.reportId, data.progress, data.stage);
  }

  private handleReportComplete(data: ReportCompleteData): void {
    toastStore.success('Report generated successfully!');
    reportStore.refreshReports();
  }

  private handleSessionExpiryWarning(data: ExpiryWarningData): void {
    const message = `Session expires in ${data.minutesRemaining} minutes`;
    toastStore.warning(message, 30000); // Show for 30 seconds
  }

  private handleSessionExpired(data: SessionExpiredData): void {
    toastStore.error('Session expired. Please sign in again.');
    authStore.logout();
    
    if (data.redirectUrl) {
      window.location.href = data.redirectUrl;
    }
  }

  private handleSystemNotification(data: SystemNotificationData): void {
    const duration = data.persistent ? 0 : 5000;
    
    switch (data.type) {
      case 'info':
        toastStore.info(data.message, duration);
        break;
      case 'warning':
        toastStore.warning(data.message, duration);
        break;
      case 'error':
        toastStore.error(data.message, duration);
        break;
    }
  }

  private handleCriticalError(data: CriticalErrorData): void {
    toastStore.error(`Critical error: ${data.message}`, 0); // Persistent
    
    switch (data.action) {
      case 'reload':
        setTimeout(() => window.location.reload(), 3000);
        break;
      case 'logout':
        authStore.logout();
        break;
      case 'contact_support':
        // Could open support chat or redirect to support page
        break;
    }
  }

  private handleClose(event: CloseEvent): void {
    console.log('WebSocket connection closed:', event.code, event.reason);
    this.isConnecting = false;
    this.isAuthenticated = false;
    this.stopHeartbeat();
    
    if (event.code !== 1000) { // Not normal closure
      toastStore.warning('Connection lost. Attempting to reconnect...');
      this.scheduleReconnect();
    }
  }

  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.isConnecting = false;
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      toastStore.error('Unable to establish real-time connection');
      return;
    }

    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    setTimeout(() => {
      if (authStore.isAuthenticated) {
        this.connect();
      }
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }));
        
        // Set timeout for heartbeat response
        this.heartbeatTimeout = setTimeout(() => {
          console.warn('Heartbeat timeout - closing connection');
          this.ws?.close();
        }, 5000);
      }
    }, 30000); // Send heartbeat every 30 seconds
  }

  private handleHeartbeat(): void {
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout);
      this.heartbeatTimeout = null;
    }
  }

  private processMessageQueue(): void {
    if (!this.isAuthenticated) return;
    
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        // Process queued messages if still relevant (not too old)
        const age = Date.now() - message.timestamp;
        if (age < 60000) { // Messages older than 1 minute are discarded
          this.handleApplicationEvent(message.type, message.data);
        }
      }
    }
  }

  // Public API
  disconnect(): void {
    console.log('Disconnecting WebSocket...');
    this.stopHeartbeat();
    
    if (this.ws) {
      this.ws.close(1000, 'Normal closure');
      this.ws = null;
    }
    
    this.isConnecting = false;
    this.isAuthenticated = false;
    this.reconnectAttempts = 0;
  }

  on<T extends WebSocketEventType>(event: T, handler: WebSocketEvents[T]): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  off<T extends WebSocketEventType>(event: T, handler: WebSocketEvents[T]): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  get isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN && this.isAuthenticated;
  }

  get connectionState(): string {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return this.isAuthenticated ? 'authenticated' : 'connected';
      case WebSocket.CLOSING:
        return 'closing';
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'unknown';
    }
  }
}

// Export singleton instance
export const webSocketClient = new GuardianWebSocketClient();

// DISABLED: Auto-connect polling was causing 1-second reactive loops and infinite effects
// TODO: Implement event-driven WebSocket connection management after fixing reactive loops
// The WebSocket client can still be used manually via webSocketClient.connect()
if (browser) {
  console.log('WebSocket auto-connection disabled to prevent reactive loops');
  console.log('Use webSocketClient.connect() manually when needed');
}