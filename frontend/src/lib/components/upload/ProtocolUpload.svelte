<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Button from '$lib/components/common/Button.svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import { toastStore } from '$lib/stores';

  interface Props {
    disabled?: boolean;
    analysisInProgress?: boolean;
    hasGroundTruth?: boolean;
    multiple?: boolean;
  }

  let { disabled = false, analysisInProgress = false, hasGroundTruth = true, multiple = false }: Props = $props();

  // Svelte 5 runes for state management
  let isDragging = $state(false);
  let fileInput = $state<HTMLInputElement>();
  let selectedFiles = $state<File[]>([]);
  let uploadProgress = $state<Map<string, number>>(new Map());

  const dispatch = createEventDispatcher<{
    upload: { files: File[] };
    analyze: { files: File[], options: any };
    error: { message: string };
  }>();

  // Supported file types for protocol documents
  const supportedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
  const maxFileSize = 50 * 1024 * 1024; // 50MB
  const maxFiles = multiple ? 10 : 1;

  // Derived values
  const hasFiles = $derived(selectedFiles.length > 0);
  const canUpload = $derived(hasFiles && !disabled && !analysisInProgress);
  const canAnalyze = $derived(hasFiles && hasGroundTruth && !disabled && !analysisInProgress);

  function handleDragOver(event: DragEvent) {
    if (disabled || analysisInProgress) return;
    event.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(event: DragEvent) {
    if (disabled || analysisInProgress) return;
    event.preventDefault();
    isDragging = false;
  }

  function handleDrop(event: DragEvent) {
    if (disabled || analysisInProgress) return;
    event.preventDefault();
    isDragging = false;

    const droppedFiles = event.dataTransfer?.files;
    if (droppedFiles) {
      handleFiles(droppedFiles);
    }
  }

  function handleFileSelect(event: Event) {
    if (disabled || analysisInProgress) return;
    const target = event.target as HTMLInputElement;
    if (target.files) {
      handleFiles(target.files);
    }
  }

  function handleFiles(fileList: FileList) {
    const fileArray = Array.from(fileList);
    
    // Validate file count
    if (fileArray.length > maxFiles) {
      dispatch('error', { message: `Maximum ${maxFiles} file${maxFiles === 1 ? '' : 's'} allowed` });
      return;
    }

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

      // Basic protocol content validation (by filename)
      const fileName = file.name.toLowerCase();
      const protocolKeywords = ['protocol', 'method', 'procedure', 'analysis', 'test', 'assay', 'validation'];
      const hasProtocolKeyword = protocolKeywords.some(keyword => fileName.includes(keyword));
      
      if (!hasProtocolKeyword && !fileName.includes('sop')) {
        // Warning but not blocking
        console.warn(`${file.name}: Filename doesn't suggest this is a protocol document`);
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
      selectedFiles = validFiles;
      console.log(`Selected ${validFiles.length} protocol document(s) for analysis`);
      toastStore.info('Files Selected', `${validFiles.length} protocol document(s) ready for analysis`);
      
      // Dispatch upload event
      dispatch('upload', { files: validFiles });
    }

    // Clear the input
    if (fileInput) {
      fileInput.value = '';
    }
  }

  function removeFile(index: number) {
    selectedFiles = selectedFiles.filter((_, i) => i !== index);
    if (selectedFiles.length === 0) {
      clearFiles();
    }
  }

  function clearFiles() {
    selectedFiles = [];
    uploadProgress.clear();
    uploadProgress = uploadProgress; // Trigger reactivity
    if (fileInput) {
      fileInput.value = '';
    }
  }

  function openFileDialog() {
    if (disabled || analysisInProgress || !fileInput) return;
    fileInput.click();
  }

  function analyzeFiles() {
    if (!canAnalyze) {
      if (!hasGroundTruth) {
        dispatch('error', { message: 'No ground truth documents available. Please upload ground truth documents first.' });
      } else {
        dispatch('error', { message: 'Please select valid protocol files for analysis' });
      }
      return;
    }

    dispatch('analyze', { 
      files: selectedFiles, 
      options: { 
        fileCount: selectedFiles.length,
        totalSize: selectedFiles.reduce((sum, file) => sum + file.size, 0)
      } 
    });
  }

  function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  function getFileTypeIcon(file: File): string {
    if (file.type.includes('pdf')) return 'file-text';
    if (file.type.includes('document') || file.type.includes('word')) return 'file-text';
    if (file.type.includes('text')) return 'file-text';
    return 'file';
  }

  function getFileTypeLabel(file: File): string {
    if (file.type.includes('pdf')) return 'PDF';
    if (file.type.includes('document') || file.type.includes('word')) return 'DOCX';
    if (file.type.includes('text')) return 'TXT';
    return 'Unknown';
  }
</script>

<div class="protocol-upload">
  <div class="upload-header">
    <div class="header-info">
      <h4>
        <Icon name="upload" size={18} />
        Protocol File Upload
      </h4>
      <p>Upload pharmaceutical protocol documents for automated analysis</p>
    </div>
  </div>

  <!-- File Drop Zone -->
  <div 
    class="drop-zone"
    class:dragging={isDragging}
    class:disabled={disabled || analysisInProgress}
    class:has-files={hasFiles}
    ondragover={handleDragOver}
    ondragleave={handleDragLeave}
    ondrop={handleDrop}
    onclick={hasFiles ? undefined : openFileDialog}
    role="button"
    tabindex="0"
    onkeydown={(e) => {
      if (!hasFiles && (e.key === 'Enter' || e.key === ' ')) {
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
      disabled={disabled || analysisInProgress}
      onchange={handleFileSelect}
      style="display: none;"
    />

    {#if !hasFiles}
      <div class="drop-zone-content">
        <Icon 
          name="upload" 
          size={48} 
          color={isDragging ? "var(--color-primary-500)" : "var(--color-primary-600)"} 
        />
        <div class="drop-zone-text">
          <h4>Upload Protocol Documents</h4>
          <p>
            {#if isDragging}
              Release to upload files
            {:else}
              Drag and drop protocol files here, or click to browse
            {/if}
          </p>
          <div class="file-requirements">
            <span>Supported: PDF, DOCX, TXT</span>
            <span>Max size: 50MB per file</span>
            {#if multiple}
              <span>Max files: {maxFiles}</span>
            {/if}
          </div>
        </div>
      </div>
    {:else}
      <!-- Selected Files Display -->
      <div class="selected-files">
        <div class="files-header">
          <h4>Selected Files ({selectedFiles.length})</h4>
          <div class="header-actions">
            <Button variant="secondary" size="sm" onclick={openFileDialog}>
              <Icon name="plus" size={14} />
              Add More
            </Button>
            <Button variant="secondary" size="sm" onclick={clearFiles}>
              <Icon name="x" size={14} />
              Clear All
            </Button>
          </div>
        </div>
        
        <div class="files-list">
          {#each selectedFiles as file, index}
            <div class="file-item">
              <div class="file-icon">
                <Icon name={getFileTypeIcon(file)} size={20} />
              </div>
              
              <div class="file-info">
                <div class="file-name">{file.name}</div>
                <div class="file-meta">
                  <span class="file-type">{getFileTypeLabel(file)}</span>
                  <span class="file-size">{formatFileSize(file.size)}</span>
                  <span class="file-date">Modified {new Date(file.lastModified).toLocaleDateString()}</span>
                </div>
              </div>
              
              <div class="file-actions">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  onclick={() => removeFile(index)}
                  disabled={disabled || analysisInProgress}
                >
                  <Icon name="x" size={14} />
                  Remove
                </Button>
              </div>
            </div>
          {/each}
        </div>
        
        <!-- File Summary -->
        <div class="files-summary">
          <div class="summary-stats">
            <span class="stat">
              <Icon name="file" size={14} />
              {selectedFiles.length} file{selectedFiles.length === 1 ? '' : 's'}
            </span>
            <span class="stat">
              <Icon name="download" size={14} />
              {formatFileSize(selectedFiles.reduce((sum, file) => sum + file.size, 0))} total
            </span>
          </div>
        </div>
      </div>
    {/if}
  </div>

  <!-- Analysis Actions -->
  {#if hasFiles}
    <div class="analysis-actions">
      <div class="action-info">
        {#if !hasGroundTruth}
          <div class="ground-truth-warning">
            <Icon name="warning" size={16} color="var(--color-warning-600)" />
            <span>Upload ground truth documents first for comprehensive analysis</span>
          </div>
        {:else}
          <div class="analysis-ready">
            <Icon name="check" size={16} color="var(--color-success-600)" />
            <span>Ready to analyze against ground truth library</span>
          </div>
        {/if}
      </div>

      <div class="action-buttons">
        <Button
          variant="primary"
          size="lg"
          onclick={analyzeFiles}
          loading={analysisInProgress}
          disabled={!canAnalyze}
        >
          <Icon name="activity" size={18} />
          {analysisInProgress ? 'Processing Files...' : `Analyze ${selectedFiles.length} File${selectedFiles.length === 1 ? '' : 's'}`}
        </Button>
      </div>
    </div>
  {/if}

  <!-- Information Section -->
  <div class="info-section">
    <div class="info-item">
      <Icon name="info" size={16} color="var(--color-primary-600)" />
      <span>Supported formats: PDF documents, Microsoft Word files (DOCX), and plain text files</span>
    </div>
    <div class="info-item">
      <Icon name="shield" size={16} color="var(--color-success-600)" />
      <span>Files are processed securely and stored in your personal Google Drive</span>
    </div>
    <div class="info-item">
      <Icon name="activity" size={16} color="var(--color-secondary-600)" />
      <span>Automatic text extraction and AI-powered analysis against your ground truth library</span>
    </div>
  </div>
</div>

<style>
  .protocol-upload {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
    padding: var(--space-6);
  }

  .upload-header {
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

  .drop-zone {
    border: 2px dashed var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-8);
    text-align: center;
    cursor: pointer;
    transition: all var(--transition-fast);
    background: var(--color-gray-25);
    min-height: 300px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .drop-zone:hover:not(.disabled):not(.has-files) {
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

  .drop-zone.has-files {
    cursor: default;
    padding: var(--space-6);
    text-align: left;
    border-style: solid;
    background: white;
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

  .selected-files {
    width: 100%;
  }

  .files-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-4);
    padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--color-border);
  }

  .files-header h4 {
    font-size: var(--font-size-base);
    font-weight: var(--font-weight-semibold);
    margin: 0;
    color: var(--color-text);
  }

  .header-actions {
    display: flex;
    gap: var(--space-2);
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
    background: var(--color-gray-50);
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
    min-width: 0;
  }

  .file-name {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    color: var(--color-text);
    margin-bottom: var(--space-1);
    word-break: break-word;
  }

  .file-meta {
    display: flex;
    gap: var(--space-3);
    font-size: var(--font-size-xs);
    color: var(--color-text-muted);
    flex-wrap: wrap;
  }

  .file-actions {
    flex-shrink: 0;
  }

  .files-summary {
    padding: var(--space-3);
    background: var(--color-primary-50);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-primary-200);
  }

  .summary-stats {
    display: flex;
    gap: var(--space-4);
    font-size: var(--font-size-sm);
    color: var(--color-primary-700);
  }

  .stat {
    display: flex;
    align-items: center;
    gap: var(--space-1);
  }

  .analysis-actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-4);
    padding: var(--space-4);
    background: var(--color-gray-50);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
  }

  .action-info {
    text-align: center;
  }

  .ground-truth-warning,
  .analysis-ready {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-2);
    font-size: var(--font-size-sm);
    padding: var(--space-3);
    border-radius: var(--radius-md);
  }

  .ground-truth-warning {
    color: var(--color-warning-700);
    background: var(--color-warning-50);
    border: 1px solid var(--color-warning-200);
  }

  .analysis-ready {
    color: var(--color-success-700);
    background: var(--color-success-50);
    border: 1px solid var(--color-success-200);
  }

  .action-buttons {
    display: flex;
    justify-content: center;
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
    .protocol-upload {
      padding: var(--space-4);
    }

    .upload-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .drop-zone {
      padding: var(--space-6);
      min-height: 250px;
    }

    .drop-zone-text h4 {
      font-size: var(--font-size-base);
    }

    .files-header {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .file-item {
      flex-direction: column;
      align-items: flex-start;
      gap: var(--space-2);
    }

    .file-actions {
      align-self: flex-end;
    }

    .summary-stats {
      flex-direction: column;
      gap: var(--space-2);
    }

    .action-buttons {
      width: 100%;
    }

    .action-buttons > * {
      width: 100%;
    }
  }
</style>