<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';

  interface Props {
    disabled?: boolean;
    analysisInProgress?: boolean;
    hasGroundTruth?: boolean;
    placeholder?: string;
    maxLength?: number;
  }

  let { 
    disabled = false, 
    analysisInProgress = false, 
    hasGroundTruth = true,
    placeholder = 'Enter your pharmaceutical protocol text here...',
    maxLength = 50000
  }: Props = $props();

  // Svelte 5 runes for state management
  let textContent = $state('');
  let textareaElement = $state<HTMLTextAreaElement>();
  let isFocused = $state(false);
  let lastAnalyzedText = $state('');

  const dispatch = createEventDispatcher<{
    input: { text: string };
    analyze: { text: string, options: any };
    error: { message: string };
  }>();

  // Derived values using $derived
  const characterCount = $derived(textContent.length);
  const wordCount = $derived(textContent.trim() ? textContent.trim().split(/\s+/).length : 0);
  const lineCount = $derived(textContent ? textContent.split('\n').length : 1);
  
  const isValidLength = $derived(characterCount >= 10 && characterCount <= maxLength);
  const hasMinimumContent = $derived(wordCount >= 5);
  const canAnalyze = $derived(
    isValidLength && hasMinimumContent && !disabled && !analysisInProgress && hasGroundTruth
  );
  const hasNewContent = $derived(textContent !== lastAnalyzedText);
  const showAnalyzeButton = $derived(canAnalyze && hasNewContent);

  // Content analysis
  const containsPharmaceuticalTerms = $derived.by(() => {
    const pharmTerms = [
      'hplc', 'chromatography', 'analysis', 'method', 'procedure', 'protocol',
      'pharmaceutical', 'drug', 'api', 'assay', 'validation', 'specification',
      'quality', 'control', 'testing', 'sample', 'preparation', 'mobile phase',
      'column', 'detection', 'uv', 'ms', 'nmr', 'ftir', 'gc', 'lc'
    ];
    const lowerText = textContent.toLowerCase();
    return pharmTerms.some(term => lowerText.includes(term));
  });

  const suggestedImprovements = $derived.by(() => {
    const suggestions: string[] = [];
    
    if (wordCount > 0 && wordCount < 20) {
      suggestions.push('Consider adding more detail to your protocol description');
    }
    
    if (!containsPharmaceuticalTerms && wordCount > 10) {
      suggestions.push('This doesn\'t appear to be a pharmaceutical protocol. Please ensure you\'re entering the correct content.');
    }
    
    if (textContent.length > 0 && !textContent.includes('.')) {
      suggestions.push('Consider adding proper sentence structure with periods for better analysis');
    }
    
    return suggestions;
  });

  const validationStatus = $derived.by(() => {
    if (characterCount === 0) return 'empty';
    if (!isValidLength) return characterCount < 10 ? 'too-short' : 'too-long';
    if (!hasMinimumContent) return 'insufficient';
    if (!containsPharmaceuticalTerms && wordCount > 20) return 'non-pharmaceutical';
    return 'valid';
  });

  const statusMessage = $derived.by(() => {
    switch (validationStatus) {
      case 'empty':
        return 'Enter your protocol text to begin analysis';
      case 'too-short':
        return `Add ${10 - characterCount} more characters (minimum 10)`;
      case 'too-long':
        return `Reduce by ${characterCount - maxLength} characters (maximum ${maxLength.toLocaleString()})`;
      case 'insufficient':
        return 'Add more content (minimum 5 words)';
      case 'non-pharmaceutical':
        return 'This may not be a pharmaceutical protocol - please verify content';
      case 'valid':
        return hasGroundTruth 
          ? 'Ready for analysis against ground truth library'
          : 'Upload ground truth documents first';
      default:
        return '';
    }
  });

  const statusColor = $derived.by(() => {
    switch (validationStatus) {
      case 'valid':
        return hasGroundTruth ? 'var(--color-success-600)' : 'var(--color-warning-600)';
      case 'non-pharmaceutical':
        return 'var(--color-warning-600)';
      case 'too-long':
      case 'insufficient':
        return 'var(--color-error-600)';
      case 'too-short':
        return 'var(--color-warning-600)';
      default:
        return 'var(--color-text-muted)';
    }
  });

  function handleInput(event: Event) {
    const target = event.target as HTMLTextAreaElement;
    textContent = target.value;
    
    // Auto-resize textarea
    if (textareaElement) {
      textareaElement.style.height = 'auto';
      textareaElement.style.height = textareaElement.scrollHeight + 'px';
    }
    
    // Dispatch input event
    dispatch('input', { text: textContent });
  }

  function handleFocus() {
    isFocused = true;
  }

  function handleBlur() {
    isFocused = false;
  }

  function handleKeydown(event: KeyboardEvent) {
    // Ctrl/Cmd + Enter to analyze
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter' && canAnalyze) {
      event.preventDefault();
      analyzeText();
    }
  }

  function analyzeText() {
    if (!canAnalyze) {
      dispatch('error', { message: 'Please enter valid protocol text before analysis' });
      return;
    }

    lastAnalyzedText = textContent;
    dispatch('analyze', { 
      text: textContent, 
      options: { 
        characterCount, 
        wordCount, 
        lineCount,
        containsPharmaceuticalTerms
      } 
    });
  }

  function clearText() {
    textContent = '';
    lastAnalyzedText = '';
    if (textareaElement) {
      textareaElement.style.height = 'auto';
      textareaElement.focus();
    }
  }

  function insertExample() {
    const exampleText = `HPLC Analysis of Acetaminophen Tablets

Method Overview:
This analytical method describes the quantitative determination of acetaminophen in pharmaceutical tablets using high-performance liquid chromatography (HPLC) with UV detection.

Sample Preparation:
1. Weigh accurately about 20 tablets and determine average weight
2. Powder the tablets in a suitable mill
3. Transfer accurately weighed portion equivalent to about 100mg acetaminophen to 100mL volumetric flask
4. Add 70mL of mobile phase, sonicate for 15 minutes
5. Dilute to volume with mobile phase and mix well
6. Filter through 0.45μm membrane filter

Chromatographic Conditions:
- Column: C18, 250mm × 4.6mm, 5μm particle size
- Mobile Phase: Acetonitrile:Water (30:70, v/v)
- Flow Rate: 1.0 mL/min
- Detection: UV at 254nm
- Injection Volume: 20μL
- Run Time: 15 minutes
- Column Temperature: 25°C

System Suitability:
- Theoretical plates: Not less than 2000
- Tailing factor: Not more than 2.0
- Relative standard deviation: Not more than 2.0%

Quality Control:
All procedures must comply with ICH Q2(R1) guidelines for analytical method validation.`;

    textContent = exampleText;
    if (textareaElement) {
      textareaElement.style.height = 'auto';
      textareaElement.style.height = textareaElement.scrollHeight + 'px';
    }
    dispatch('input', { text: textContent });
  }
