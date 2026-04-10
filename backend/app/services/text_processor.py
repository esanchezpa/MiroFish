"""
Text processing service
v0.2: propagates boundary_min_fill_ratio and min_chunk_chars to the splitter
"""

from typing import List, Optional
from ..utils.file_parser import FileParser, split_text_into_chunks


class TextProcessor:
    """Text processor"""
    
    @staticmethod
    def extract_from_files(file_paths: List[str]) -> str:
        """Extract text from multiple files"""
        return FileParser.extract_from_multiple(file_paths)
    
    @staticmethod
    def split_text(
        text: str,
        chunk_size: int = 4000,
        overlap: int = 120,
        boundary_min_fill_ratio: float = 0.80,
        min_chunk_chars: int = 2200
    ) -> List[str]:
        """
        Split text into chunks.
        
        Args:
            text: Input text
            chunk_size: Target chunk size in characters
            overlap: Overlap between consecutive chunks
            boundary_min_fill_ratio: Min fill ratio to accept a boundary cut (v0.2)
            min_chunk_chars: Minimum valid chunk size in characters (v0.2)
            
        Returns:
            List of text chunks
        """
        return split_text_into_chunks(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
            boundary_min_fill_ratio=boundary_min_fill_ratio,
            min_chunk_chars=min_chunk_chars
        )
    
    @staticmethod
    def preprocess_text(text: str) -> str:
        """
        Preprocess text:
        - Normalize line endings
        - Collapse excessive blank lines
        - Strip leading/trailing whitespace per line
        """
        import re
        
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'\n{3,}', '\n\n', text)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    @staticmethod
    def get_text_stats(text: str) -> dict:
        """Get text statistics"""
        return {
            "total_chars": len(text),
            "total_lines": text.count('\n') + 1,
            "total_words": len(text.split()),
        }
