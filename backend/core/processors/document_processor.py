"""
Document Processing Module

Handles pharmaceutical standards document loading, chunking, and metadata extraction.
Converted from notebook Cell 2 functionality with enhanced error handling and
configurable processing options.

Features:
- Document loading from multiple formats (TXT, PDF, DOCX)
- Intelligent text chunking with overlap and sentence boundary detection
- Metadata extraction (sections, pages, chunk indices)
- Configurable chunk sizes and overlap
- Robust error handling and validation
"""
import os
import re
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from ...config.settings import settings
from ...utils import logger, DocumentError, DocumentProcessingError, UnsupportedFormatError

@dataclass
class ChunkMetadata:
    """
    Metadata for a document chunk.
    
    Attributes:
        section: Section number extracted from text (e.g., "2.4.14")
        section_title: Title or first line of the section
        page: Page number where chunk appears
        chunk_index: Sequential index of this chunk in the document
        start_char: Starting character position in original document
        end_char: Ending character position in original document
        char_count: Number of characters in this chunk
        word_count: Approximate number of words in this chunk
    """
    section: str = ""
    section_title: str = ""
    page: int = 1
    chunk_index: int = 0
    start_char: int = 0
    end_char: int = 0
    char_count: int = 0
    word_count: int = 0

@dataclass
class DocumentChunk:
    """
    A processed document chunk with text and metadata.
    
    Attributes:
        text: The actual text content of the chunk
        metadata: Associated metadata for the chunk
    """
    text: str
    metadata: ChunkMetadata

