import type { ChatSession, ChatMessage } from '$lib/types';
import { generateId } from '$lib/utils';
import { CHAT_CONFIG } from '$lib/constants';
import { 
  memoized, 
  debouncedEffect, 
  createVirtualList,
  getPerformanceMetrics 
} from '$lib/utils/performance.svelte';
import { 
  globalErrorBoundary, 
  withRetry, 
  ErrorType,
  ErrorSeverity,
  createError 
} from '$lib/utils/error-handling.svelte';
import { persistedState } from '$lib/utils/state-persistence.svelte';

// Create reactive chat state using Svelte 5 runes
let sessions = $state<ChatSession[]>([]);
let currentSession = $state<ChatSession | null>(null);
let streaming = $state(false);
let currentUserId = $state<string | null>(null);

// State persistence for chat sessions
const persistedChatState = persistedState(
  { sessions: [], currentSessionId: null as string | null },
  {
    key: 'guardian-chat-state',
    version: 1,
    storage: 'localStorage',
    debounceMs: 1000,
    exclude: ['streaming'], // Don't persist streaming state
    crossTab: false // DISABLED: Cross-tab sync was causing infinite reactive loops
  }
);

// Note: Chat persistence moved to component initialization
// Store-level effects are not allowed in Svelte 5

// Derived computations for chat management
export function sessionCount() { return sessions.length; }

export function currentMessages() { return currentSession?.messages || []; }

export function lastMessage() {
  const messages = currentMessages();
  return messages[messages.length - 1] || null;
}

export function messageCount() { return currentMessages().length; }

export function hasActiveSession() { return currentSession !== null; }

export function canSendMessage() {
  return currentSession !== null && 
    !streaming &&
    currentMessages().length < CHAT_CONFIG.MAX_MESSAGES;
}

// Additional derived computations for enhanced UX
export function hasSessions() { return sessions.length > 0; }
export function isStreaming() { return streaming; }
export function hasMessages() { return currentMessages().length > 0; }
export function currentSessionId() { return currentSession?.id || null; }

// Advanced derived computations with memoization for performance
const sessionsByDateMemo = memoized(
  () => {
    return [...sessions].sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    );
  },
  () => [sessions.length, sessions.map(s => s.updatedAt.getTime()).join(',')],
  { name: 'chat-sessions-by-date', maxAge: 5000 }
);

const recentSessionsMemo = memoized(
  () => {
    const sortedSessions = sessionsByDateMemo();
    return sortedSessions.slice(0, 10);
  },
  () => [sessions.length],
  { name: 'chat-recent-sessions', maxAge: 5000 }
);

export function sessionsByDate() { return sessionsByDateMemo(); }
export function recentSessions() { return recentSessionsMemo(); }

const messagesByRoleMemo = memoized(
  () => {
    const messages = currentMessages();
    return {
      user: messages.filter(msg => msg.role === 'user'),
      assistant: messages.filter(msg => msg.role === 'assistant')
    };
  },
  () => [currentMessages().length, currentMessages().map(m => m.role).join(',')],
  { name: 'chat-messages-by-role', maxAge: 2000 }
);

const chatStatsMemo = memoized(
  () => {
    return {
      totalSessions: sessions.length,
      totalMessages: sessions.reduce((sum, session) => sum + session.messages.length, 0),
      currentSessionMessages: currentMessages().length,
      isAtMessageLimit: currentMessages().length >= CHAT_CONFIG.MAX_MESSAGES,
      canAcceptMoreMessages: currentMessages().length < CHAT_CONFIG.MAX_MESSAGES
    };
  },
  () => [sessions.length, sessions.map(s => s.messages.length).join(',')],
  { name: 'chat-stats', maxAge: 3000 }
);

export function messagesByRole() { return messagesByRoleMemo(); }
export function chatStats() { return chatStatsMemo(); }

export function conversationContext() {
  if (!currentSession || currentMessages().length === 0) return null;
  
  return {
    sessionId: currentSession.id,
    messageCount: currentMessages().length,
    lastActivity: currentSession.updatedAt,
    hasContext: currentMessages().some(msg => msg.documentContext || msg.analysisContext)
  };
}

