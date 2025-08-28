import { writable, derived } from 'svelte/store';
import type { ChatState, ChatSession, ChatMessage } from '$lib/types';
import { generateId } from '$lib/utils';
import { CHAT_CONFIG } from '$lib/constants';

const defaultChatState: ChatState = {
  sessions: [],
  currentSession: null,
  streaming: false,
  currentUserId: null
};

function createChatStore() {
  const { subscribe, set, update } = writable<ChatState>(defaultChatState);

  return {
    subscribe,
    
    // Session management
    createSession: () => {
      const newSession: ChatSession = {
        id: generateId(),
        messages: [],
        createdAt: new Date(),
        updatedAt: new Date()
      };
      
      update(state => ({
        ...state,
        sessions: [...state.sessions, newSession],
        currentSession: newSession
      }));
      
      return newSession.id;
    },
    
    selectSession: (sessionId: string) =>
      update(state => ({
        ...state,
        currentSession: state.sessions.find(session => session.id === sessionId) || null
      })),
    
    removeSession: (sessionId: string) =>
      update(state => ({
        ...state,
        sessions: state.sessions.filter(session => session.id !== sessionId),
        currentSession: state.currentSession?.id === sessionId ? null : state.currentSession
      })),
    
    // Message management
    addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => {
      const newMessage: ChatMessage = {
        ...message,
        id: generateId(),
        timestamp: new Date()
      };
      
      update(state => {
        if (!state.currentSession) return state;
        
        const updatedSession = {
          ...state.currentSession,
          messages: [...state.currentSession.messages, newMessage],
          updatedAt: new Date()
        };
        
        // Trim messages if exceeding limit
        if (updatedSession.messages.length > CHAT_CONFIG.MAX_MESSAGES) {
          updatedSession.messages = updatedSession.messages.slice(-CHAT_CONFIG.MAX_MESSAGES);
        }
        
        return {
          ...state,
          currentSession: updatedSession,
          sessions: state.sessions.map(session =>
            session.id === updatedSession.id ? updatedSession : session
          )
        };
      });
      
      return newMessage.id;
    },
    
    updateMessage: (messageId: string, updates: Partial<ChatMessage>) =>
      update(state => {
        if (!state.currentSession) return state;
        
        const updatedSession = {
          ...state.currentSession,
          messages: state.currentSession.messages.map(message =>
            message.id === messageId ? { ...message, ...updates } : message
          ),
          updatedAt: new Date()
        };
        
        return {
          ...state,
          currentSession: updatedSession,
          sessions: state.sessions.map(session =>
            session.id === updatedSession.id ? updatedSession : session
          )
        };
      }),
    
    removeMessage: (messageId: string) =>
      update(state => {
        if (!state.currentSession) return state;
        
        const updatedSession = {
          ...state.currentSession,
          messages: state.currentSession.messages.filter(message => message.id !== messageId),
          updatedAt: new Date()
        };
        
        return {
          ...state,
          currentSession: updatedSession,
          sessions: state.sessions.map(session =>
            session.id === updatedSession.id ? updatedSession : session
          )
        };
      }),
    
    // Streaming management
    setStreaming: (streaming: boolean) =>
      update(state => ({ ...state, streaming })),
    
    // User context management
    setCurrentUser: (userId: string | null) =>
      update(state => {
        // If user changed, clear all data
        if (state.currentUserId !== userId) {
          return {
            ...defaultChatState,
            currentUserId: userId
          };
        }
        return { ...state, currentUserId: userId };
      }),
    
    // Utility functions
    clearCurrentSession: () =>
      update(state => {
        if (!state.currentSession) return state;
        
        const clearedSession = {
          ...state.currentSession,
          messages: [],
          updatedAt: new Date()
        };
        
        return {
          ...state,
          currentSession: clearedSession,
          sessions: state.sessions.map(session =>
            session.id === clearedSession.id ? clearedSession : session
          )
        };
      }),
    
    clearAll: () => set(defaultChatState)
  };
}

export const chatStore = createChatStore();

// Derived stores
export const sessionCount = derived(
  chatStore,
  $chatStore => $chatStore.sessions.length
);

export const currentMessages = derived(
  chatStore,
  $chatStore => $chatStore.currentSession?.messages || []
);

export const lastMessage = derived(
  currentMessages,
  $currentMessages => $currentMessages[$currentMessages.length - 1] || null
);

export const messageCount = derived(
  currentMessages,
  $currentMessages => $currentMessages.length
);

export const hasActiveSession = derived(
  chatStore,
  $chatStore => $chatStore.currentSession !== null
);

export const canSendMessage = derived(
  [chatStore, currentMessages],
  ([$chatStore, $currentMessages]) => 
    $chatStore.currentSession !== null && 
    !$chatStore.streaming &&
    $currentMessages.length < CHAT_CONFIG.MAX_MESSAGES
);