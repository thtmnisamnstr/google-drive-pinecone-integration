"""Document processing for text chunking and embedding generation."""

import re
import tiktoken
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..utils.exceptions import DocumentProcessingError


class DocumentProcessor:
    """Processes documents for chunking and embedding."""
    
    def __init__(self, chunk_size: int = 450, chunk_overlap: int = 75):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # Used by OpenAI models
    
    def chunk_text(self, text: str, file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller pieces for embedding.
        
        Args:
            text: Raw text content
            file_metadata: Metadata about the file
            
        Returns:
            List of chunk dictionaries with metadata
        """
        try:
            if not text.strip():
                return []
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            # Split into sentences first
            sentences = self._split_into_sentences(cleaned_text)
            
            # Create chunks
            chunks = []
            current_chunk = []
            current_tokens = 0
            
            for sentence in sentences:
                sentence_tokens = len(self.tokenizer.encode(sentence))
                
                # If adding this sentence would exceed chunk size, save current chunk
                if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append(self._create_chunk_metadata(
                        chunk_text, file_metadata, len(chunks)
                    ))
                    
                    # Start new chunk with overlap
                    overlap_tokens = 0
                    overlap_chunk = []
                    
                    # Add sentences from the end of previous chunk for overlap
                    for prev_sentence in reversed(current_chunk):
                        prev_tokens = len(self.tokenizer.encode(prev_sentence))
                        if overlap_tokens + prev_tokens <= self.chunk_overlap:
                            overlap_chunk.insert(0, prev_sentence)
                            overlap_tokens += prev_tokens
                        else:
                            break
                    
                    current_chunk = overlap_chunk
                    current_tokens = overlap_tokens
                
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
            
            # Add final chunk if it has content
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append(self._create_chunk_metadata(
                    chunk_text, file_metadata, len(chunks)
                ))
            
            return chunks
            
        except Exception as e:
            raise DocumentProcessingError(f"Failed to chunk text: {e}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere with processing
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Clean text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting - can be improved with more sophisticated NLP
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences and very short ones
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
        
        return sentences
    
    def _create_chunk_metadata(self, chunk_text: str, file_metadata: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """
        Create metadata for a chunk.
        
        Args:
            chunk_text: Text content of the chunk
            file_metadata: Original file metadata
            chunk_index: Index of this chunk within the file
            
        Returns:
            Chunk metadata dictionary
        """
        # Generate vector ID
        vector_id = f"{file_metadata['id']}#{chunk_index}"
        
        # Count tokens in chunk
        token_count = len(self.tokenizer.encode(chunk_text))
        
        return {
            'id': vector_id,
            'file_id': file_metadata['id'],
            'file_name': file_metadata['name'],
            'file_type': file_metadata.get('file_type', 'unknown'),
            'chunk_index': chunk_index,
            'content': chunk_text,
            'modified_time': file_metadata['modifiedTime'],
            'web_view_link': file_metadata['webViewLink']
        }
    
    def process_file(self, file_content: str, file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a complete file and return all chunks.
        
        Args:
            file_content: Raw file content
            file_metadata: File metadata
            
        Returns:
            List of chunk dictionaries
        """
        return self.chunk_text(file_content, file_metadata)
    
    def get_token_count(self, text: str) -> int:
        """
        Get the number of tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        return len(self.tokenizer.encode(text))
    
    def estimate_chunks(self, text: str) -> int:
        """
        Estimate the number of chunks a text will produce.
        
        Args:
            text: Text to estimate chunks for
            
        Returns:
            Estimated number of chunks
        """
        token_count = self.get_token_count(text)
        effective_chunk_size = self.chunk_size - self.chunk_overlap
        
        if effective_chunk_size <= 0:
            return 1
        
        return max(1, (token_count + effective_chunk_size - 1) // effective_chunk_size) 