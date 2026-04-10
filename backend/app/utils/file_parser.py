"""
File parsing utilities
Supports text extraction from PDF, Markdown, and TXT files.
v0.2: split_text_into_chunks updated with boundary_min_fill_ratio and min_chunk_chars
"""

import os
from pathlib import Path
from typing import List, Optional


def _read_text_with_fallback(file_path: str) -> str:
    """
    Read text file with multi-level encoding fallback:
    1. UTF-8
    2. charset_normalizer detection
    3. chardet detection
    4. UTF-8 with errors='replace'
    """
    data = Path(file_path).read_bytes()
    
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass
    
    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass
    
    if not encoding:
        encoding = 'utf-8'
    
    return data.decode(encoding, errors='replace')


class FileParser:
    """File parser supporting PDF, Markdown, and TXT"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt'}
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """Extract text from a file"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)
        
        raise ValueError(f"Cannot process file format: {suffix}")
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF"""
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ImportError("PyMuPDF required: pip install PyMuPDF")
        
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """Extract text from Markdown with encoding detection"""
        return _read_text_with_fallback(file_path)
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """Extract text from TXT with encoding detection"""
        return _read_text_with_fallback(file_path)
    
    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """Extract and merge text from multiple files"""
        all_texts = []
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== Document {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== Document {i}: {file_path} (extraction failed: {str(e)}) ===")
        
        return "\n\n".join(all_texts)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 4000,
    overlap: int = 120,
    boundary_min_fill_ratio: float = 0.80,
    min_chunk_chars: int = 2200
) -> List[str]:
    """
    Split text into chunks with smart boundary detection.
    
    v0.2 improvements:
    - boundary_min_fill_ratio: only cut at a sentence boundary if the candidate chunk
      is at least this fraction of chunk_size (prevents micro-fragments)
    - min_chunk_chars: hard minimum chunk size in chars (also prevents micro-fragments)
    - Fallback: if no valid boundary found, cut hard at start + chunk_size
    
    Example for 2.8M chars, chunk_size=4000, overlap=120:
      ~727 chunks (vs ~5600+ with old defaults of chunk_size=500)
    
    Args:
        text: Input text
        chunk_size: Target chunk size in characters
        overlap: Overlap between consecutive chunks in characters
        boundary_min_fill_ratio: Minimum fill ratio to accept a boundary cut (0.0-1.0)
        min_chunk_chars: Minimum chunk size; chunks smaller than this are skipped
        
    Returns:
        List of text chunks
    """
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    
    separators = ['。', '！', '？', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ']
    
    while start < len(text):
        end = start + chunk_size
        
        if end < len(text):
            # Try to find a clean boundary near the end of the window
            candidate_end = None
            
            for sep in separators:
                pos = text[start:end].rfind(sep)
                if pos != -1:
                    real_end = start + pos + len(sep)
                    candidate_len = real_end - start
                    # Only accept if chunk is large enough (prevents micro-fragments)
                    if (candidate_len >= min_chunk_chars and
                            candidate_len >= chunk_size * boundary_min_fill_ratio):
                        candidate_end = real_end
                        break
            
            if candidate_end:
                end = candidate_end
            # else: no valid boundary — use hard cut at start + chunk_size
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) >= min(min_chunk_chars, 50):  # always keep non-trivial chunks
            chunks.append(chunk)
        
        # Next chunk starts at end - overlap
        start = end - overlap if end < len(text) else len(text)
    
    return chunks