// Virtual list support for large message lists
export function createMessageVirtualList(containerHeight: number = 400) {
  return createVirtualList(
    () => currentMessages,
    {
      itemHeight: 80, // Approximate message height
      containerHeight,
      overscan: 5,
      name: 'chat-messages'
    }
  );
}

// Performance monitoring
export function getChatPerformanceMetrics() {
  return getPerformanceMetrics();
}

// Note: User isolation moved to component initialization
// Store-level effects are not allowed in Svelte 5

// Helper function to update session in sessions array
function updateSessionInArray(sessionId: string, updater: (session: ChatSession) => ChatSession): void {
  sessions = sessions.map(session =>
    session.id === sessionId ? updater(session) : session
  );
}

// Helper function to update current session if it matches ID
function updateCurrentSessionIfMatches(sessionId: string, updater: (session: ChatSession) => ChatSession): void {
  if (currentSession?.id === sessionId) {
    currentSession = updater(currentSession);
  }
}

// Helper function to trim messages if exceeding limit
function trimMessagesIfNeeded(session: ChatSession): ChatSession {
  if (session.messages.length > CHAT_CONFIG.MAX_MESSAGES) {
    return {
      ...session,
      messages: session.messages.slice(-CHAT_CONFIG.MAX_MESSAGES)
    };
  }
  return session;
}