</script>

<div class="text-protocol-input">
  <div class="input-header">
    <div class="header-info">
      <h4>
        <Icon name="edit" size={18} />
        Protocol Text Input
      </h4>
      <p>Paste or type your pharmaceutical protocol directly for immediate analysis</p>
    </div>
    
    <div class="header-actions">
      {#if textContent.length === 0}
        <Button variant="secondary" size="sm" onclick={insertExample}>
          <Icon name="file-text" size={14} />
          Insert Example
        </Button>
      {:else}
        <Button variant="secondary" size="sm" onclick={clearText}>
          <Icon name="x" size={14} />
          Clear
        </Button>
      {/if}
    </div>
  </div>

  <div class="input-container" class:focused={isFocused} class:disabled={disabled}>
    <textarea
      bind:this={textareaElement}
      value={textContent}
      {placeholder}
      {disabled}
      maxlength={maxLength}
      oninput={handleInput}
      onfocus={handleFocus}
      onblur={handleBlur}
      onkeydown={handleKeydown}
      class="protocol-textarea"
      spellcheck="true"
    ></textarea>
    
    {#if textContent.length === 0 && !isFocused}
      <div class="empty-state-overlay">
        <Icon name="edit" size={32} color="var(--color-gray-300)" />
        <span class="empty-text">Start typing or paste your protocol text...</span>
        <span class="empty-hint">Supports pharmaceutical protocols, analytical methods, and procedures</span>
      </div>
    {/if}
  </div>

  <!-- Text Statistics -->
  <div class="text-stats">
    <div class="stats-left">
      <div class="stat-item">
        <Icon name="type" size={14} />
        <span>{characterCount.toLocaleString()} characters</span>
      </div>
      <div class="stat-item">
        <Icon name="file-text" size={14} />
        <span>{wordCount.toLocaleString()} words</span>
      </div>
      <div class="stat-item">
        <Icon name="list" size={14} />
        <span>{lineCount.toLocaleString()} lines</span>
      </div>
    </div>
    
    <div class="stats-right">
      <div class="char-limit">
        <span class="char-count" class:warning={characterCount > maxLength * 0.9}>
          {characterCount} / {maxLength.toLocaleString()}
        </span>
      </div>
    </div>
  </div>

  <!-- Validation Status -->
  <div class="validation-status">
    <div class="status-indicator" style="color: {statusColor}">
      <Icon 
        name={validationStatus === 'valid' ? 'check' : validationStatus === 'empty' ? 'info' : 'warning'} 
        size={16} 
      />
      <span class="status-text">{statusMessage}</span>
    </div>
    
    {#if validationStatus === 'valid' && hasGroundTruth}
      <div class="pharmaceutical-indicator">
        <Icon 
          name={containsPharmaceuticalTerms ? 'check' : 'warning'} 
          size={14} 
          color={containsPharmaceuticalTerms ? 'var(--color-success-600)' : 'var(--color-warning-600)'}
        />
        <span class="indicator-text">
          {containsPharmaceuticalTerms ? 'Pharmaceutical content detected' : 'No pharmaceutical terms detected'}
        </span>
      </div>
    {/if}
  </div>

  <!-- Content Suggestions -->
  {#if suggestedImprovements.length > 0}
    <div class="suggestions">
      <h5>
        <Icon name="info" size={16} />
        Suggestions for Better Analysis
      </h5>
      <ul class="suggestions-list">
        {#each suggestedImprovements as suggestion}
          <li>{suggestion}</li>
        {/each}
      </ul>
    </div>
  {/if}

  <!-- Analysis Action -->
  {#if showAnalyzeButton}
    <div class="analysis-action">
      <Button
        variant="primary"
        size="lg"
        onclick={analyzeText}
        loading={analysisInProgress}
        disabled={!canAnalyze}
      >
        <Icon name="activity" size={18} />
        {analysisInProgress ? 'Analyzing Protocol...' : 'Analyze Against Ground Truth'}
      </Button>
      <div class="keyboard-hint">
        <Icon name="info" size={12} />
        <span>Tip: Press Ctrl+Enter to analyze</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .text-protocol-input {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    padding: var(--space-6);
  }

  .input-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: var(--space-4);
  }

  .header-info h4 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .header-info p {
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    margin: 0;
  }

  .header-actions {
    flex-shrink: 0;
  }

  .input-container {
    position: relative;
    border: 2px solid var(--color-border);
    border-radius: var(--radius-lg);
    background: white;
    transition: all var(--transition-fast);
    min-height: 300px;
  }

  .input-container.focused {
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-primary-100);
  }

  .input-container.disabled {
    background: var(--color-gray-50);
    opacity: 0.7;
  }

  .protocol-textarea {
    width: 100%;
    min-height: 300px;
    padding: var(--space-4);
    border: none;
    outline: none;
    resize: none;
    font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
    color: var(--color-text);
    background: transparent;
    overflow-y: auto;
  }

  .protocol-textarea::placeholder {
    color: var(--color-text-muted);
    font-style: italic;
  }

  .empty-state-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
    text-align: center;
    pointer-events: none;
    opacity: 0.7;
  }

  .empty-text {
    font-size: var(--font-size-base);
    color: var(--color-text-muted);
    font-weight: var(--font-weight-medium);
  }

  .empty-hint {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    opacity: 0.8;
  }

  .text-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-3) var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border);
  }

  .stats-left {
    display: flex;
    gap: var(--space-4);
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
  }

  .stats-right {
    display: flex;
    align-items: center;
    gap: var(--space-3);
  }

  .char-limit {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  .char-count.warning {
    color: var(--color-warning-600);
    font-weight: var(--font-weight-medium);
  }

  .validation-status {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    padding: var(--space-3);
    background: var(--color-gray-25);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border);
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
  }

  .pharmaceutical-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-xs);
    color: var(--color-text-secondary);
    margin-left: var(--space-5);
  }

  .suggestions {
    padding: var(--space-4);
    background: var(--color-warning-50);
    border: 1px solid var(--color-warning-200);
    border-radius: var(--radius-md);
  }

  .suggestions h5 {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    margin: 0 0 var(--space-3) 0;
    color: var(--color-warning-700);
  }

  .suggestions-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .suggestions-list li {
    font-size: var(--font-size-sm);
    color: var(--color-warning-700);
    padding-left: var(--space-4);
    position: relative;
  }

  .suggestions-list li::before {
    content: '•';
    position: absolute;
    left: 0;
    color: var(--color-warning-500);
  }

  .analysis-action {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-primary-50);
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-lg);
  }

  .keyboard-hint {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    font-size: var(--font-size-xs);
    color: var(--color-primary-600);
    opacity: 0.8;
  }

  @media (max-width: 768px) {
    .text-protocol-input {
      padding: var(--space-4);
    }

    .input-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .text-stats {
      flex-direction: column;
      gap: var(--space-2);
      align-items: stretch;
    }

    .stats-left {
      flex-direction: column;
      gap: var(--space-2);
    }

    .protocol-textarea {
      min-height: 250px;
      font-size: var(--font-size-sm);
    }

    .input-container {
      min-height: 250px;
    }
  }
</style>