class DocumentProcessor:
    """
    Processes pharmaceutical standards documents into searchable chunks.
    
    Handles document loading, text extraction, chunking with intelligent
    boundary detection, and metadata extraction for efficient similarity
    search and analysis.
    
    Attributes:
        chunk_size: Target size of each chunk in characters
        chunk_overlap: Overlap between consecutive chunks in characters
        max_chunks: Maximum number of chunks to generate per document
        storage_dir: Directory to store processed documents
    """
    
    def __init__(self, 
                 chunk_size: int = None,
                 chunk_overlap: int = None,
                 max_chunks: int = None,
                 storage_dir: str = None):
        """
        Initialize the document processor.
        
        Args:
            chunk_size: Target chunk size in characters (defaults to config)
            chunk_overlap: Overlap between chunks (defaults to config)
            max_chunks: Maximum chunks per document (defaults to config)
            storage_dir: Storage directory (defaults to config)
        """
        self.chunk_size = chunk_size or settings.document.chunk_size
        self.chunk_overlap = chunk_overlap or settings.document.chunk_overlap
        self.max_chunks = max_chunks or settings.document.max_chunks_per_document
        self.storage_dir = storage_dir or settings.document.storage_dir
        
        # Regex patterns for metadata extraction
        self.section_pattern = re.compile(
            r'(^|\n)(\d+\.\d+(?:\.\d+)*)\s+(.*?)(?=\n\d+\.\d+|\Z)', 
            re.DOTALL
        )
        self.page_pattern = re.compile(r'PAGE\s+(\d+)', re.IGNORECASE)
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        
        logger.info(
            f"Initialized DocumentProcessor",
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            max_chunks=self.max_chunks,
            storage_dir=self.storage_dir
        )
    
    def load_document(self, file_path: str) -> str:
        """
        Load document text from various file formats.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            str: Raw document text
            
        Raises:
            DocumentError: If file not found or format unsupported
            DocumentProcessingError: If file processing fails
        """
        if not os.path.exists(file_path):
            raise DocumentError(f"Document not found: {file_path}")
        
        file_path = Path(file_path)
        file_ext = file_path.suffix.lower()
        
        logger.info(f"Loading document: {file_path}", file_type=file_ext)
        
        try:
            if file_ext == '.txt':
                return self._load_text_file(file_path)
            elif file_ext == '.pdf':
                return self._load_pdf_file(file_path)
            elif file_ext == '.docx':
                return self._load_docx_file(file_path)
            else:
                raise UnsupportedFormatError(
                    f"Unsupported file format: {file_ext}",
                    details={"supported_formats": settings.document.supported_formats}
                )
                
        except UnsupportedFormatError:
            raise
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to load document {file_path}: {str(e)}",
                details={"file_path": str(file_path), "file_type": file_ext}
            )
    
    def _load_text_file(self, file_path: Path) -> str:
        """Load text from a plain text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_pdf_file(self, file_path: Path) -> str:
        """Load text from a PDF file."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except ImportError:
            raise DocumentProcessingError(
                "PyPDF2 not available for PDF processing. Install with: pip install PyPDF2"
            )
    
    def _load_docx_file(self, file_path: Path) -> str:
        """Load text from a Word document."""
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise DocumentProcessingError(
                "python-docx not available for DOCX processing. Install with: pip install python-docx"
            )
    
    def extract_sections(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Extract sections from document text using regex patterns.
        
        Args:
            text: Raw document text
            
        Returns:
            List of tuples: (prefix, section_number, section_text)
        """
        sections = self.section_pattern.findall(text)
        logger.debug(f"Extracted {len(sections)} sections from document")
        return sections
    
    def extract_page_numbers(self, text: str) -> List[int]:
        """
        Extract page numbers from document text.
        
        Args:
            text: Text content to search for page markers
            
        Returns:
            List of page numbers found in the text
        """
        page_matches = self.page_pattern.findall(text)
        page_numbers = [int(page) for page in page_matches]
        logger.debug(f"Found {len(page_numbers)} page markers")
        return page_numbers
    
    def find_sentence_boundary(self, text: str, position: int, window: int = 50) -> int:
        """
        Find the nearest sentence boundary to avoid cutting words/sentences.
        
        Args:
            text: Text to search
            position: Target position
            window: Search window around the position
            
        Returns:
            int: Adjusted position at sentence boundary
        """
        if position >= len(text):
            return len(text)
        
        # Define sentence ending punctuation
        sentence_endings = '.?!'
        
        # Search backwards and forwards for sentence boundaries
        start_search = max(0, position - window)
        end_search = min(len(text), position + window)
        
        # Look for sentence endings within the window
        best_position = position
        for i in range(position, end_search):
            if text[i] in sentence_endings and i + 1 < len(text) and text[i + 1].isspace():
                best_position = i + 1
                break
        
        # If no forward boundary found, search backwards
        if best_position == position:
            for i in range(position, start_search, -1):
                if text[i] in sentence_endings and i + 1 < len(text) and text[i + 1].isspace():
                    best_position = i + 1
                    break
        
        return best_position
    
    def chunk_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Process a document into chunks with metadata.
        
        Loads document, extracts sections, and creates overlapping chunks
        with intelligent boundary detection and metadata extraction.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of DocumentChunk objects
            
        Raises:
            DocumentError: If document processing fails
        """
        start_time = time.time()
        
        # Load document text
        text = self.load_document(file_path)
        
        logger.info(
            f"Processing document into chunks",
            file_path=file_path,
            text_length=len(text),
            chunk_size=self.chunk_size,
            overlap=self.chunk_overlap
        )
        
        # Extract sections and metadata
        sections = self.extract_sections(text)
        chunks = []
        current_page = 1
        
        # If no sections found (e.g., for general documents like CVs), treat entire text as one section
        if not sections:
            logger.debug("No numbered sections found, treating entire document as single section")
            # Clean the text (remove page markers)
            clean_text = re.sub(r'PAGE\s+\d+', '', text).strip()
            
            # Extract title (first line or first 50 chars)
            title = clean_text.split('\n')[0] if '\n' in clean_text else clean_text[:50]
            title = title.strip()
            
            # Chunk the entire text
            chunks = self._chunk_section_text(
                clean_text, "1", title, current_page, 0
            )
        else:
            # Process each section
            for section_prefix, section_num, section_text in sections:
                # Check for page markers within the section
                page_matches = self.page_pattern.findall(section_text)
                if page_matches:
                    current_page = int(page_matches[0])
                
                # Clean the text (remove page markers)
                clean_text = re.sub(r'PAGE\s+\d+', '', section_text).strip()
                
                # Extract section title (first line or first 50 chars)
                section_title = clean_text.split('\n')[0] if '\n' in clean_text else clean_text[:50]
                section_title = section_title.strip()
                
                # Chunk the section text
                section_chunks = self._chunk_section_text(
                    clean_text, section_num, section_title, current_page, len(chunks)
                )
                
                chunks.extend(section_chunks)
                
                # Check if we've reached the maximum number of chunks
                if len(chunks) >= self.max_chunks:
                    logger.warning(
                        f"Reached maximum chunk limit ({self.max_chunks}), stopping processing"
                    )
                    chunks = chunks[:self.max_chunks]
                    break
        
        processing_time = time.time() - start_time
        
        logger.info(
            f"Document processed successfully",
            file_path=file_path,
            num_chunks=len(chunks),
            num_sections=len(sections),
            processing_time_seconds=processing_time,
            avg_chunk_size=sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0
        )
        
        return chunks
    
    def _chunk_section_text(self, 
                           text: str, 
                           section_num: str, 
                           section_title: str, 
                           page: int, 
                           base_chunk_index: int) -> List[DocumentChunk]:
        """
        Chunk a single section's text with overlap.
        
        Args:
            text: Section text to chunk
            section_num: Section number
            section_title: Section title
            page: Page number
            base_chunk_index: Starting chunk index
            
        Returns:
            List of DocumentChunk objects for this section
        """
        chunks = []
        start = 0
        chunk_index = base_chunk_index
        
        while start < len(text):
            # Calculate chunk end position
            end = min(start + self.chunk_size, len(text))
            
            # Find good boundary to avoid cutting sentences
            if end < len(text):
                end = self.find_sentence_boundary(text, end)
            
            # Extract chunk text
            chunk_text = text[start:end].strip()
            
            # Only add non-empty chunks
            if chunk_text:
                # Calculate word count (approximate)
                word_count = len(chunk_text.split())
                
                # Create metadata
                metadata = ChunkMetadata(
                    section=section_num,
                    section_title=section_title,
                    page=page,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    char_count=len(chunk_text),
                    word_count=word_count
                )
                
                # Create chunk
                chunk = DocumentChunk(text=chunk_text, metadata=metadata)
                chunks.append(chunk)
                chunk_index += 1
            
            # Move to next position with overlap
            start = max(start + 1, end - self.chunk_overlap) if end < len(text) else len(text)
        
        return chunks
    
    def get_processing_stats(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Generate statistics about the processed chunks.
        
        Args:
            chunks: List of processed chunks
            
        Returns:
            Dictionary with processing statistics
        """
        if not chunks:
            return {"error": "No chunks provided"}
        
        chunk_sizes = [chunk.metadata.char_count for chunk in chunks]
        word_counts = [chunk.metadata.word_count for chunk in chunks]
        sections = list(set(chunk.metadata.section for chunk in chunks if chunk.metadata.section))
        pages = list(set(chunk.metadata.page for chunk in chunks))
        
        return {
            "total_chunks": len(chunks),
            "total_characters": sum(chunk_sizes),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_words": sum(word_counts),
            "avg_words_per_chunk": sum(word_counts) / len(word_counts),
            "unique_sections": len(sections),
            "page_range": f"{min(pages)}-{max(pages)}" if pages else "unknown",
            "sections_preview": sections[:10]  # First 10 sections
        }

# Global instance for use throughout the application
document_processor = DocumentProcessor()