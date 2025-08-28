<script lang="ts">
  import { browser } from '$app/environment';
  import { chatStore, canSendMessage, currentMessages, authState, currentUser, toastStore } from '$lib/stores';
  import Icon from '$lib/components/common/Icon.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import { formatRelativeTime } from '$lib/utils';
  import { session as sessionApi, GuardianApiError } from '$lib/services/api';
  import { sanitizeText, validateUserInput } from '$lib/utils/security';
  import type { ChatMessage } from '$lib/types';

  interface Props {
    documentContext?: string;
    analysisContext?: string;
  }
  
  let { documentContext, analysisContext }: Props = $props();

  // Convert input state to Svelte 5 runes
  let messageInput = $state('');
  let chatContainer: HTMLElement;
  let inputElement: HTMLInputElement;
  let initialized = $state(false);

  // Convert authentication reactive statements to Svelte 5 $derived
  // Access reactive authentication state directly
  const authenticated = $derived(authState.authenticated);
  const user = $derived(currentUser());
  const messages = $derived(currentMessages());
  const streaming = $derived(chatStore.streaming);
  const canSend = $derived(authenticated && canSendMessage() && messageInput.trim().length > 0 && !streaming);

  // Convert auto-scroll to Svelte 5 $effect
  $effect(() => {
    // Auto-scroll to bottom when new messages arrive
    if (chatContainer && messages.length > 0) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });

  // Convert onMount to Svelte 5 $effect
  $effect(() => {
    if (!browser || initialized) return;
    initialized = true;
    
    // Create a session if none exists and user is authenticated
    if (authenticated && !chatStore.currentSession) {
      chatStore.createSession();
    }
  });

  async function sendMessage() {
    if (!canSend) return;

    if (!authenticated) {
      toastStore.error('Authentication Required', 'Please sign in to use the chat assistant');
      return;
    }

    const rawContent = messageInput.trim();
    messageInput = '';

    // Validate and sanitize user input
    const validation = validateUserInput(rawContent, {
      maxLength: 2000, // Reasonable limit for chat messages
      sanitizeHtml: true
    });

    if (!validation.isValid) {
      toastStore.error('Invalid Input', validation.errors.join('. '));
      messageInput = rawContent; // Restore input for user to fix
      return;
    }

    const content = validation.sanitizedInput;

    // Add user message
    chatStore.addMessage({
      role: 'user',
      content,
      documentContext,
      analysisContext
    });

    // Set streaming state
    chatStore.setStreaming(true);

    try {
      // Try to use session-based chat API, fallback to simulation
      if (sessionApi.chat) {
        await sendSessionBasedMessage(content);
      } else {
        // Fallback to simulation for development
        await simulateAIResponse(content);
      }
    } catch (error) {
      console.error('Chat error:', error);
      let errorMessage = 'I apologize, but I encountered an error processing your message. Please try again.';
      
      if (error instanceof GuardianApiError) {
        errorMessage = error.message;
        toastStore.error('Chat Error', error.message);
      }
      
      chatStore.addMessage({
        role: 'assistant',
        content: errorMessage,
        documentContext,
        analysisContext
      });
    } finally {
      chatStore.setStreaming(false);
    }
  }

  // Session-based chat API integration
  async function sendSessionBasedMessage(userMessage: string) {
    try {
      const response = await sessionApi.chat({
        message: userMessage,
        document_context: documentContext,
        analysis_context: analysisContext
      });

      if (response.data) {
        chatStore.addMessage({
          role: 'assistant',
          content: response.data.response || response.data.message,
          documentContext,
          analysisContext
        });
      }
    } catch (error) {
      throw error;
    }
  }

  // Simulate AI response (fallback for development)
  async function simulateAIResponse(userMessage: string) {
    // Simulate typing delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    let response = '';
    
    if (userMessage.toLowerCase().includes('compliance')) {
      response = 'Based on your protocol analysis, I can see several compliance considerations. Global pharmaceutical standards have specific requirements for pharmaceutical protocols that need to be addressed...';
    } else if (userMessage.toLowerCase().includes('recommendation')) {
      response = 'Here are my recommendations for improving protocol compliance:\n\n1. Review the analytical methods section\n2. Ensure proper documentation of quality control procedures\n3. Verify that all critical parameters are within specified ranges';
    } else {
      response = 'I\'m here to help you with pharmaceutical compliance questions. You can ask me about specific findings, recommendations for improvement, or general guidance on regulatory standards.';
    }

    // Simulate streaming response
    const words = response.split(' ');
    let currentResponse = '';
    
    const messageId = chatStore.addMessage({
      role: 'assistant',
      content: '',
      documentContext,
      analysisContext
    });

    for (let i = 0; i < words.length; i++) {
      currentResponse += (i > 0 ? ' ' : '') + words[i];
      chatStore.updateMessage(messageId, { content: currentResponse });
      await new Promise(resolve => setTimeout(resolve, 50 + Math.random() * 100));
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function clearChat() {
    chatStore.clearCurrentSession();
  }

  function getMessageAvatar(role: string): string {
    return role === 'user' ? 'You' : 'AI';
  }
</script>

<div class="chat-interface">
  <div class="chat-header">
    <div class="header-info">
      <Icon name="chat" size={20} />
      <h3>Compliance Assistant</h3>
    </div>
    <div class="header-actions">
      <Button
        variant="secondary"
        size="sm"
        onclick={clearChat}
        disabled={messages.length === 0}
      >
        <Icon name="x" size={16} />
        Clear
      </Button>
    </div>
  </div>

  <div class="chat-messages" bind:this={chatContainer}>
    {#if messages.length === 0}
      <div class="empty-state">
        {#if authenticated}
          <Icon name="chat" size={48} color="var(--color-gray-400)" />
          <h4>Start a Conversation</h4>
          <p>Ask me about your protocol compliance analysis, specific findings, or general pharmaceutical guidance.</p>
          <div class="suggested-questions">
            <button 
              class="suggestion-button"
              onclick={() => messageInput = 'What are the main compliance issues in my protocol?'}
            >
              What are the main compliance issues?
            </button>
            <button 
              class="suggestion-button"
              onclick={() => messageInput = 'How can I improve my compliance score?'}
            >
              How can I improve my score?
            </button>
            <button 
              class="suggestion-button"
              onclick={() => messageInput = 'Explain the critical findings'}
            >
              Explain critical findings
            </button>
          </div>
        {:else}
          <Icon name="lock" size={48} color="var(--color-gray-400)" />
          <h4>Authentication Required</h4>
          <p>Please sign in to start a conversation with the AI compliance assistant.</p>
          <div class="auth-prompt">
            <p>With the chat assistant, you can:</p>
            <ul>
              <li>Ask questions about compliance findings</li>
              <li>Get recommendations for improvement</li>
              <li>Receive guidance on regulatory standards</li>
            </ul>
          </div>
        {/if}
      </div>
    {:else}
      {#each messages as message (message.id)}
        <div class="message" class:user={message.role === 'user'} class:assistant={message.role === 'assistant'}>
          <div class="message-avatar">
            {getMessageAvatar(message.role)}
          </div>
          
          <div class="message-bubble">
            <div class="message-content">
              {#if message.content}
                {#each message.content.split('\n') as line}
                  {line}<br>
                {/each}
              {/if}
            </div>
            <div class="message-timestamp">
              {formatRelativeTime(message.timestamp)}
            </div>
          </div>
        </div>
      {/each}

      {#if streaming}
        <div class="message assistant">
          <div class="message-avatar">AI</div>
          <div class="message-bubble">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      {/if}
    {/if}
  </div>

  <div class="chat-input">
    <div class="input-container">
      <input
        bind:this={inputElement}
        bind:value={messageInput}
        type="text"
        placeholder={authenticated ? "Ask about your protocol compliance..." : "Please sign in to use chat"}
        disabled={!authenticated || streaming}
        onkeypress={handleKeyPress}
      />
      <Button
        variant="primary"
        size="sm"
        disabled={!canSend}
        loading={streaming}
        onclick={sendMessage}
      >
        <Icon name="arrow-right" size={16} />
      </Button>
    </div>
    
    {#if documentContext || analysisContext}
      <div class="context-info">
        <Icon name="info" size={14} />
        <span>
          Context: 
          {#if documentContext}Document{/if}
          {#if documentContext && analysisContext} + {/if}
          {#if analysisContext}Analysis{/if}
        </span>
      </div>
    {/if}
  </div>
</div>

<style>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: 600px;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    overflow: hidden;
  }

  .chat-header {
    display: flex;
    justify-content: between;
    align-items: center;
    padding: var(--space-4) var(--space-6);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-gray-50);
  }

  .header-info {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .header-info h3 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0;
  }

  .header-actions {
    display: flex;
    gap: var(--space-2);
  }

  .chat-messages {
    flex: 1;
    padding: var(--space-4);
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    gap: var(--space-4);
  }

  .empty-state h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin: 0;
  }

  .empty-state p {
    color: var(--color-text-secondary);
    max-width: 300px;
    margin: 0;
  }

  .suggested-questions {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    margin-top: var(--space-4);
  }

  .suggestion-button {
    background: none;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-2) var(--space-3);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .suggestion-button:hover {
    background: var(--color-primary-50);
    border-color: var(--color-primary-200);
    color: var(--color-primary-600);
  }

  .message {
    display: flex;
    gap: var(--space-3);
    max-width: 80%;
    align-items: flex-start;
  }

  .message.user {
    align-self: flex-end;
    flex-direction: row-reverse;
  }

  .message.assistant {
    align-self: flex-start;
  }

  .message-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: var(--radius-full);
    font-size: var(--font-size-xs);
    font-weight: var(--font-weight-medium);
    flex-shrink: 0;
  }

  .message.user .message-avatar {
    background: var(--color-primary-500);
    color: white;
  }

  .message.assistant .message-avatar {
    background: var(--color-gray-200);
    color: var(--color-gray-700);
  }

  .message-bubble {
    position: relative;
    max-width: 100%;
  }

  .message-content {
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
    word-wrap: break-word;
  }

  .message.user .message-content {
    background: var(--color-primary-500);
    color: white;
  }

  .message.assistant .message-content {
    background: var(--color-gray-100);
    color: var(--color-text);
  }

  .message-timestamp {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin-top: var(--space-1);
    text-align: right;
  }

  .message.user .message-timestamp {
    text-align: left;
  }

  .typing-indicator {
    display: flex;
    gap: var(--space-1);
    padding: var(--space-3) var(--space-4);
    background: var(--color-gray-100);
    border-radius: var(--radius-lg);
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: var(--color-gray-400);
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out;
  }

  .typing-indicator span:nth-child(1) {
    animation-delay: -0.32s;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: -0.16s;
  }

  .chat-input {
    padding: var(--space-4) var(--space-6);
    border-top: 1px solid var(--color-border);
    background: var(--color-surface);
  }

  .input-container {
    display: flex;
    gap: var(--space-2);
    align-items: center;
  }

  .input-container input {
    flex: 1;
    padding: var(--space-3) var(--space-4);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    font-size: var(--font-size-sm);
    transition: border-color var(--transition-fast);
    background: var(--color-surface);
  }

  .input-container input:focus {
    outline: none;
    border-color: var(--color-primary-500);
  }

  .input-container input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .context-info {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-top: var(--space-2);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  /* Authentication-aware styles */
  .auth-prompt {
    margin-top: var(--space-4);
    text-align: left;
    max-width: 300px;
  }

  .auth-prompt p {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-2) 0;
  }

  .auth-prompt ul {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .auth-prompt li {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    position: relative;
    padding-left: var(--space-4);
  }

  .auth-prompt li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: var(--color-primary-600);
    font-weight: var(--font-weight-bold);
  }

  @keyframes typing {
    0%, 60%, 100% {
      transform: translateY(0);
    }
    30% {
      transform: translateY(-10px);
    }
  }

  @media (max-width: 640px) {
    .chat-interface {
      height: 500px;
    }

    .message {
      max-width: 95%;
    }

    .chat-header {
      padding: var(--space-3) var(--space-4);
    }

    .chat-messages {
      padding: var(--space-3);
    }

    .chat-input {
      padding: var(--space-3) var(--space-4);
    }
  }
</style>