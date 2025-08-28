<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import Icon from '$lib/components/common/Icon.svelte';
  import Button from '$lib/components/common/Button.svelte';
  import { UPLOAD_CONFIG } from '$lib/constants';
  import { formatFileSize, isValidPDF, validateFileSize } from '$lib/utils';
  import { toastStore } from '$lib/stores';

  interface Props {
    multiple?: boolean;
    disabled?: boolean;
    maxSize?: number;
  }

  let { 
    multiple = false,
    disabled = false,
    maxSize = UPLOAD_CONFIG.MAX_FILE_SIZE
  }: Props = $props();

  // Convert drag state to Svelte 5 runes
  let dragover = $state(false);
  let fileInput: HTMLInputElement;
  
  const dispatch = createEventDispatcher<{
    upload: { files: File[] };
    error: { message: string };
  }>();

  function handleDragEnter(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      dragover = true;
    }
  }

  function handleDragLeave(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    // Only set dragover to false if we're leaving the upload zone itself
    if (e.currentTarget === e.target) {
      dragover = false;
    }
  }

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    dragover = false;

    if (disabled) return;

    const files = Array.from(e.dataTransfer?.files || []);
    handleFiles(files);
  }

  function handleFileSelect(e: Event) {
    const target = e.target as HTMLInputElement;
    const files = Array.from(target.files || []);
    handleFiles(files);
    
    // Reset the input value so the same file can be selected again
    target.value = '';
  }

  function handleFiles(files: File[]) {
    if (files.length === 0) return;

    // Validate file count
    if (!multiple && files.length > 1) {
      dispatch('error', { message: 'Please select only one file' });
      toastStore.error('Upload Error', 'Please select only one file');
      return;
    }

    const validFiles: File[] = [];
    const errors: string[] = [];

    for (const file of files) {
      // Validate file type and extension
      const extension = '.' + file.name.split('.').pop()?.toLowerCase();
      const isValidType = UPLOAD_CONFIG.ALLOWED_TYPES.includes(file.type) || 
                         UPLOAD_CONFIG.ALLOWED_EXTENSIONS.includes(extension);
      
      if (!isValidType) {
        errors.push(`${file.name}: Only PDF, TXT, and DOCX files are supported`);
        continue;
      }

      // Validate file size
      if (!validateFileSize(file, maxSize / (1024 * 1024))) {
        errors.push(`${file.name}: File size exceeds ${formatFileSize(maxSize)} limit`);
        continue;
      }

      validFiles.push(file);
    }

    // Report errors
    if (errors.length > 0) {
      const errorMessage = errors.join(', ');
      dispatch('error', { message: errorMessage });
      toastStore.error('Upload Error', errorMessage);
    }

    // Process valid files
    if (validFiles.length > 0) {
      dispatch('upload', { files: validFiles });
    }
  }

  function openFileDialog() {
    if (!disabled) {
      fileInput.click();
    }
  }
</script>

<div 
  class="upload-zone"
  class:dragover
  class:disabled
  ondragenter={handleDragEnter}
  ondragleave={handleDragLeave}
  ondragover={handleDragOver}
  ondrop={handleDrop}
  onclick={openFileDialog}
  onkeydown={(e) => e.key === 'Enter' && openFileDialog()}
  role="button"
  tabindex={disabled ? -1 : 0}
  aria-label="Upload document"
>
  <input
    bind:this={fileInput}
    type="file"
    accept=".pdf,.txt,.docx,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    {multiple}
    {disabled}
    onchange={handleFileSelect}
    style="display: none;"
  />

  <div class="upload-zone-content">
    <div class="upload-zone-icon">
      <Icon name="upload" size={48} />
    </div>

    <div class="upload-zone-text">
      <h3 class="upload-title">
        {dragover ? 'Drop files here' : 'Upload Protocol Document'}
      </h3>
      <p class="upload-description">
        {#if dragover}
          Release to upload your files
        {:else}
          Drag and drop your files here, or click to browse
        {/if}
      </p>
      <p class="upload-specs">
        Supports PDF, TXT, and DOCX files up to {formatFileSize(maxSize)}
        {multiple ? ' (multiple files allowed)' : ''}
      </p>
    </div>

    {#if !dragover}
      <div class="upload-actions">
        <Button variant="primary" {disabled}>
          <Icon name="file" size={16} />
          Choose Files
        </Button>
      </div>
    {/if}
  </div>
</div>

<style>
  .upload-zone {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    padding: var(--space-8);
    border: 2px dashed var(--color-border);
    border-radius: var(--radius-xl);
    background: var(--color-surface);
    cursor: pointer;
    transition: all var(--transition-normal);
  }

  .upload-zone:hover:not(.disabled) {
    border-color: var(--color-primary-400);
    background: var(--color-primary-50);
  }

  .upload-zone:focus {
    outline: 2px solid var(--color-primary-500);
    outline-offset: 2px;
  }

  .upload-zone.dragover {
    border-color: var(--color-primary-500);
    background: var(--color-primary-100);
    transform: scale(1.02);
    box-shadow: var(--shadow-lg);
  }

  .upload-zone.disabled {
    cursor: not-allowed;
    opacity: 0.6;
    background: var(--color-gray-50);
  }

  .upload-zone-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-6);
    text-align: center;
    max-width: 400px;
  }

  .upload-zone-icon {
    color: var(--color-gray-400);
    transition: color var(--transition-normal);
  }

  .upload-zone:hover:not(.disabled) .upload-zone-icon,
  .upload-zone.dragover .upload-zone-icon {
    color: var(--color-primary-500);
  }

  .upload-zone-text {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .upload-title {
    font-size: var(--font-size-xl);
    font-weight: var(--font-weight-semibold);
    color: var(--color-text);
    margin: 0;
  }

  .upload-description {
    font-size: var(--font-size-base);
    color: var(--color-text-secondary);
    margin: 0;
    line-height: var(--line-height-relaxed);
  }

  .upload-specs {
    font-size: var(--font-size-sm);
    color: var(--color-text-muted);
    margin: 0;
  }

  .upload-actions {
    display: flex;
    gap: var(--space-3);
  }

  @media (max-width: 640px) {
    .upload-zone {
      min-height: 250px;
      padding: var(--space-6);
    }

    .upload-zone-content {
      gap: var(--space-4);
    }

    .upload-title {
      font-size: var(--font-size-lg);
    }

    .upload-description {
      font-size: var(--font-size-sm);
    }
  }
</style>