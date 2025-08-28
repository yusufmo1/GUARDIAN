<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import DocumentProcessingProgress from './DocumentProcessingProgress.svelte';
  import { toastStore } from '$lib/stores';

  interface Props {
    disabled?: boolean;
    multiple?: boolean;
    onUploadProgress?: (stage: number, completed: boolean, error?: string) => void;
  }

  let { disabled = false, multiple = true, onUploadProgress }: Props = $props();

  // Svelte 5 runes for state management
  let isDragging = $state(false);
  let fileInput = $state<HTMLInputElement>();
  let selectedCategory = $state('regulatory_standards');
  let files = $state<FileList | null>(null);
  let isProcessing = $state(false);
  let currentProcessingStage = $state(0);
  let processingFiles = $state<File[]>([]);

  // Create event dispatcher
  const dispatch = createEventDispatcher<{
    upload: { files: File[], category: string };
    error: { message: string };
  }>();

  // Document categories for ground truth documents
  const documentCategories = [
    { value: 'regulatory_standards', label: 'Regulatory Standards', description: 'Official regulatory monographs and standards' },
    { value: 'analytical_method', label: 'Analytical Methods', description: 'Standard analytical procedures and methods' },
    { value: 'quality_control', label: 'Quality Control', description: 'QC procedures and specifications' },
    { value: 'regulatory_guidance', label: 'Regulatory Guidance', description: 'FDA, EMA, and other regulatory guidance documents' },
    { value: 'ich_guideline', label: 'ICH Guidelines', description: 'International harmonization guidelines' },
    { value: 'pharmacopoeial_general', label: 'Pharmacopoeial General', description: 'General chapters and methods' }
  ];

  // Supported file types for ground truth documents
  const supportedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  const maxFileSize = 50 * 1024 * 1024; // 50MB

  // Derived values
  const selectedCategoryInfo = $derived(
    documentCategories.find(cat => cat.value === selectedCategory)
  );

  function handleDragOver(event: DragEvent) {
    if (disabled) return;
    event.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(event: DragEvent) {
    if (disabled) return;
    event.preventDefault();
    isDragging = false;
  }

  function handleDrop(event: DragEvent) {
    if (disabled) return;
    event.preventDefault();
    isDragging = false;

    const droppedFiles = event.dataTransfer?.files;
    if (droppedFiles) {
      handleFiles(droppedFiles);
    }
  }

  function handleFileSelect(event: Event) {
    if (disabled) return;
    const target = event.target as HTMLInputElement;
    if (target.files) {
      handleFiles(target.files);
    }
  }

  function handleFiles(fileList: FileList) {
    const fileArray = Array.from(fileList);
    
    // Validate files
    const errors: string[] = [];
    const validFiles: File[] = [];

    for (const file of fileArray) {
      // Check file type
      if (!supportedTypes.includes(file.type)) {
        errors.push(`${file.name}: Unsupported file type. Please use PDF, DOCX, or TXT files.`);
        continue;
      }

      // Check file size
      if (file.size > maxFileSize) {
        errors.push(`${file.name}: File too large. Maximum size is 50MB.`);
        continue;
      }

      // Check for empty files
      if (file.size === 0) {
        errors.push(`${file.name}: File is empty.`);
        continue;
      }

      validFiles.push(file);
    }

    // Show errors if any
    if (errors.length > 0) {
      errors.forEach(error => {
        dispatch('error', { message: error });
      });
    }

    // Process valid files
    if (validFiles.length > 0) {
      files = fileList;
      console.log(`Selected ${validFiles.length} ground truth documents for category: ${selectedCategory}`);
      toastStore.info('Upload Started', `Uploading ${validFiles.length} document(s)...`);
      
      // Auto-upload immediately after selection
      uploadFiles();
    }

    // Clear the input
    if (fileInput) {
      fileInput.value = '';
    }
  }

  function uploadFiles() {
    console.log('GroundTruthUpload: uploadFiles() called', { files, filesLength: files?.length, selectedCategory });
    
    if (!files || files.length === 0) {
      console.log('GroundTruthUpload: No files selected, dispatching error');
      dispatch('error', { message: 'No files selected for upload' });
      return;
    }

    const fileArray = Array.from(files);
    console.log('GroundTruthUpload: Dispatching upload event', { fileCount: fileArray.length, category: selectedCategory });
    
    // Start processing flow
    isProcessing = true;
    currentProcessingStage = 0;
    processingFiles = [...fileArray];
    
    // Start the progress simulation
    simulateProcessingStages();
    
    // Dispatch upload event to parent
    dispatch('upload', { files: fileArray, category: selectedCategory });
    
    // Clear files after processing starts
    files = null;
  }

  async function simulateProcessingStages() {
    // Simulate the processing stages with realistic timings but wait for backend
    const stageDurations = [
      1000, // Uploading document - 1s
      1500, // Extracting text - 1.5s  
      2000, // Processing content - 2s
      2500, // Generating embeddings - 2.5s
      1500, // Building search index - 1.5s
    ];

    // Go through stages until the last one
    for (let stage = 0; stage < stageDurations.length && isProcessing; stage++) {
      currentProcessingStage = stage;
      
      // Notify parent of progress
      if (onUploadProgress) {
        onUploadProgress(stage, false);
      }
      
      await new Promise(resolve => setTimeout(resolve, stageDurations[stage]));
    }

    // Now wait for backend completion signal
    // The parent component will call completeProcessing when backend is done
  }

  // Export this function so parent can call it when backend completes
  export function completeProcessing(success: boolean, errorMessage?: string) {
    if (!isProcessing) return; // Already completed
    
    if (success) {
      // Complete the final stage
      currentProcessingStage = 5; // Analysis complete
      
      // Notify parent
      if (onUploadProgress) {
        onUploadProgress(5, true);
      }
      
      setTimeout(() => {
        isProcessing = false;
        processingFiles = [];
        
        // Show completion message
        toastStore.success('Processing Complete', 'Documents have been successfully processed and indexed');
      }, 500); // Small delay to show completion stage
    } else {
      // Handle error
      isProcessing = false;
      processingFiles = [];
      currentProcessingStage = 0;
      
      // Notify parent
      if (onUploadProgress) {
        onUploadProgress(0, true, errorMessage);
      }
      
      toastStore.error('Processing Failed', errorMessage || 'Document processing failed');
    }
  }

  function cancelProcessing() {
    isProcessing = false;
    currentProcessingStage = 0;
    processingFiles = [];
    files = null;
    
    toastStore.info('Processing Cancelled', 'Document processing has been cancelled');
  }

  function clearFiles() {
    files = null;
    if (fileInput) {
      fileInput.value = '';
    }
  }

  function openFileDialog() {
    if (disabled || !fileInput) return;
    fileInput.click();
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
</script>

<div class="ground-truth-upload">
  <div class="upload-header">
    <h3>
      <Icon name="book-open" size={20} />
      Upload Ground Truth Documents
    </h3>
    <p>Upload regulatory standards, analytical methods, and compliance reference documents.</p>
  </div>

  <!-- Category Selection -->
  <div class="category-section">
    <label for="document-category">Document Category</label>
    <select 
      id="document-category" 
      bind:value={selectedCategory}
      {disabled}
    >
      {#each documentCategories as category}
        <option value={category.value}>{category.label}</option>
      {/each}
    </select>
    {#if selectedCategoryInfo}
      <p class="category-description">{selectedCategoryInfo.description}</p>
    {/if}
  </div>

  <!-- File Drop Zone -->
  <div 
    class="drop-zone"
    class:dragging={isDragging}
    class:disabled={disabled}
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    onclick={openFileDialog}
    role="button"
    tabindex="0"
    onkeydown={(e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openFileDialog();
      }
    }}
  >
    <input
      bind:this={fileInput}
      type="file"
      accept=".pdf,.docx,.txt"
      {multiple}
      {disabled}
      onchange={handleFileSelect}
      style="display: none;"
    />

    <div class="drop-zone-content">
      <Icon name="upload" size={48} color="var(--color-primary-600)" />
      <div class="drop-zone-text">
        <h4>Upload Ground Truth Documents</h4>
        <p>
          {#if isDragging}
            Release to upload files
          {:else}
            Drag and drop files here, or click to browse
          {/if}
        </p>
        <div class="file-requirements">
          <span>Supported: PDF, DOCX, TXT</span>
          <span>Max size: 50MB per file</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Processing Progress -->
  {#if isProcessing && processingFiles.length > 0}
    <DocumentProcessingProgress 
      files={processingFiles}
      currentStage={currentProcessingStage}
      {isProcessing}
      onCancel={cancelProcessing}
    />
  {/if}

  <!-- Selected Files Preview -->
  {#if files && files.length > 0 && !isProcessing}
    <div class="files-preview">
      <div class="files-header">
        <h4>Selected Files ({files.length})</h4>
        <Button variant="secondary" size="sm" onclick={clearFiles}>
          <Icon name="x" size={14} />
          Clear All
        </Button>
      </div>
      
      <div class="files-list">
        {#each Array.from(files) as file}
          <div class="file-item">
            <div class="file-icon">
              <Icon name="file-text" size={20} />
            </div>
            <div class="file-info">
              <span class="file-name">{file.name}</span>
              <span class="file-size">{formatFileSize(file.size)}</span>
            </div>
            <div class="file-category">
              <Icon name="tag" size={14} />
              <span>{selectedCategoryInfo?.label}</span>
            </div>
          </div>
        {/each}
      </div>

      <div class="upload-status">
        <div class="status-indicator">
          <Icon name="loading" size={16} class="animate-spin" />
          <span>Uploading {files.length} document{files.length === 1 ? '' : 's'}...</span>
        </div>
        <Button variant="secondary" size="sm" onclick={clearFiles}>
          <Icon name="x" size={14} />
          Cancel
        </Button>
      </div>
    </div>
  {/if}

  <!-- Information Section -->
  <div class="info-section">
    <div class="info-item">
      <Icon name="info" size={16} color="var(--color-primary-600)" />
      <span>Documents are automatically processed and indexed for intelligent search and compliance analysis.</span>
    </div>
    <div class="info-item">
      <Icon name="shield" size={16} color="var(--color-success-600)" />
      <span>All documents are stored securely in your personal Google Drive with encrypted processing.</span>
    </div>
    <div class="info-item">
      <Icon name="search" size={16} color="var(--color-secondary-600)" />
      <span>Upload standards now to enable protocol compliance checking against authoritative references.</span>
    </div>
  </div>
</div>

<style>
  .ground-truth-upload {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .upload-header {
    text-align: center;
    margin-bottom: var(--space-4);
  }

  .upload-header h3 {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .upload-header p {
    color: var(--color-text-secondary);
    margin: 0;
    font-size: var(--font-size-sm);
  }

  .category-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .category-section label {
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    font-size: var(--font-size-sm);
  }

  .category-section select {
    padding: var(--space-3);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    background: white;
    color: var(--color-text);
  }

  .category-section select:focus {
    outline: none;
    border-color: var(--color-primary-500);
    box-shadow: 0 0 0 3px var(--color-primary-100);
  }

  .category-section select:disabled {
    background: var(--color-gray-50);
    opacity: 0.7;
  }

  .category-description {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    margin: 0;
    font-style: italic;
  }

  .drop-zone {
    border: 2px dashed var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-8);
    text-align: center;
    cursor: pointer;
    transition: all var(--transition-fast);
    background: var(--color-gray-25);
  }

  .drop-zone:hover:not(.disabled) {
    border-color: var(--color-primary-300);
    background: var(--color-primary-25);
  }

  .drop-zone.dragging {
    border-color: var(--color-primary-500);
    background: var(--color-primary-50);
    transform: scale(1.02);
  }

  .drop-zone.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .drop-zone-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-4);
  }

  .drop-zone-text h4 {
    font-size: var(--font-size-lg);
    font-weight: var(--font-weight-semibold);
    margin: 0 0 var(--space-2) 0;
    color: var(--color-text);
  }

  .drop-zone-text p {
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-3) 0;
  }

  .file-requirements {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  .files-preview {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-4);
    background: var(--color-gray-25);
  }

  .files-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
  }

  .files-header h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .files-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    background: white;
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border);
  }

  .file-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: var(--color-primary-100);
    border-radius: var(--radius-md);
    color: var(--color-primary-600);
    flex-shrink: 0;
  }

  .file-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    min-width: 0;
  }

  .file-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    word-break: break-word;
  }

  .file-size {
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
  }

  .file-category {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    font-size: var(--font-size-xs);
    color: var(--color-secondary-600);
    background: var(--color-secondary-50);
    padding: var(--space-1) var(--space-2);
    border-radius: var(--radius-sm);
    flex-shrink: 0;
  }

  .upload-status {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    background: var(--color-primary-50);
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-md);
  }

  .status-indicator {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    color: var(--color-primary-700);
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
  }

  .info-section {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-md);
  }

  .info-item {
    display: flex;
    align-items: flex-start;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    color: var(--color-text-secondary);
    line-height: var(--line-height-relaxed);
  }

  @media (max-width: 768px) {
    .ground-truth-upload {
      padding: var(--space-4);
    }

    .drop-zone {
      padding: var(--space-6);
    }

    .drop-zone-text h4 {
      font-size: var(--font-size-base);
    }

    .upload-status {
      flex-direction: column;
      align-items: stretch;
      gap: var(--space-2);
    }

    .file-item {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .file-category {
      align-self: flex-end;
    }
  }

  /* Loading animation */
  :global(.animate-spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
</style>