// Chat store interface - maintains compatibility with existing code
export const chatStore = {
  // Getters for reactive access
  get sessions(): ChatSession[] {
    return sessions;
  },
  
  get currentSession(): ChatSession | null {
    return currentSession;
  },
  
  get streaming(): boolean {
    return streaming;
  },
  
  get currentUserId(): string | null {
    return currentUserId;
  },
  
  // Session management
  createSession(): string {
    const newSession: ChatSession = {
      id: generateId(),
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    sessions = [...sessions, newSession];
    currentSession = newSession;
    
    return newSession.id;
  },
  
  selectSession(sessionId: string): void {
    const session = sessions.find(s => s.id === sessionId);
    currentSession = session || null;
  },
  
  removeSession(sessionId: string): void {
    sessions = sessions.filter(session => session.id !== sessionId);
    
    // Clear current session if the removed session was current
    if (currentSession?.id === sessionId) {
      currentSession = null;
    }
  },
  
  updateSession(sessionId: string, updates: Partial<Omit<ChatSession, 'id'>>): void {
    const updater = (session: ChatSession) => ({
      ...session,
      ...updates,
      updatedAt: new Date()
    });
    
    updateSessionInArray(sessionId, updater);
    updateCurrentSessionIfMatches(sessionId, updater);
  },
  
  // Message management with error handling and debouncing
  addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>): string {
    try {
      if (!currentSession) {
        const error = createError(
          'No active session to add message to',
          ErrorType.VALIDATION,
          ErrorSeverity.MEDIUM
        );
        globalErrorBoundary.addError(error);
        throw new Error(error.message);
      }
      
      // Validate message content
      if (!message.content?.trim()) {
        const error = createError(
          'Message content cannot be empty',
          ErrorType.VALIDATION,
          ErrorSeverity.LOW
        );
        globalErrorBoundary.addError(error);
        throw new Error(error.message);
      }
      
      const newMessage: ChatMessage = {
        ...message,
        id: generateId(),
        timestamp: new Date()
      };
      
      const updater = (session: ChatSession) => {
        const updatedSession = {
          ...session,
          messages: [...session.messages, newMessage],
          updatedAt: new Date()
        };
        
        // Trim messages if exceeding limit
        return trimMessagesIfNeeded(updatedSession);
      };
      
      updateSessionInArray(currentSession.id, updater);
      updateCurrentSessionIfMatches(currentSession.id, updater);
      
      return newMessage.id;
    } catch (error) {
      console.error('Failed to add message:', error);
      globalErrorBoundary.addError(createError(
        `Failed to add message: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.MEDIUM,
        { originalError: error, messageContent: message.content }
      ));
      throw error;
    }
  },
  
  updateMessage(messageId: string, updates: Partial<ChatMessage>): void {
    if (!currentSession) return;
    
    const updater = (session: ChatSession) => ({
      ...session,
      messages: session.messages.map(message =>
        message.id === messageId ? { ...message, ...updates } : message
      ),
      updatedAt: new Date()
    });
    
    updateSessionInArray(currentSession.id, updater);
    updateCurrentSessionIfMatches(currentSession.id, updater);
  },
  
  removeMessage(messageId: string): void {
    if (!currentSession) return;
    
    const updater = (session: ChatSession) => ({
      ...session,
      messages: session.messages.filter(message => message.id !== messageId),
      updatedAt: new Date()
    });
    
    updateSessionInArray(currentSession.id, updater);
    updateCurrentSessionIfMatches(currentSession.id, updater);
  },
  
  // Batch message operations
  addMultipleMessages(messages: Array<Omit<ChatMessage, 'id' | 'timestamp'>>): string[] {
    if (!currentSession) {
      throw new Error('No active session to add messages to');
    }
    
    const newMessages: ChatMessage[] = messages.map(message => ({
      ...message,
      id: generateId(),
      timestamp: new Date()
    }));
    
    const updater = (session: ChatSession) => {
      const updatedSession = {
        ...session,
        messages: [...session.messages, ...newMessages],
        updatedAt: new Date()
      };
      
      return trimMessagesIfNeeded(updatedSession);
    };
    
    updateSessionInArray(currentSession.id, updater);
    updateCurrentSessionIfMatches(currentSession.id, updater);
    
    return newMessages.map(msg => msg.id);
  },
  
  removeMultipleMessages(messageIds: string[]): void {
    if (!currentSession) return;
    
    const updater = (session: ChatSession) => ({
      ...session,
      messages: session.messages.filter(message => !messageIds.includes(message.id)),
      updatedAt: new Date()
    });
    
    updateSessionInArray(currentSession.id, updater);
    updateCurrentSessionIfMatches(currentSession.id, updater);
  },
  
  // Streaming management with debouncing and error handling
  setStreaming(isStreaming: boolean): void {
    try {
      streaming = isStreaming;
      
      // Log streaming state changes for debugging
      console.log(`Chat streaming ${isStreaming ? 'started' : 'stopped'}`);
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Failed to set streaming state: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.LOW,
        { isStreaming }
      ));
    }
  },
  
  startStreaming(): void {
    this.setStreaming(true);
  },
  
  stopStreaming(): void {
    this.setStreaming(false);
  },
  
  // Debounced message updates for streaming scenarios
  debouncedUpdateMessage: (() => {
    let pendingUpdates = new Map<string, Partial<ChatMessage>>();
    let updateTimeout: number | null = null;
    
    return (messageId: string, updates: Partial<ChatMessage>, delay: number = 150) => {
      // Accumulate updates
      const existing = pendingUpdates.get(messageId) || {};
      pendingUpdates.set(messageId, { ...existing, ...updates });
      
      // Clear previous timeout
      if (updateTimeout) {
        clearTimeout(updateTimeout);
      }
      
      // Schedule batch update
      updateTimeout = window.setTimeout(() => {
        try {
          for (const [id, updateData] of pendingUpdates) {
            this.updateMessage(id, updateData);
          }
          pendingUpdates.clear();
        } catch (error) {
          globalErrorBoundary.addError(createError(
            `Batch message update failed: ${error.message}`,
            ErrorType.CLIENT,
            ErrorSeverity.MEDIUM,
            { pendingUpdateCount: pendingUpdates.size }
          ));
        }
      }, delay);
    };
  })(),
  
  // Session utilities
  clearCurrentSession(): void {
    if (!currentSession) return;
    
    const updater = (session: ChatSession) => ({
      ...session,
      messages: [],
      updatedAt: new Date()
    });
    
    updateSessionInArray(currentSession.id, updater);
    updateCurrentSessionIfMatches(currentSession.id, updater);
  },
  
  duplicateSession(sessionId: string): string | null {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return null;
    
    const newSession: ChatSession = {
      id: generateId(),
      messages: [...session.messages], // Copy messages
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    sessions = [...sessions, newSession];
    
    return newSession.id;
  },
  
  renameSession(sessionId: string, newName: string): void {
    // Note: ChatSession doesn't have a name field in the type, 
    // but this could be added for future enhancement
    console.log(`Rename session ${sessionId} to ${newName} - feature not implemented in ChatSession type`);
  },
  
  // User context management
  setCurrentUser(userId: string | null): void {
    const previousUserId = currentUserId;
    
    // If user changed, clear all data
    if (previousUserId !== userId) {
      console.log(`Chat: User changed from ${previousUserId} to ${userId}, clearing data`);
      
      sessions = [];
      currentSession = null;
      streaming = false;
    }
    
    currentUserId = userId;
  },
  
  // Bulk operations
  clearAll(): void {
    console.log('Chat: Clearing all data');
    sessions = [];
    currentSession = null;
    streaming = false;
    currentUserId = null;
  },
  
  clearOldSessions(keepCount: number = 10): void {
    if (sessions.length <= keepCount) return;
    
    const sortedSessions = sessionsByDate;
    const sessionsToKeep = sortedSessions.slice(0, keepCount);
    const currentSessionId = currentSession?.id;
    
    // Always keep current session even if it's not in the recent list
    if (currentSessionId && !sessionsToKeep.find(s => s.id === currentSessionId)) {
      const currentSessionData = sessions.find(s => s.id === currentSessionId);
      if (currentSessionData) {
        sessionsToKeep.push(currentSessionData);
      }
    }
    
    sessions = sessionsToKeep;
  },
  
  // Optimized message filtering and search with memoization
  getMessagesByRole(role: ChatMessage['role']): ChatMessage[] {
    return messagesByRole()[role];
  },
  
  searchMessages: memoized(
    (query: string) => {
      if (!query?.trim()) return [];
      
      const lowercaseQuery = query.toLowerCase();
      return currentMessages.filter(msg =>
        msg.content.toLowerCase().includes(lowercaseQuery)
      );
    },
    (query: string) => [query, currentMessages.length],
    { name: 'chat-search-messages', maxAge: 5000 }
  ),
  
  // Advanced search with context and metadata
  advancedSearchMessages(options: {
    query?: string;
    role?: ChatMessage['role'];
    hasContext?: boolean;
    dateRange?: { start: Date; end: Date };
  }): ChatMessage[] {
    try {
      const { query, role, hasContext, dateRange } = options;
      let results = [...currentMessages];
      
      if (query?.trim()) {
        const lowercaseQuery = query.toLowerCase();
        results = results.filter(msg =>
          msg.content.toLowerCase().includes(lowercaseQuery)
        );
      }
      
      if (role) {
        results = results.filter(msg => msg.role === role);
      }
      
      if (hasContext !== undefined) {
        results = results.filter(msg => 
          hasContext ? (msg.documentContext || msg.analysisContext) : 
                      !(msg.documentContext || msg.analysisContext)
        );
      }
      
      if (dateRange) {
        results = results.filter(msg => {
          const msgTime = msg.timestamp.getTime();
          return msgTime >= dateRange.start.getTime() && 
                 msgTime <= dateRange.end.getTime();
        });
      }
      
      return results;
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Advanced search failed: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.LOW,
        { searchOptions: options }
      ));
      return [];
    }
  },
  
  getMessagesWithContext(): ChatMessage[] {
    return currentMessages.filter(msg => 
      msg.documentContext || msg.analysisContext
    );
  },
  
  // Session filtering and search
  getSessionById(sessionId: string): ChatSession | undefined {
    return sessions.find(session => session.id === sessionId);
  },
  
  searchSessions(query: string): ChatSession[] {
    const lowercaseQuery = query.toLowerCase();
    return sessions.filter(session =>
      session.messages.some(msg => 
        msg.content.toLowerCase().includes(lowercaseQuery)
      )
    );
  },
  
  getSessionsWithMessages(): ChatSession[] {
    return sessions.filter(session => session.messages.length > 0);
  },
  
  getEmptySessions(): ChatSession[] {
    return sessions.filter(session => session.messages.length === 0);
  },
  
  // Advanced analytics and statistics with performance monitoring
  getChatStatistics() {
    const stats = chatStats();
    const performanceMetrics = getChatPerformanceMetrics();
    
    return {
      ...stats,
      performance: {
        derivedComputations: performanceMetrics.derivedComputations,
        lastUpdate: performanceMetrics.lastUpdate,
        cacheHitRates: this.getCacheHitRates()
      }
    };
  },
  
  // Cache performance analysis
  getCacheHitRates() {
    const metrics = getChatPerformanceMetrics();
    const chatMetrics = Object.entries(metrics.derivedComputations)
      .filter(([name]) => name.startsWith('chat-'))
      .reduce((acc, [name, data]) => {
        acc[name] = {
          computations: data.count,
          averageTime: data.avgTime,
          totalTime: data.totalTime
        };
        return acc;
      }, {} as Record<string, any>);
    
    return chatMetrics;
  },
  
  // Error recovery and health check
  async recoverFromErrors(): Promise<boolean> {
    try {
      // Validate current state
      const isValid = this.validateCurrentState();
      if (!isValid) {
        console.warn('Chat state validation failed, attempting recovery...');
        
        // Attempt to restore from persistence
        await persistedChatState.restore();
        
        // Re-validate
        if (!this.validateCurrentState()) {
          // Reset to clean state if still invalid
          this.reset();
        }
      }
      
      // Clear old error states
      globalErrorBoundary.clearErrors(ErrorType.CLIENT);
      
      return true;
    } catch (error) {
      globalErrorBoundary.addError(createError(
        `Chat recovery failed: ${error.message}`,
        ErrorType.CLIENT,
        ErrorSeverity.HIGH,
        { recoveryAttempt: true }
      ));
      return false;
    }
  },
  
  // State validation for error recovery
  validateCurrentState(): boolean {
    try {
      // Check sessions array integrity
      if (!Array.isArray(sessions)) return false;
      
      // Validate each session
      for (const session of sessions) {
        if (!this.validateSession(session)) return false;
        
        // Validate messages in session
        for (const message of session.messages) {
          if (!this.validateMessage(message)) return false;
        }
      }
      
      // Validate current session reference
      if (currentSession && !sessions.find(s => s.id === currentSession.id)) {
        return false;
      }
      
      return true;
    } catch (error) {
      return false;
    }
  },
  
  // Retry wrapper for critical operations
  async withRetry<T>(
    operation: () => Promise<T> | T,
    operationName: string,
    maxRetries: number = 3
  ): Promise<T> {
    return withRetry(
      async () => operation(),
      {
        maxRetries,
        baseDelay: 1000,
        onRetry: (attempt, error) => {
          console.warn(`Retry ${attempt} for ${operationName}:`, error);
        },
        context: { operation: operationName }
      }
    );
  },
  
  // State management helpers
  getSnapshot() {
    return {
      sessions: sessions.map(session => ({
        ...session,
        messages: [...session.messages]
      })),
      currentSession: currentSession ? {
        ...currentSession,
        messages: [...currentSession.messages]
      } : null,
      streaming,
      currentUserId
    };
  },
  
  // Reset to initial state (for testing)
  reset(): void {
    sessions = [];
    currentSession = null;
    streaming = false;
    currentUserId = null;
  },
  
  // Validation helpers
  validateSession(session: Partial<ChatSession>): boolean {
    return !!(
      session.id &&
      Array.isArray(session.messages) &&
      session.createdAt &&
      session.updatedAt
    );
  },
  
  validateMessage(message: Partial<ChatMessage>): boolean {
    return !!(
      message.id &&
      message.role &&
      message.content &&
      message.timestamp
    );
  },
  
  // Export/import helpers
  exportSession(sessionId: string): ChatSession | null {
    const session = this.getSessionById(sessionId);
    return session ? { ...session, messages: [...session.messages] } : null;
  },
  
  importSession(sessionData: ChatSession): boolean {
    if (!this.validateSession(sessionData)) return false;
    
    // Check if session already exists
    if (sessions.find(s => s.id === sessionData.id)) {
      return false; // Don't import duplicate
    }
    
    sessions = [...sessions, sessionData];
    return true;
  }
};