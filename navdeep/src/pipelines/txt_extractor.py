"""Text File Extractor
Extracts text from plain text files (.txt)
"""

import os
import logging
from typing import Dict, Any
from datetime import datetime
import chardet

logger = logging.getLogger(__name__)

class TXTExtractor:
    """Extract text from plain text files"""
    
    def __init__(self):
        """Initialize the text extractor"""
        self.supported_extensions = ['.txt']
    
    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from a text file
        
        Args:
            file_path: Path to the text file
            
        Returns:
            Dictionary containing extraction results
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}',
                'file_path': file_path
            }
        
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result.get('encoding', 'utf-8')
            
            # Read the file with detected encoding
            with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                text_content = f.read()
            
            # Get file metadata
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            
            # Count lines and characters
            lines = text_content.split('\n')
            line_count = len(lines)
            char_count = len(text_content)
            word_count = len(text_content.split())
            
            return {
                'success': True,
                'text': text_content,
                'metadata': {
                    'file_path': file_path,
                    'file_name': os.path.basename(file_path),
                    'file_size': file_size,
                    'encoding': encoding,
                    'encoding_confidence': encoding_result.get('confidence', 0),
                    'line_count': line_count,
                    'character_count': char_count,
                    'word_count': word_count,
                    'extraction_method': 'direct_read',
                    'extracted_at': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def validate_text_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate if the file is a readable text file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing validation results
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    'valid': False,
                    'reason': 'File not found'
                }
            
            # Check file size (avoid very large files)
            file_size = os.path.getsize(file_path)
            max_size = 100 * 1024 * 1024  # 100MB limit
            
            if file_size > max_size:
                return {
                    'valid': False,
                    'reason': f'File too large: {file_size} bytes (max: {max_size} bytes)'
                }
            
            # Try to detect if it's a text file
            with open(file_path, 'rb') as f:
                sample = f.read(1024)  # Read first 1KB
                
            # Check for binary content
            if b'\x00' in sample:
                return {
                    'valid': False,
                    'reason': 'File appears to be binary'
                }
            
            # Try to decode as text
            try:
                encoding_result = chardet.detect(sample)
                encoding = encoding_result.get('encoding', 'utf-8')
                sample.decode(encoding)
                
                return {
                    'valid': True,
                    'encoding': encoding,
                    'confidence': encoding_result.get('confidence', 0),
                    'file_size': file_size
                }
                
            except UnicodeDecodeError:
                return {
                    'valid': False,
                    'reason': 'Unable to decode as text'
                }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Validation error: {str(e)}'
            }